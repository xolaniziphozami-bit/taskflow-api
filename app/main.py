from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from .database import Base, engine, get_db
from .database_models import TaskDB, UserDB
from .models import AccessToken, TaskCreate, TaskResponse, TaskUpdate, UserCreate, UserLogin, UserResponse


app = FastAPI(
    title="TaskFlow API",
    description="A task management API with JWT authentication and per-user task ownership.",
    version="2.0.0",
)


def initialize_database() -> None:
    """Create new tables and safely add ownership to existing task databases."""
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("tasks")}
        if "user_id" not in columns:
            # Existing tasks stay intact and unassigned. They are not exposed to any account.
            connection.exec_driver_sql(
                "ALTER TABLE tasks ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_tasks_user_id ON tasks (user_id)"
        )


initialize_database()


@app.get("/", tags=["Health"])
def home():
    return {"message": "TaskFlow API is running!"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    username = user_data.username.strip().lower()
    user = UserDB(username=username, password_hash=hash_password(user_data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username is already registered",
        )
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=AccessToken, tags=["Authentication"])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    username = credentials.username.strip().lower()
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessToken(
        access_token=create_access_token(user.id),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
def get_profile(current_user: UserDB = Depends(get_current_user)):
    return current_user


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_task = TaskDB(
        title=task.title,
        description=task.description,
        completed=task.completed,
        user_id=current_user.id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks", response_model=list[TaskResponse], tags=["Tasks"])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    return (
        db.query(TaskDB)
        .filter(TaskDB.user_id == current_user.id)
        .order_by(TaskDB.id)
        .all()
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    task = (
        db.query(TaskDB)
        .filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    task = (
        db.query(TaskDB)
        .filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.title = task_data.title
    task.description = task_data.description
    task.completed = task_data.completed
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    task = (
        db.query(TaskDB)
        .filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

from fastapi import FastAPI, HTTPException
from .database import engine, SessionLocal 
from .database_models import TaskDB
from .models import Task, TaskResponse

app = FastAPI()

TaskDB.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "TaskFlow API is running!"}  

@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: Task):
    db = SessionLocal()
    db_task = TaskDB(title=task.title, description=task.description, completed=task.completed)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    db.close()
    
    return db_task

@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks():
    db = SessionLocal()
    tasks = db.query(TaskDB).all()
    db.close()
    
    return tasks

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: Task):
    db = SessionLocal()
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if not db_task:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")   

    db_task.title = task.title
    db_task.description = task.description
    db_task.completed = task.completed

    db.commit()
    db.refresh(db_task)
    db.close()

    return db_task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    db = SessionLocal()
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if not db_task: 
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")   

    db.delete(db_task)
    db.commit()
    db.close()

    return 

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    db = SessionLocal()
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    db.close()

    if task:
        return task
    
    raise HTTPException(status_code=404, detail="Task not found")

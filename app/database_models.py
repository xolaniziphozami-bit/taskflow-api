from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tasks = relationship("TaskDB", back_populates="owner", cascade="all, delete-orphan")


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=False, default="")
    completed = Column(Boolean, nullable=False, default=False)
    # Nullable only to preserve rows created before account ownership was added.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    owner = relationship("UserDB", back_populates="tasks")

from pydantic import BaseModel

class Task(BaseModel):
    id: int
    title: str
    description: str
    completed: bool = False 

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    
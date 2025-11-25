# In-memory storage and logic for todos
# Contains a simple in-memory list and functions to add/get todos. Later can be enhanced with database storage.
from app.models import Todo

todo_list = []

def add_todo(todo: Todo):
    todo_list.append(todo)

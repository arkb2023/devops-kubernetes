# Pydantic models for todo data
# Defines data schemas, e.g., Todo model with a string text field limited to 140 chars.
from pydantic import BaseModel, Field

class Todo(BaseModel):
    text: str = Field(..., max_length=140, min_length=1)

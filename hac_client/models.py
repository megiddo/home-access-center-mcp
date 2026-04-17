from typing import List, Optional
from pydantic import BaseModel

class Assignment(BaseModel):
    name: str
    category: str
    date_assigned: Optional[str] = None
    date_due: Optional[str] = None
    max_points: Optional[float] = None
    score: Optional[float] = None
    notes: Optional[str] = None

class Course(BaseModel):
    name: str
    average: Optional[float] = None
    assignments: List[Assignment]

class ClassworkReport(BaseModel):
    student_id: Optional[str] = None
    courses: List[Course]

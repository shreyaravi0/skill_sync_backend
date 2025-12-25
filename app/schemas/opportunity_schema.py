from pydantic import BaseModel
from typing import Optional

class OpportunityCreate(BaseModel):
    title: str
    description: Optional[str] = None
    posted_by: str
    type: str   # job / internship / mentorship

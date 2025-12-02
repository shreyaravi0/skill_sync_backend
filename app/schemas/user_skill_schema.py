from pydantic import BaseModel
from typing import List

class UserSkillAssign(BaseModel):
    username: str
    skill_names: List[str]

from pydantic import BaseModel
from typing import List

class OpportunitySkillAssign(BaseModel):
    opportunity_id: str
    skill_names: List[str]

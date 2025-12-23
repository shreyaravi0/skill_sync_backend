from pydantic import BaseModel

class MatchRequest(BaseModel):
    username: str

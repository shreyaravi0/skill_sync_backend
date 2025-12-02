from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.skill_schema import SkillCreate

router = APIRouter()

# CREATE
@router.post("/")
def add_skill(skill: SkillCreate, supabase = Depends(get_supabase)):
    res = supabase.table("skills").insert({
        "name": skill.name,
        "category": skill.category,
        "skill_description": skill.skill_description
    }).execute()
    return res.data

# GET ALL
@router.get("/")
def get_all_skills(supabase = Depends(get_supabase)):
    return supabase.table("skills").select("*").execute().data

# GET ONE
@router.get("/{name}")
def get_skill(name: str, supabase = Depends(get_supabase)):
    res = supabase.table("skills").select("*").eq("name", name).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    return res.data[0]

# UPDATE
@router.put("/{name}")
def update_skill(name: str, updates: dict, supabase = Depends(get_supabase)):
    res = supabase.table("skills").update(updates).eq("name", name).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    return res.data[0]

# DELETE
@router.delete("/{name}")
def delete_skill(name: str, supabase = Depends(get_supabase)):
    res = supabase.table("skills").delete().eq("name", name).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill deleted"}

supabase = get_supabase()

def get_skill_by_name(name: str):
    res = supabase.table("skills").select("*").eq("name", name).execute()
    return res.data[0] if res.data else None


def create_skill(name: str, category="auto", skill_description="auto-added"):
    """
    Insert a new skill if it doesn't exist.
    """
    res = supabase.table("skills").insert({
        "name": name,
        "category": category,
        "skill_description": skill_description
    }).execute()
    return res.data[0]


def get_or_create_skill(name: str):
    """
    Check if a skill exists; if not, create it.
    """
    skill = get_skill_by_name(name)
    if skill:
        return skill
    return create_skill(name)

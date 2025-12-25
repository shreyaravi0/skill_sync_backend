from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.user_skill_schema import UserSkillAssign
from app.routes.skills import get_skill_by_name
from app.routes.users import get_user_by_username

router = APIRouter(
    prefix="/user-skills",
    tags=["User Skills"]
)


@router.post("/")
def assign_user_skills(data: UserSkillAssign, supabase = Depends(get_supabase)):
    """
    Assign skills to a user by username
    """
    # 1. Fetch user by username
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(400, f"User '{data.username}' does not exist")

    user_id = user["user_id"]

    inserted_rows = []

    # 2. Loop through skill names
    for skill_name in data.skill_names:
        # fetch skill row
        skill = get_skill_by_name(skill_name)
        if not skill:
            raise HTTPException(400, f"Skill '{skill_name}' does not exist")

        skill_id = skill["skill_id"]

        # Check if mapping already exists
        existing = (
            supabase
            .table("user_skills")
            .select("*")
            .eq("user_id", user_id)
            .eq("skill_id", skill_id)
            .execute()
        )
        
        if existing.data:
            continue  # Skip if already exists

        # 3. Insert mapping into user_skills
        res = (
            supabase
            .table("user_skills")
            .insert({
                "user_id": user_id,
                "skill_id": skill_id
            })
            .execute()
        )

        inserted_rows.append(res.data[0])

    return {
        "message": f"Skills assigned to user '{data.username}'",
        "assigned": inserted_rows
    }


@router.get("/{username}")
def get_user_skills(username: str, supabase = Depends(get_supabase)):
    """
    Get all skills for a specific user by username
    """
    # 1. Get user
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(404, f"User '{username}' does not exist")
    
    user_id = user["user_id"]
    
    # 2. Get user_skills mappings
    user_skill_rows = (
        supabase
        .table("user_skills")
        .select("skill_id")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    
    if not user_skill_rows:
        return []
    
    # 3. Get skill details for each skill_id
    skills = []
    for row in user_skill_rows:
        skill_id = row["skill_id"]
        skill_data = (
            supabase
            .table("skills")
            .select("*")
            .eq("skill_id", skill_id)
            .execute()
            .data
        )
        if skill_data:
            skills.append(skill_data[0])
    
    return skills


@router.delete("/{username}/{skill_name}")
def remove_user_skill(username: str, skill_name: str, supabase = Depends(get_supabase)):
    """
    Remove a specific skill from a user
    """
    # 1. Get user
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(404, f"User '{username}' does not exist")
    
    user_id = user["user_id"]
    
    # 2. Get skill
    skill = get_skill_by_name(skill_name)
    if not skill:
        raise HTTPException(404, f"Skill '{skill_name}' does not exist")
    
    skill_id = skill["skill_id"]
    
    # 3. Delete mapping
    res = (
        supabase
        .table("user_skills")
        .delete()
        .eq("user_id", user_id)
        .eq("skill_id", skill_id)
        .execute()
    )
    
    if not res.data:
        raise HTTPException(404, "User skill mapping not found")
    
    return {"message": f"Skill '{skill_name}' removed from user '{username}'"}
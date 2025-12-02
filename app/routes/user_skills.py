from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.user_skill_schema import UserSkillAssign
from app.routes.skills import get_skill_by_name
from app.routes.users import get_user_by_username

router = APIRouter(prefix="/user-skills", tags=["User Skills"])

# @router.post("/")
# def assign_user_skills(data: UserSkillAssign, supabase = Depends(get_supabase)):

#     user_id = data.user_id
#     skill_names = data.skill_names

#     inserted_rows = []

#     for skill_name in skill_names:
#         # 1. Fetch skill row
#         skill = get_skill_by_name(skill_name)
#         if not skill:
#             raise HTTPException(
#                 400,
#                 detail=f"Skill '{skill_name}' does not exist in skills table"
#             )

#         skill_id = skill["skill_id"]

#         # 2. Insert mapping into user_skills table
#         res = (
#             supabase
#             .table("user_skills")
#             .insert({
#                 "user_id": user_id,
#                 "skill_id": skill_id
#             })
#             .execute()
#         )

#         inserted_rows.append(res.data[0])

#     return {
#         "message": "Skills assigned to user",
#         "assigned": inserted_rows
#     }


@router.post("/")
def assign_user_skills(data: UserSkillAssign, supabase = Depends(get_supabase)):

    # 1. Fetch user by username
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(400, f"User '{data.username}' does not exist")

    user_id = user["user_id"]   # <-- IMPORTANT

    inserted_rows = []

    # 2. Loop through skill names
    for skill_name in data.skill_names:

        # fetch skill row
        skill = get_skill_by_name(skill_name)
        if not skill:
            raise HTTPException(400, f"Skill '{skill_name}' does not exist")

        skill_id = skill["skill_id"]

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

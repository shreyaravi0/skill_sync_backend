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


# -------------------------------------------------
# GET USER SKILLS
# GET /user-skills/{username}
# -------------------------------------------------
@router.get("/{username}")
def get_user_skills(
    username: str,
    supabase = Depends(get_supabase)
):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(404, "User not found")

    user_id = user["user_id"]

    user_skills = (
        supabase
        .table("user_skills")
        .select("skill_id")
        .eq("user_id", user_id)
        .execute()
    )

    if not user_skills.data:
        return []

    skill_ids = [row["skill_id"] for row in user_skills.data]

    skills = (
        supabase
        .table("skills")
        .select("skill_id, name")
        .in_("skill_id", skill_ids)
        .execute()
    )

    return skills.data


# -------------------------------------------------
# DELETE USER SKILL
# DELETE /user-skills/{username}/{skill_name}
# -------------------------------------------------
@router.delete("/{username}/{skill_name}")
def delete_user_skill(
    username: str,
    skill_name: str,
    supabase = Depends(get_supabase)
):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(404, "User not found")

    skill = get_skill_by_name(skill_name)
    if not skill:
        raise HTTPException(404, "Skill not found")

    delete_res = (
        supabase
        .table("user_skills")
        .delete()
        .eq("user_id", user["user_id"])
        .eq("skill_id", skill["skill_id"])
        .execute()
    )

    if not delete_res.data:
        raise HTTPException(404, "Skill mapping not found")

    return {
        "message": f"Skill '{skill_name}' removed from user '{username}'"
    }
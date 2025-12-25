from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.opportunity_skills_schema import OpportunitySkillAssign
from app.routes.skills import get_skill_by_name

router = APIRouter(prefix="/opportunity-skills", tags=["Opportunity Skills"])

@router.post("/")
def assign_skills(data: OpportunitySkillAssign, supabase=Depends(get_supabase)):

    opportunity_id = data.opportunity_id
    skill_names = data.skill_names

    inserted_rows = []

    for skill_name in skill_names:
        # 1. Fetch skill row
        skill = get_skill_by_name(skill_name)
        if not skill:
            raise HTTPException(
                400,
                detail=f"Skill '{skill_name}' does not exist in skills table"
            )

        skill_id = skill["skill_id"]

        # 2. Insert into the join table
        res = (
            supabase
            .table("opportunity_skills")
            .insert({
                "opp_id": opportunity_id,
                "skill_id": skill_id
            })
            .execute()
        )

        inserted_rows.append(res.data[0])

    return {
        "message": "Skills assigned to opportunity",
        "assigned": inserted_rows
    }



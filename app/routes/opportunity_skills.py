from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.opportunity_skills_schema import OpportunitySkillAssign
from app.routes.skills import get_skill_by_name

router = APIRouter(prefix="/opportunity-skills", tags=["Opportunity Skills"])

@router.post("/")
def assign_skills(data: OpportunitySkillAssign, supabase = Depends(get_supabase)):
    """
    Assign multiple skills to an opportunity
    """
    opportunity_id = data.opportunity_id
    skill_names = data.skill_names

    # Verify opportunity exists
    opp_check = (
        supabase
        .table("opportunities")
        .select("opp_id")
        .eq("opp_id", opportunity_id)
        .execute()
    )
    
    if not opp_check.data:
        raise HTTPException(404, f"Opportunity '{opportunity_id}' does not exist")

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

        # Check if mapping already exists
        existing = (
            supabase
            .table("opportunity_skills")
            .select("*")
            .eq("opp_id", opportunity_id)
            .eq("skill_id", skill_id)
            .execute()
        )
        
        if existing.data:
            continue  # Skip if already exists

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


@router.get("/{opportunity_id}")
def get_opportunity_skills(opportunity_id: str, supabase = Depends(get_supabase)):
    """
    Get all skills for a specific opportunity
    """
    # 1. Verify opportunity exists
    opp_check = (
        supabase
        .table("opportunities")
        .select("opp_id")
        .eq("opp_id", opportunity_id)
        .execute()
    )
    
    if not opp_check.data:
        raise HTTPException(404, f"Opportunity '{opportunity_id}' does not exist")
    
    # 2. Get opportunity_skills mappings
    opp_skill_rows = (
        supabase
        .table("opportunity_skills")
        .select("skill_id")
        .eq("opp_id", opportunity_id)
        .execute()
        .data
    )
    
    if not opp_skill_rows:
        return []
    
    # 3. Get skill details for each skill_id
    skills = []
    for row in opp_skill_rows:
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


@router.delete("/{opportunity_id}/{skill_name}")
def remove_opportunity_skill(opportunity_id: str, skill_name: str, supabase = Depends(get_supabase)):
    """
    Remove a specific skill from an opportunity
    """
    # 1. Get skill
    skill = get_skill_by_name(skill_name)
    if not skill:
        raise HTTPException(404, f"Skill '{skill_name}' does not exist")
    
    skill_id = skill["skill_id"]
    
    # 2. Delete mapping
    res = (
        supabase
        .table("opportunity_skills")
        .delete()
        .eq("opp_id", opportunity_id)
        .eq("skill_id", skill_id)
        .execute()
    )
    
    if not res.data:
        raise HTTPException(404, "Opportunity skill mapping not found")
    
    return {"message": f"Skill '{skill_name}' removed from opportunity"}
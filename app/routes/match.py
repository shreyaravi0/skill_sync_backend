from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict

from app.db import get_supabase
from app.schemas.match_schema import MatchRequest
from app.ml.matcher import build_skill_vector, compute_match_score
from app.routes.users import get_user_by_username

router = APIRouter(prefix="/match", tags=["Matching"])

@router.post("/")
def find_matches(data: MatchRequest, supabase = Depends(get_supabase)) -> Dict[str, List[Dict]]:
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user")

    role = user["role"]
    target_role = "mentor" if role == "mentee" else "mentee"

    # Fetch all target users
    targets = supabase.table("users").select("*").eq("role", target_role).execute().data

    # Fetch all skills once
    all_skills_data = supabase.table("skills").select("*").execute().data
    skill_id_to_name = {s["skill_id"]: s["name"] for s in all_skills_data}
    all_skill_names = [s["name"] for s in all_skills_data]

    # User skills
    user_skill_rows = supabase.table("user_skills").select("skill_id").eq("user_id", user["user_id"]).execute().data
    user_skill_names = [skill_id_to_name[row["skill_id"]] for row in user_skill_rows]

    user_vec = build_skill_vector(user_skill_names, all_skill_names)

    matches = []

    for target in targets:
        target_skill_rows = supabase.table("user_skills").select("skill_id").eq("user_id", target["user_id"]).execute().data
        target_skill_names = [skill_id_to_name[row["skill_id"]] for row in target_skill_rows]

        target_vec = build_skill_vector(target_skill_names, all_skill_names)
        score = compute_match_score(user_vec, target_vec)

        if score > 0:  # only include relevant matches
            matches.append({
                "username": target["username"],
                "name": target["name"],
                "role": target["role"],
                "skills": target_skill_names,
                "score": score
            })

    # Sort matches by descending score
    matches.sort(key=lambda x: x["score"], reverse=True)

    return {"matches": matches}

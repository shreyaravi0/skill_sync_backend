from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.match_schema import MatchRequest
from app.ml.matcher import build_skill_vector, compute_match_score
from app.routes.users import get_user_by_username

router = APIRouter(prefix="/match", tags=["Matching"])

@router.post("/")
def match_mentor(data: MatchRequest, supabase = Depends(get_supabase)):

    mentee = get_user_by_username(data.mentee_username)
    if not mentee or mentee["role"] != "mentee":
        raise HTTPException(400, "Invalid mentee")

    # fetch all mentors
    mentors = (
        supabase.table("users")
        .select("*")
        .eq("role", "mentor")
        .execute()
        .data
    )

    # get skill lists
    all_skills = supabase.table("skills").select("name").execute().data
    all_skill_names = [s["name"] for s in all_skills]

    # mentee skills
    mentee_skill_rows = supabase.table("user_skills").select("skill_id").eq("user_id", mentee["user_id"]).execute().data
    mentee_skill_ids = [row["skill_id"] for row in mentee_skill_rows]

    # convert ids to names
    mentee_skill_names = [supabase.table("skills").select("name").eq("skill_id", id).execute().data[0]["name"]
                          for id in mentee_skill_ids]

    mentee_vec = build_skill_vector(mentee_skill_names, all_skill_names)

    best_match = None
    best_score = -1

    for mentor in mentors:
        mentor_skill_rows = supabase.table("user_skills").select("skill_id").eq("user_id", mentor["user_id"]).execute().data
        mentor_skill_ids = [row["skill_id"] for row in mentor_skill_rows]

        mentor_skill_names = [supabase.table("skills").select("name").eq("skill_id", id).execute().data[0]["name"]
                              for id in mentor_skill_ids]

        mentor_vec = build_skill_vector(mentor_skill_names, all_skill_names)

        score = compute_match_score(mentor_vec, mentee_vec)

        if score > best_score:
            best_score = score
            best_match = mentor

    return {"best_match": best_match, "score": best_score}

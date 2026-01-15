from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import logging

from app.db import get_supabase
from app.schemas.match_schema import MatchRequest
from app.routes.users import get_user_by_username
from app.ml.matcher import get_matcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["Matching"])

# ------------------------------------------------------------------
# Load semantic matcher ONCE at startup (fail fast if broken)
# ------------------------------------------------------------------
try:
    matcher = get_matcher()
except Exception as e:
    raise RuntimeError(
        "Semantic matcher failed to load. "
        "Ensure sentence-transformers, torch, and scikit-learn are installed."
    ) from e


# ------------------------------------------------------------------
# Find matches (SEMANTIC ONLY)
# ------------------------------------------------------------------
@router.post("/")
def find_matches(
    data: MatchRequest,
    supabase=Depends(get_supabase)
) -> Dict[str, List[Dict]]:
    """
    Find optimal mentor/mentee matches using semantic matching.

    Features:
    - Semantic embeddings (skill meaning, not just exact matches)
    - Multi-factor scoring
    - Experience-aware matching
    - Explainable recommendations
    """

    # Get requesting user
    user = get_user_by_username(data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user")

    role = user["role"]
    target_role = "mentor" if role == "mentee" else "mentee"

    # Fetch target users
    targets = (
        supabase.table("users")
        .select("*")
        .eq("role", target_role)
        .execute()
        .data
    )

    if not targets:
        return {"matches": []}

    # Fetch all skills once
    all_skills_data = supabase.table("skills").select("*").execute().data
    skill_id_to_name = {s["skill_id"]: s["name"] for s in all_skills_data}

    # Fetch user skills
    user_skill_rows = (
        supabase.table("user_skills")
        .select("skill_id")
        .eq("user_id", user["user_id"])
        .execute()
        .data
    )

    user_skill_names = [
        skill_id_to_name[row["skill_id"]]
        for row in user_skill_rows
        if row["skill_id"] in skill_id_to_name
    ]

    if not user_skill_names:
        logger.warning(f"User {user['username']} has no skills")
        return {"matches": []}

    user_experience = user.get("experience_level", "")

    matches: List[Dict] = []

    # --------------------------------------------------------------
    # SEMANTIC MATCHING LOOP
    # --------------------------------------------------------------
    for target in targets:
        target_skill_rows = (
            supabase.table("user_skills")
            .select("skill_id")
            .eq("user_id", target["user_id"])
            .execute()
            .data
        )

        target_skill_names = [
            skill_id_to_name[row["skill_id"]]
            for row in target_skill_rows
            if row["skill_id"] in skill_id_to_name
        ]

        if not target_skill_names:
            continue

        target_experience = target.get("experience_level", "")

        try:
            scores = matcher.compute_match_score(
                user_skills=user_skill_names,
                target_skills=target_skill_names,
                user_experience=user_experience,
                target_experience=target_experience,
                role=role,
            )

            total_score = float(scores["total"])

            if total_score > 0.2:
                explanation = matcher.generate_explanation(
                    scores, user_skill_names, target_skill_names
                )

                matches.append({
                    "username": target["username"],
                    "name": target["name"],
                    "role": target["role"],
                    "skills": target_skill_names,
                    "score": round(total_score, 4),
                    "explanation": explanation,
                    "score_breakdown": {
                        "semantic_similarity": round(float(scores["semantic_similarity"]), 3),
                        "skill_complementarity": round(float(scores["skill_complementarity"]), 3),
                        "experience_match": round(float(scores["experience_match"]), 3),
                        "skill_diversity": round(float(scores["skill_diversity"]), 3),
                    }
                })

        except Exception as e:
            logger.error(f"Match error for {target['username']}: {e}")

    matches.sort(key=lambda x: x["score"], reverse=True)

    logger.info(
        f"Found {len(matches)} matches for {user['username']} "
        f"(role={role}, skills={len(user_skill_names)})"
    )

    return {"matches": matches}


# ------------------------------------------------------------------
# Batch matching
# ------------------------------------------------------------------
@router.post("/batch")
def find_matches_batch(
    usernames: List[str],
    supabase=Depends(get_supabase)
) -> Dict[str, Dict]:
    """
    Find matches for multiple users in batch.
    """
    results = {}

    for username in usernames:
        try:
            request = MatchRequest(username=username)
            results[username] = find_matches(request, supabase)
        except Exception as e:
            logger.error(f"Batch match failed for {username}: {e}")
            results[username] = {"matches": [], "error": str(e)}

    return results


# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------
@router.get("/stats")
def get_matching_stats(supabase=Depends(get_supabase)) -> Dict:
    mentors = supabase.table("users").select("user_id").eq("role", "mentor").execute().data
    mentees = supabase.table("users").select("user_id").eq("role", "mentee").execute().data
    skills = supabase.table("skills").select("skill_id").execute().data
    user_skills = supabase.table("user_skills").select("user_id").execute().data

    return {
        "total_mentors": len(mentors),
        "total_mentees": len(mentees),
        "total_skills": len(skills),
        "total_skill_associations": len(user_skills),
        "avg_skills_per_user": round(
            len(user_skills) / max(len(mentors) + len(mentees), 1), 2
        ),
        "potential_matches": len(mentors) * len(mentees),
        "algorithm": "ADVANCED_SEMANTIC",
    }


# ------------------------------------------------------------------
# Algorithm info
# ------------------------------------------------------------------
@router.get("/algorithm-info")
def get_algorithm_info() -> Dict:
    return {
        "algorithm": "Advanced Semantic Matcher",
        "version": "2.0",
        "model": "all-MiniLM-L6-v2",
        "features": [
            "Semantic skill embeddings",
            "Multi-factor scoring",
            "Experience-aware matching",
            "Explainable recommendations",
        ],
        "weights": matcher.weights,
        "description": (
            "Uses sentence-transformer embeddings to understand skill meaning "
            "and combines similarity, complementarity, experience, and diversity."
        ),
    }

from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.mentorship_schema import MentorshipCreate
from app.routes.users import get_user_by_username

router = APIRouter(
    prefix="/mentorships",
    tags=["Mentorships"]
)
# ---------------- CREATE ----------------
@router.post("/")
def create_mentorship(data: MentorshipCreate, supabase=Depends(get_supabase)):

    # 1. Verify mentor exists
    mentor = get_user_by_username(data.mentor_name)
    if not mentor:
        raise HTTPException(400, "Mentor username does not exist")

    # 2. Check mentor role
    if mentor["role"] != "mentor":
        raise HTTPException(400, "This user is not a mentor")

    # 3. Verify mentee exists
    mentee = get_user_by_username(data.mentee_name)
    if not mentee:
        raise HTTPException(400, "Mentee username does not exist")

    # 4. Check mentee role
    if mentee["role"] != "mentee":
        raise HTTPException(400, "This user is not a mentee")

    # 5. Prevent self-mentoring
    if data.mentor_name == data.mentee_name:
        raise HTTPException(400, "User cannot mentor themselves")

    # 6. 🔥 CHECK IF MENTORSHIP ALREADY EXISTS
    existing = (
        supabase
        .table("mentorships")
        .select("*")
        .eq("mentor_name", data.mentor_name)
        .eq("mentee_name", data.mentee_name)
        .execute()
        .data
    )

    if existing:
        # ✅ Do NOT create again
        return {
            "message": "Mentorship already exists",
            "mentorship": existing[0]
        }

    # 7. ✅ CREATE MENTORSHIP ONLY IF NOT EXISTS
    mentorship = (
        supabase
        .table("mentorships")
        .insert({
            "mentor_name": data.mentor_name,
            "mentee_name": data.mentee_name,
        })
        .execute()
        .data[0]
    )

    return {
        "message": "Mentorship created successfully",
        "mentorship": mentorship
    }


# ---------------- READ ALL ----------------
@router.get("/")
def get_all_mentorships(supabase=Depends(get_supabase)):
    res = supabase.table("mentorships").select("*").execute()
    return res.data


# ---------------- READ SPECIFIC ----------------
@router.get("/{mentorship_id}")
def get_mentorship(mentorship_id: str, supabase=Depends(get_supabase)):
    res = (
        supabase.table("mentorships")
        .select("*")
        .eq("mentorship_id", mentorship_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Mentorship not found")

    return res.data[0]


# ---------------- UPDATE ----------------
@router.put("/{mentorship_id}")
def update_mentorship(mentorship_id: str, updates: dict, supabase=Depends(get_supabase)):
    res = (
        supabase.table("mentorships")
        .update(updates)
        .eq("mentorship_id", mentorship_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Mentorship not found")

    return res.data[0]


# ---------------- DELETE ----------------
@router.delete("/{mentorship_id}")
def delete_mentorship(mentorship_id: str, supabase=Depends(get_supabase)):
    res = (
        supabase.table("mentorships")
        .delete()
        .eq("mentorship_id", mentorship_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Mentorship not found")

    return {"message": "Mentorship deleted"}

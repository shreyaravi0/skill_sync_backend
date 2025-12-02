from fastapi import APIRouter, Depends, HTTPException
from app.db import get_supabase
from app.schemas.user_schema import UserCreate
from app.utils.hashing import hash_password, verify_password
from app.utils.auth import create_access_token


router = APIRouter()

# ---------------- CREATE ----------------
@router.post("/register")
def register(user: UserCreate, supabase = Depends(get_supabase)):
    exists = supabase.table("users").select("*").eq("username", user.username).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed = hash_password(user.password)

    res = supabase.table("users").insert({
        "username": user.username,
        "name": user.name,
        "password_hash": hashed,
        "role": user.role,
        "phone_number": user.phone_number,
        "experience_level": user.experience_level,
        "profile_summary": user.profile_summary
    }).execute()

    return res.data


# ---------------- READ ----------------
@router.get("/")
def get_all_users(supabase = Depends(get_supabase)):
    res = supabase.table("users").select("*").execute()
    return res.data

@router.get("/{username}")
def get_user(username: str, supabase = Depends(get_supabase)):
    res = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    return res.data[0]



# ---------------- UPDATE ----------------
@router.put("/{username}")
def update_user(username: str, updates: dict, supabase = Depends(get_supabase)):
    res = supabase.table("users").update(updates).eq("username", username).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return res.data[0]


# ---------------- DELETE ----------------
@router.delete("/{username}")
def delete_user(username: str, supabase = Depends(get_supabase)):
    res = supabase.table("users").delete().eq("username", username).execute()
    if res.data == []:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

supabase = get_supabase()
def get_user_by_username(username: str):
    """
    Fetch a single user by username.
    Returns a dict (the user row) or None if not found.
    """
    res = (
        supabase
        .table("users")
        .select("*")
        .eq("username", username)
        .execute()
    )

    return res.data[0] if res.data else None
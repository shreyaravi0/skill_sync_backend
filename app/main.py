from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users, skills, opportunities, mentorships, opportunity_skills, user_skills, match

app = FastAPI(
    title="SkillSync Backend (Supabase)",
    version="1.0.0"
)

# ---------------- CORS (Important for frontend) ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROUTERS ----------------
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(skills.router, prefix="/skills", tags=["Skills"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
app.include_router(mentorships.router)
app.include_router(opportunity_skills.router,prefix="/opportunity-skills",tags=["Opportunity Skills"])
app.include_router(user_skills.router)
app.include_router(match.router, prefix="/match", tags=["Matching"])
# ---------------- HEALTH CHECK ----------------
@app.get("/")
def root():
    return {"message": "SkillSync Backend is running 🚀"}
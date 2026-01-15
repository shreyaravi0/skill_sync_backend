# app/routes/resume_ats.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from app.ml.ats_scorer import ATSScorer
from app.routes.users import get_user_by_username

router = APIRouter(prefix="/resume-ats", tags=["Resume ATS"])

# Initialize ATS scorer
ats_scorer = ATSScorer()


@router.post("/analyze")
async def analyze_resume(
    username: str,
    file: UploadFile = File(...)
):
    """
    Analyze resume and get ATS score with improvement suggestions
    
    - Analyzes resume using ATS scorer
    - Returns comprehensive score with suggestions
    - NO database storage - pure computation
    """
    try:
        # Validate user exists
        user = get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF and DOCX are supported"
            )
        
        # Read file
        file_bytes = await file.read()
        
        if len(file_bytes) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 5MB"
            )
        
        # Score the resume
        score_result = ats_scorer.score_resume(file_bytes, file.filename)
        
        # Add filename for frontend reference
        score_result['filename'] = file.filename
        
        return {
            'message': 'Resume analyzed successfully',
            'score': score_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for resume ATS service
    """
    return {
        'status': 'healthy',
        'service': 'Resume ATS Scorer',
        'supported_formats': ['PDF', 'DOCX'],
        'max_file_size': '5MB'
    }
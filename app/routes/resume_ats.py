# app/routes/resume_ats.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from app.utils.firebase_resume_db import get_resume_db
from app.ml.ats_scorer import ATSScorer
from app.routes.users import get_user_by_username

router = APIRouter(prefix="/resume-ats", tags=["Resume ATS"])

# Initialize ATS scorer
ats_scorer = ATSScorer()


class ScoreResponse(BaseModel):
    """Response model for resume score"""
    id: str
    message: str
    score: dict


@router.post("/upload-and-score")
async def upload_and_score_resume(
    username: str,
    file: UploadFile = File(...)
):
    """
    Analyze resume and get ATS score with improvement suggestions
    
    - Analyzes resume using ATS scorer
    - Stores results in Firestore (NO file storage)
    - Returns comprehensive score with suggestions
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
        
        # Get Firebase database
        resume_db = get_resume_db()
        
        # Score the resume (no file upload needed)
        score_result = ats_scorer.score_resume(file_bytes, file.filename)
        
        # Prepare document for storage (only metadata and scores)
        score_document = {
            'file_name': file.filename,
            'overall_score': score_result['overall_score'],
            'keyword_score': score_result['keyword_score'],
            'formatting_score': score_result['formatting_score'],
            'readability_score': score_result['readability_score'],
            'completeness_score': score_result['completeness_score'],
            'matched_keywords': score_result['matched_keywords'],
            'missing_keywords': score_result['missing_keywords'],
            'suggestions': score_result['suggestions'],
            'overall_feedback': score_result['overall_feedback'],
            'word_count': score_result['word_count']
        }
        
        # Store in Firestore
        doc_id = resume_db.create_score(username, score_document)
        
        return {
            'id': doc_id,
            'message': 'Resume analyzed and score saved successfully',
            'score': score_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores/{username}")
async def get_user_resume_scores(username: str, limit: int = 10):
    """
    Get all resume scores for a user
    """
    try:
        # Validate user
        user = get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        resume_db = get_resume_db()
        scores = resume_db.get_user_scores(username, limit)
        
        return {
            'username': username,
            'total': len(scores),
            'scores': scores
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/{score_id}")
async def get_resume_score(score_id: str):
    """
    Get specific resume score by ID with detailed suggestions
    """
    try:
        resume_db = get_resume_db()
        score = resume_db.get_score_by_id(score_id)
        
        if not score:
            raise HTTPException(status_code=404, detail="Score not found")
        
        return score
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/score/{score_id}")
async def delete_resume_score(score_id: str, username: str):
    """
    Delete resume score (with ownership check)
    """
    try:
        resume_db = get_resume_db()
        success = resume_db.delete_score(score_id, username)
        
        if not success:
            raise HTTPException(status_code=404, detail="Score not found")
        
        return {'message': 'Resume score deleted successfully'}
        
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this score")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{username}")
async def get_user_statistics(username: str):
    """
    Get resume statistics and progress for user
    """
    try:
        user = get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        resume_db = get_resume_db()
        stats = resume_db.get_statistics(username)
        
        return {
            'username': username,
            'statistics': stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Get top scoring resumes (leaderboard)
    """
    try:
        resume_db = get_resume_db()
        top_scores = resume_db.get_top_scores(limit)
        
        return {
            'leaderboard': top_scores,
            'total': len(top_scores)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rescore/{score_id}")
async def rescore_resume(score_id: str, username: str):
    """
    Note: Re-scoring requires the original file which is not stored.
    Users need to re-upload the resume to get a new score.
    """
    try:
        resume_db = get_resume_db()
        
        # Get existing score
        existing = resume_db.get_score_by_id(score_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Score not found")
        
        # Check ownership
        if existing.get('username') != username:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        return {
            'message': 'To get a new score, please re-upload your resume',
            'score_id': score_id,
            'note': 'Original resume files are not stored for privacy reasons'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{score_id}")
async def get_detailed_suggestions(score_id: str):
    """
    Get detailed improvement suggestions for a specific resume
    """
    try:
        resume_db = get_resume_db()
        score = resume_db.get_score_by_id(score_id)
        
        if not score:
            raise HTTPException(status_code=404, detail="Score not found")
        
        # Organize suggestions by priority
        suggestions = score.get('suggestions', [])
        missing_keywords = score.get('missing_keywords', [])
        
        categorized_suggestions = {
            'critical': [],
            'important': [],
            'recommended': []
        }
        
        # Categorize suggestions based on keywords
        for suggestion in suggestions:
            if any(word in suggestion.lower() for word in ['add', 'include', 'missing']):
                categorized_suggestions['critical'].append(suggestion)
            elif any(word in suggestion.lower() for word in ['use', 'improve', 'optimize']):
                categorized_suggestions['important'].append(suggestion)
            else:
                categorized_suggestions['recommended'].append(suggestion)
        
        return {
            'score_id': score_id,
            'overall_score': score.get('overall_score'),
            'categorized_suggestions': categorized_suggestions,
            'missing_keywords': missing_keywords,
            'overall_feedback': score.get('overall_feedback'),
            'next_steps': generate_next_steps(score)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_next_steps(score: dict) -> list:
    """Generate actionable next steps based on score"""
    next_steps = []
    overall_score = score.get('overall_score', 0)
    
    if score.get('keyword_score', 0) < 60:
        next_steps.append("Focus on adding relevant industry keywords and technical skills")
    
    if score.get('formatting_score', 0) < 60:
        next_steps.append("Improve resume structure with clear section headers and bullet points")
    
    if score.get('readability_score', 0) < 60:
        next_steps.append("Use action verbs and quantify your achievements")
    
    if score.get('completeness_score', 0) < 60:
        next_steps.append("Ensure all essential sections are included (Experience, Education, Skills)")
    
    if overall_score >= 75:
        next_steps.append("Your resume is strong! Fine-tune based on specific job descriptions")
    
    return next_steps
# # app/routes/resume_ats.py
# from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
# from fastapi.responses import JSONResponse
# from typing import Optional
# from pydantic import BaseModel

# from app.utils.firebase_db import get_resume_db
# # from app.ml.ats_scorer import ATSScorer
# from app.routes.users import get_user_by_username

# router = APIRouter(prefix="/resume-ats", tags=["Resume ATS"])

# # Initialize ATS scorer
# ats_scorer = ATSScorer()


# class ScoreResponse(BaseModel):
#     """Response model for resume score"""
#     id: str
#     message: str
#     score: dict


# @router.post("/upload-and-score")
# async def upload_and_score_resume(
#     username: str,
#     file: UploadFile = File(...)
# ):
#     """
#     Upload resume and get ATS score (NoSQL - Firebase)
    
#     - Uploads file to Firebase Storage
#     - Analyzes resume using ATS scorer
#     - Stores results in Firestore NoSQL database
#     """
#     try:
#         # Validate user exists
#         user = get_user_by_username(username)
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Validate file type
#         if not file.filename.endswith(('.pdf', '.docx')):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid file type. Only PDF and DOCX are supported"
#             )
        
#         # Read file
#         file_bytes = await file.read()
        
#         if len(file_bytes) > 5 * 1024 * 1024:  # 5MB limit
#             raise HTTPException(
#                 status_code=400,
#                 detail="File too large. Maximum size is 5MB"
#             )
        
#         # Get Firebase NoSQL database
#         resume_db = get_resume_db()
        
#         # Upload to Firebase Storage
#         file_url = resume_db.upload_resume(
#             file_bytes=file_bytes,
#             filename=file.filename,
#             username=username
#         )
        
#         # Score the resume
#         score_result = ats_scorer.score_resume(file_bytes, file.filename)
        
#         # Prepare document for NoSQL storage
#         score_document = {
#             'file_name': file.filename,
#             'file_url': file_url,
#             'overall_score': score_result['overall_score'],
#             'formatting_score': score_result['formatting_score'],
#             'keyword_score': score_result['keyword_score'],
#             'readability_score': score_result['readability_score'],
#             'completeness_score': score_result['completeness_score'],
#             'matched_keywords': score_result['matched_keywords'],
#             'missing_keywords': score_result['missing_keywords'],
#             'suggestions': score_result['suggestions'],
#             'overall_feedback': score_result['overall_feedback'],
#             'word_count': score_result['word_count']
#         }
        
#         # Store in Firestore NoSQL
#         doc_id = resume_db.create_score(username, score_document)
        
#         return {
#             'id': doc_id,
#             'message': 'Resume uploaded and scored successfully',
#             'score': score_result
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/scores/{username}")
# async def get_user_resume_scores(username: str, limit: int = 10):
#     """
#     Get all resume scores for a user from Firebase NoSQL
#     """
#     try:
#         # Validate user
#         user = get_user_by_username(username)
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         resume_db = get_resume_db()
#         scores = resume_db.get_user_scores(username, limit)
        
#         return {
#             'username': username,
#             'total': len(scores),
#             'scores': scores
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/score/{score_id}")
# async def get_resume_score(score_id: str):
#     """
#     Get specific resume score by ID from Firebase NoSQL
#     """
#     try:
#         resume_db = get_resume_db()
#         score = resume_db.get_score_by_id(score_id)
        
#         if not score:
#             raise HTTPException(status_code=404, detail="Score not found")
        
#         return score
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/score/{score_id}")
# async def delete_resume_score(score_id: str, username: str):
#     """
#     Delete resume score from Firebase NoSQL (with ownership check)
#     """
#     try:
#         resume_db = get_resume_db()
#         success = resume_db.delete_score(score_id, username)
        
#         if not success:
#             raise HTTPException(status_code=404, detail="Score not found")
        
#         return {'message': 'Resume score deleted successfully'}
        
#     except HTTPException:
#         raise
#     except PermissionError:
#         raise HTTPException(status_code=403, detail="Unauthorized to delete this score")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/statistics/{username}")
# async def get_user_statistics(username: str):
#     """
#     Get resume statistics for user from Firebase NoSQL
#     """
#     try:
#         user = get_user_by_username(username)
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         resume_db = get_resume_db()
#         stats = resume_db.get_statistics(username)
        
#         return {
#             'username': username,
#             'statistics': stats
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/leaderboard")
# async def get_leaderboard(limit: int = 10):
#     """
#     Get top scoring resumes (leaderboard) from Firebase NoSQL
#     """
#     try:
#         resume_db = get_resume_db()
#         top_scores = resume_db.get_top_scores(limit)
        
#         return {
#             'leaderboard': top_scores,
#             'total': len(top_scores)
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/rescore/{score_id}")
# async def rescore_resume(score_id: str, username: str):
#     """
#     Re-analyze an existing resume with updated scoring algorithm
#     """
#     try:
#         resume_db = get_resume_db()
        
#         # Get existing score
#         existing = resume_db.get_score_by_id(score_id)
#         if not existing:
#             raise HTTPException(status_code=404, detail="Score not found")
        
#         # Check ownership
#         if existing.get('username') != username:
#             raise HTTPException(status_code=403, detail="Unauthorized")
        
#         # Download file from storage
#         file_url = existing.get('file_url')
#         # Note: You'd need to implement downloading from Firebase Storage here
#         # For now, return a message
        
#         return {
#             'message': 'Re-scoring functionality would download and re-analyze the file',
#             'score_id': score_id
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
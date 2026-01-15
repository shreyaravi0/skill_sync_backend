# app/utils/firebase_resume_db.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional
import os

class FirebaseResumeDB:
    """Firebase handler for resume ATS scoring system"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseResumeDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FirebaseResumeDB._initialized:
            self._initialize_firebase()
            FirebaseResumeDB._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase_rkey.json')
                
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(
                        f"Firebase key not found at {cred_path}. "
                        "Download from Firebase Console → Project Settings → Service Accounts"
                    )
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.scores_collection = 'resume_scores'
            
            print("✅ Firebase Resume DB initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise
    
    def create_score(self, username: str, score_data: Dict) -> str:
        """
        Store resume score in Firestore
        Returns: Document ID
        """
        try:
            # Add metadata
            score_document = {
                'username': username,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                **score_data
            }
            
            # Create document
            doc_ref = self.db.collection(self.scores_collection).document()
            doc_ref.set(score_document)
            
            return doc_ref.id
            
        except Exception as e:
            print(f"Error creating score: {e}")
            raise Exception(f"Failed to create score: {str(e)}")
    
    def get_user_scores(self, username: str, limit: int = 10) -> List[Dict]:
        """
        Get all resume scores for a user
        Returns: List of score documents
        """
        try:
            query = (
                self.db.collection(self.scores_collection)
                .where(filter=firestore.FieldFilter('username', '==', username))
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            scores = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Convert timestamp to ISO format
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                if data.get('updated_at'):
                    data['updated_at'] = data['updated_at'].isoformat()
                
                scores.append(data)
            
            return scores
            
        except Exception as e:
            print(f"Error fetching user scores: {e}")
            return []
    
    def get_score_by_id(self, score_id: str) -> Optional[Dict]:
        """
        Get specific score by ID
        Returns: Score document or None
        """
        try:
            doc = self.db.collection(self.scores_collection).document(score_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data['id'] = doc.id
            
            # Convert timestamps
            if data.get('created_at'):
                data['created_at'] = data['created_at'].isoformat()
            if data.get('updated_at'):
                data['updated_at'] = data['updated_at'].isoformat()
            
            return data
            
        except Exception as e:
            print(f"Error fetching score: {e}")
            return None
    
    def update_score(self, score_id: str, updates: Dict) -> bool:
        """
        Update a resume score
        Returns: True if successful
        """
        try:
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            self.db.collection(self.scores_collection).document(score_id).update(updates)
            return True
            
        except Exception as e:
            print(f"Error updating score: {e}")
            return False
    
    def delete_score(self, score_id: str, username: str) -> bool:
        """
        Delete a resume score (with ownership check)
        Returns: True if successful
        """
        try:
            # Get document first to verify ownership
            doc = self.db.collection(self.scores_collection).document(score_id).get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            if data.get('username') != username:
                raise PermissionError("You don't have permission to delete this score")
            
            # Delete from Firestore
            self.db.collection(self.scores_collection).document(score_id).delete()
            
            return True
            
        except Exception as e:
            print(f"Error deleting score: {e}")
            raise
    
    def get_statistics(self, username: str) -> Dict:
        """
        Get resume statistics for a user
        Returns: Statistics dictionary
        """
        try:
            scores = self.get_user_scores(username, limit=100)
            
            if not scores:
                return {
                    'total_resumes': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'improvement_trend': 'N/A'
                }
            
            overall_scores = [s.get('overall_score', 0) for s in scores]
            
            stats = {
                'total_resumes': len(scores),
                'average_score': sum(overall_scores) / len(overall_scores),
                'highest_score': max(overall_scores),
                'lowest_score': min(overall_scores),
                'latest_score': scores[0].get('overall_score', 0) if scores else 0,
                'improvement_trend': self._calculate_trend(overall_scores)
            }
            
            return stats
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return {}
    
    def _calculate_trend(self, scores: List[int]) -> str:
        """Calculate if scores are improving, declining, or stable"""
        if len(scores) < 2:
            return "Not enough data"
        
        recent_avg = sum(scores[:3]) / min(3, len(scores))
        older_avg = sum(scores[-3:]) / min(3, len(scores))
        
        if recent_avg > older_avg + 5:
            return "Improving ↑"
        elif recent_avg < older_avg - 5:
            return "Declining ↓"
        else:
            return "Stable →"
    
    def get_top_scores(self, limit: int = 10) -> List[Dict]:
        """
        Get leaderboard of top scoring resumes
        Returns: List of top scores (anonymized)
        """
        try:
            query = (
                self.db.collection(self.scores_collection)
                .order_by('overall_score', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            top_scores = []
            for doc in query.stream():
                data = doc.to_dict()
                
                # Anonymize username (show only first 3 chars + ***)
                username = data.get('username', 'anonymous')
                anonymized = username[:3] + '***' if len(username) > 3 else '***'
                
                top_scores.append({
                    'username': anonymized,
                    'overall_score': data.get('overall_score', 0),
                    'created_at': data.get('created_at').isoformat() if data.get('created_at') else None
                })
            
            return top_scores
            
        except Exception as e:
            print(f"Error fetching top scores: {e}")
            return []


# Singleton instance
def get_resume_db():
    """Get FirebaseResumeDB instance"""
    return FirebaseResumeDB()
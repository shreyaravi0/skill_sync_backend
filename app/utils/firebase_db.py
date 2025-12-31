# app/utils/firebase_db.py
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
from typing import Dict, List, Optional
import os

class FirebaseDB:
    """Firebase Firestore NoSQL Database Manager"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FirebaseDB._initialized:
            self._initialize_firebase()
            FirebaseDB._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Path to your service account key
            cred_path = os.path.join(os.path.dirname(__file__), 'firebase_key.json')
            
            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"Firebase key not found at {cred_path}. "
                    "Download from Firebase Console → Project Settings → Service Accounts"
                )
            
            cred = credentials.Certificate(cred_path)
            
            # Initialize with storage bucket
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'your-project-id.appspot.com'  # Replace with your bucket
            })
            
            self.db = firestore.client()
            self.bucket = storage.bucket()
            
            print("✅ Firebase initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise
    
    def get_db(self):
        """Get Firestore database instance"""
        return self.db
    
    def get_bucket(self):
        """Get Storage bucket instance"""
        return self.bucket


class ResumeScoreDB:
    """NoSQL operations for Resume Scores in Firestore"""
    
    def __init__(self):
        self.firebase = FirebaseDB()
        self.db = self.firebase.get_db()
        self.bucket = self.firebase.get_bucket()
        self.collection = 'resume_scores'
    
    def upload_resume(self, file_bytes: bytes, filename: str, username: str) -> str:
        """
        Upload resume to Firebase Storage
        Returns: Public URL of uploaded file
        """
        try:
            # Create unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_name = f"resumes/{username}/{timestamp}_{filename}"
            
            # Upload to Firebase Storage
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(
                file_bytes,
                content_type='application/pdf' if filename.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            # Make publicly accessible (optional - adjust based on your needs)
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            raise Exception(f"Failed to upload resume: {str(e)}")
    
    def create_score(self, username: str, score_data: Dict) -> str:
        """
        Create new resume score document
        Returns: Document ID
        """
        try:
            # Add metadata
            score_data['username'] = username
            score_data['created_at'] = firestore.SERVER_TIMESTAMP
            score_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Create document with auto-generated ID
            doc_ref = self.db.collection(self.collection).document()
            doc_ref.set(score_data)
            
            return doc_ref.id
            
        except Exception as e:
            raise Exception(f"Failed to create score: {str(e)}")
    
    def get_user_scores(self, username: str, limit: int = 10) -> List[Dict]:
        """
        Get all resume scores for a user
        Returns: List of score documents
        """
        try:
            scores_ref = (
                self.db.collection(self.collection)
                .where('username', '==', username)
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            docs = scores_ref.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Convert Firestore timestamp to string
                if 'created_at' in data and data['created_at']:
                    data['created_at'] = data['created_at'].isoformat()
                
                results.append(data)
            
            return results
            
        except Exception as e:
            raise Exception(f"Failed to get user scores: {str(e)}")
    
    def get_score_by_id(self, score_id: str) -> Optional[Dict]:
        """
        Get specific score by ID
        Returns: Score document or None
        """
        try:
            doc = self.db.collection(self.collection).document(score_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                
                if 'created_at' in data and data['created_at']:
                    data['created_at'] = data['created_at'].isoformat()
                
                return data
            
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get score: {str(e)}")
    
    def delete_score(self, score_id: str, username: str) -> bool:
        """
        Delete resume score (with ownership check)
        Returns: True if deleted, False if not found or unauthorized
        """
        try:
            doc_ref = self.db.collection(self.collection).document(score_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            # Check ownership
            if doc.to_dict().get('username') != username:
                raise PermissionError("Unauthorized to delete this score")
            
            # Delete associated file from storage if exists
            file_url = doc.to_dict().get('file_url')
            if file_url:
                try:
                    # Extract blob name from URL
                    blob_name = file_url.split('/')[-1]
                    blob = self.bucket.blob(f"resumes/{username}/{blob_name}")
                    blob.delete()
                except:
                    pass  # File might not exist
            
            doc_ref.delete()
            return True
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to delete score: {str(e)}")
    
    def get_top_scores(self, limit: int = 10) -> List[Dict]:
        """
        Get top scoring resumes (leaderboard)
        Returns: List of top score documents
        """
        try:
            scores_ref = (
                self.db.collection(self.collection)
                .order_by('overall_score', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            docs = scores_ref.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Remove sensitive data for leaderboard
                data.pop('file_url', None)
                
                if 'created_at' in data and data['created_at']:
                    data['created_at'] = data['created_at'].isoformat()
                
                results.append(data)
            
            return results
            
        except Exception as e:
            raise Exception(f"Failed to get top scores: {str(e)}")
    
    def update_score(self, score_id: str, username: str, updates: Dict) -> bool:
        """
        Update existing score
        Returns: True if updated, False if not found
        """
        try:
            doc_ref = self.db.collection(self.collection).document(score_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            # Check ownership
            if doc.to_dict().get('username') != username:
                raise PermissionError("Unauthorized to update this score")
            
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            doc_ref.update(updates)
            
            return True
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to update score: {str(e)}")
    
    def get_statistics(self, username: str) -> Dict:
        """
        Get user's resume statistics
        Returns: Statistics dictionary
        """
        try:
            scores = self.get_user_scores(username, limit=100)
            
            if not scores:
                return {
                    'total_resumes': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'latest_score': 0
                }
            
            scores_list = [s.get('overall_score', 0) for s in scores]
            
            return {
                'total_resumes': len(scores),
                'average_score': round(sum(scores_list) / len(scores_list), 1),
                'highest_score': max(scores_list),
                'latest_score': scores[0].get('overall_score', 0),
                'improvement': scores[0].get('overall_score', 0) - scores[-1].get('overall_score', 0) if len(scores) > 1 else 0
            }
            
        except Exception as e:
            raise Exception(f"Failed to get statistics: {str(e)}")


# Singleton instance
def get_resume_db():
    """Get ResumeScoreDB instance"""
    return ResumeScoreDB()
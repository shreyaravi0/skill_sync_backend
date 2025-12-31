# app/utils/firebase_chat_db.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional
import os

class FirebaseChatDB:
    """Firebase Firestore Chat Manager"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseChatDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FirebaseChatDB._initialized:
            self._initialize_firebase()
            FirebaseChatDB._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase_key.json')
                
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(
                        f"Firebase key not found at {cred_path}. "
                        "Download from Firebase Console → Project Settings → Service Accounts"
                    )
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.messages_collection = 'messages'
            
            print("✅ Firebase Chat DB initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise
    
    def get_db(self):
        """Get Firestore database instance"""
        return self.db
    
    # ===============================
    # MESSAGE OPERATIONS
    # ===============================
    
    def create_message(self, from_user: str, to_user: str, message: str) -> Dict:
        """
        Create a new message in Firestore
        Returns: Message document with ID and timestamp
        """
        try:
            message_data = {
                'from_user': from_user,
                'to_user': to_user,
                'message': message,
                'created_at': firestore.SERVER_TIMESTAMP,
                'read': False
            }
            
            # Create document with auto-generated ID
            doc_ref = self.db.collection(self.messages_collection).document()
            doc_ref.set(message_data)
            
            # Fetch the document to get the server timestamp
            doc = doc_ref.get()
            result = doc.to_dict()
            result['id'] = doc.id
            
            # Convert timestamp to ISO format for JSON serialization
            if result.get('created_at'):
                result['created_at'] = result['created_at'].isoformat()
            
            return result
            
        except Exception as e:
            print(f"Error creating message: {e}")
            raise Exception(f"Failed to create message: {str(e)}")
    
    def get_chat_history(self, user1: str, user2: str, limit: int = 100) -> List[Dict]:
        """
        Get chat history between two users
        Returns: List of messages ordered by created_at
        """
        try:
            # Query messages where (from_user=user1 AND to_user=user2) OR (from_user=user2 AND to_user=user1)
            # Firestore doesn't support OR queries directly, so we do two queries
            
            query1 = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('from_user', '==', user1))
                .where(filter=firestore.FieldFilter('to_user', '==', user2))
                .order_by('created_at')
                .limit(limit)
            )
            
            query2 = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('from_user', '==', user2))
                .where(filter=firestore.FieldFilter('to_user', '==', user1))
                .order_by('created_at')
                .limit(limit)
            )
            
            messages = []
            
            # Execute both queries
            for doc in query1.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                messages.append(data)
            
            for doc in query2.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                messages.append(data)
            
            # Sort by timestamp
            messages.sort(key=lambda x: x['created_at'])
            
            return messages
            
        except Exception as e:
            print(f"Error fetching chat history: {e}")
            return []
    
    def get_conversations(self, username: str) -> List[Dict]:
        """
        Get all conversations for a user
        Returns: List of conversation summaries with last message
        """
        try:
            # Get all messages where user is sender or receiver
            query1 = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('from_user', '==', username))
                .order_by('created_at', direction=firestore.Query.DESCENDING)
            )
            
            query2 = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('to_user', '==', username))
                .order_by('created_at', direction=firestore.Query.DESCENDING)
            )
            
            messages = []
            
            for doc in query1.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                messages.append(data)
            
            for doc in query2.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].isoformat()
                messages.append(data)
            
            # Sort by timestamp descending
            messages.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Group by conversation partner
            conversations = {}
            for msg in messages:
                other_user = (
                    msg['to_user'] if msg['from_user'] == username 
                    else msg['from_user']
                )
                
                if other_user not in conversations:
                    conversations[other_user] = {
                        'user': other_user,
                        'last_message': msg['message'],
                        'last_message_time': msg['created_at']
                    }
            
            return list(conversations.values())
            
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []
    
    def mark_messages_read(self, from_user: str, to_user: str) -> bool:
        """
        Mark all messages from from_user to to_user as read
        Returns: True if successful
        """
        try:
            query = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('from_user', '==', from_user))
                .where(filter=firestore.FieldFilter('to_user', '==', to_user))
                .where(filter=firestore.FieldFilter('read', '==', False))
            )
            
            batch = self.db.batch()
            for doc in query.stream():
                batch.update(doc.reference, {'read': True})
            
            batch.commit()
            return True
            
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return False
    
    def delete_conversation(self, user1: str, user2: str) -> bool:
        """
        Delete all messages between two users
        Returns: True if successful
        """
        try:
            # Query messages in both directions
            query1 = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('from_user', '==', user1))
                .where(filter=firestore.FieldFilter('to_user', '==', user2))
            )
            
            query2 = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('from_user', '==', user2))
                .where(filter=firestore.FieldFilter('to_user', '==', user1))
            )
            
            # Delete in batches (Firestore limit is 500 per batch)
            batch = self.db.batch()
            count = 0
            
            for doc in query1.stream():
                batch.delete(doc.reference)
                count += 1
                if count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            for doc in query2.stream():
                batch.delete(doc.reference)
                count += 1
                if count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            if count > 0:
                batch.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
    
    def get_unread_count(self, username: str) -> int:
        """
        Get count of unread messages for a user
        """
        try:
            query = (
                self.db.collection(self.messages_collection)
                .where(filter=firestore.FieldFilter('to_user', '==', username))
                .where(filter=firestore.FieldFilter('read', '==', False))
            )
            
            count = len(list(query.stream()))
            return count
            
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0


# Singleton instance
def get_firebase_chat_db():
    """Get FirebaseChatDB instance"""
    return FirebaseChatDB()
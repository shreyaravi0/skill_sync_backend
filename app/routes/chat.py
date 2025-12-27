from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
from datetime import datetime
from app.db import get_supabase

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])

# Store active connections
class ConnectionManager:
    def __init__(self):
        # Format: {username: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket
        print(f"✅ {username} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
        print(f"❌ {username} disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, username: str):
        """Send message to a specific user"""
        if username in self.active_connections:
            try:
                await self.active_connections[username].send_json(message)
            except Exception as e:
                print(f"Error sending to {username}: {e}")
                self.disconnect(username)
    
    def is_online(self, username: str) -> bool:
        """Check if user is currently connected"""
        return username in self.active_connections

manager = ConnectionManager()

@router.websocket("/chat/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    supabase = get_supabase()
    await manager.connect(username, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            # ===============================
            # 1. GET CHAT HISTORY
            # ===============================
            if message_type == "get_history":
                other_user = data.get("with_user")
                
                try:
                    # Query messages between these two users
                    result = supabase.table("messages").select("*").or_(
                        f"and(from_user.eq.{username},to_user.eq.{other_user}),"
                        f"and(from_user.eq.{other_user},to_user.eq.{username})"
                    ).order("created_at", desc=False).execute()
                    
                    messages = result.data if result.data else []
                    
                    # Send history back to requester
                    await websocket.send_json({
                        "type": "history",
                        "with_user": other_user,
                        "messages": messages,
                        "count": len(messages)
                    })
                    
                except Exception as e:
                    print(f"Error fetching history: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to load history: {str(e)}"
                    })
            
            # ===============================
            # 2. SEND MESSAGE
            # ===============================
            elif message_type == "message":
                from_user = data.get("from_user", username)
                to_user = data.get("to_user")
                text = data.get("text", "")
                
                if not to_user or not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing required fields: to_user or text"
                    })
                    continue
                
                # Store message in database
                try:
                    result = supabase.table("messages").insert({
                        "from_user": from_user,
                        "to_user": to_user,
                        "message": text
                    }).execute()
                    
                    message_data = result.data[0] if result.data else {}
                    message_id = message_data.get("id")
                    created_at = message_data.get("created_at", datetime.utcnow().isoformat())
                    
                except Exception as e:
                    print(f"Error storing message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to send message: {str(e)}"
                    })
                    continue
                
                # Prepare response message
                response = {
                    "type": "message",
                    "id": message_id,
                    "from_user": from_user,
                    "to_user": to_user,
                    "message": text,
                    "created_at": created_at
                }
                
                # Send to recipient if online
                if manager.is_online(to_user):
                    await manager.send_personal_message(response, to_user)
                
                # Send confirmation back to sender
                await websocket.send_json({
                    **response,
                    "status": "delivered" if manager.is_online(to_user) else "sent"
                })
            
            # ===============================
            # 3. TYPING INDICATOR
            # ===============================
            elif message_type == "typing":
                to_user = data.get("to_user")
                is_typing = data.get("is_typing", False)
                
                if to_user and manager.is_online(to_user):
                    await manager.send_personal_message({
                        "type": "typing",
                        "from_user": username,
                        "is_typing": is_typing
                    }, to_user)
            
            # ===============================
            # 4. GET ONLINE STATUS
            # ===============================
            elif message_type == "check_online":
                users_to_check = data.get("users", [])
                
                online_status = {
                    user: manager.is_online(user) 
                    for user in users_to_check
                }
                
                await websocket.send_json({
                    "type": "online_status",
                    "users": online_status
                })
            
            # ===============================
            # 5. GET ALL CONVERSATIONS
            # ===============================
            elif message_type == "get_conversations":
                try:
                    # Get all messages involving this user
                    result = supabase.table("messages").select(
                        "from_user, to_user, message, created_at"
                    ).or_(
                        f"from_user.eq.{username},to_user.eq.{username}"
                    ).order("created_at", desc=True).execute()
                    
                    # Group by conversation partner
                    conversations = {}
                    for msg in result.data:
                        other_user = (
                            msg["to_user"] if msg["from_user"] == username 
                            else msg["from_user"]
                        )
                        
                        if other_user not in conversations:
                            conversations[other_user] = {
                                "user": other_user,
                                "last_message": msg["message"],
                                "last_message_time": msg["created_at"],
                                "is_online": manager.is_online(other_user)
                            }
                    
                    await websocket.send_json({
                        "type": "conversations",
                        "data": list(conversations.values())
                    })
                    
                except Exception as e:
                    print(f"Error fetching conversations: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to load conversations: {str(e)}"
                    })
            
            # ===============================
            # 6. MARK MESSAGES AS READ
            # ===============================
            elif message_type == "mark_read":
                other_user = data.get("from_user")
                
                try:
                    # Update all unread messages from other_user as read
                    supabase.table("messages").update({
                        "read": True
                    }).eq("from_user", other_user).eq("to_user", username).eq("read", False).execute()
                    
                    await websocket.send_json({
                        "type": "marked_read",
                        "from_user": other_user
                    })
                    
                except Exception as e:
                    print(f"Error marking read: {e}")
            
            # ===============================
            # 7. DELETE CONVERSATION
            # ===============================
            elif message_type == "delete_conversation":
                other_user = data.get("with_user")
                
                try:
                    # Delete all messages between these users
                    supabase.table("messages").delete().or_(
                        f"and(from_user.eq.{username},to_user.eq.{other_user}),"
                        f"and(from_user.eq.{other_user},to_user.eq.{username})"
                    ).execute()
                    
                    await websocket.send_json({
                        "type": "conversation_deleted",
                        "with_user": other_user
                    })
                    
                except Exception as e:
                    print(f"Error deleting conversation: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to delete conversation: {str(e)}"
                    })
            
            # ===============================
            # 8. PING/PONG (Keep-alive)
            # ===============================
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(username)
    except Exception as e:
        print(f"WebSocket error for {username}: {e}")
        manager.disconnect(username)

@router.get("/online-users")
async def get_online_users():
    """REST endpoint to check who's online"""
    return {
        "online_users": list(manager.active_connections.keys()),
        "count": len(manager.active_connections)
    }
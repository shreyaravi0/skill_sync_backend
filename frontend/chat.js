// ================================
// Get users from localStorage
// ================================
const currentUser = localStorage.getItem("username");
const chatWith = localStorage.getItem("chatWith");

if (!currentUser || !chatWith) {
    alert("Chat session not initialized");
    window.location.href = "dashboard.html";
}

document.getElementById("chatWith").innerText = `Chat with ${chatWith}`;

// Shared chat ID
const chatId = [currentUser, chatWith].sort().join("_");



// ================================
// Firebase Initialization
// ================================
const firebaseConfig = {
  apiKey: "AIzaSyAIwkJhiaTzZCrmlHWIlefC8heKo6qd-mg",
  authDomain: "dbmsel-34b4d.firebaseapp.com",
  projectId: "dbmsel-34b4d",
  storageBucket: "dbmsel-34b4d.firebasestorage.app",
  messagingSenderId: "497021855060",
  appId: "1:497021855060:web:1006d3c35bb7bf4b1394c1",
  measurementId: "G-9Y85BEWT5E"
};

firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

// ================================
// Real-time Listener
// ================================
db.collection("chats")
  .doc(chatId)
  .collection("messages")
  .orderBy("timestamp")
  .onSnapshot(snapshot => {
      const chatBox = document.getElementById("chatBox");
      chatBox.innerHTML = "";

      snapshot.forEach(doc => {
          const msg = doc.data();
          const isMe = msg.sender === currentUser;

          const div = document.createElement("div");
          div.className = isMe ? "message sent" : "message received";

          div.innerHTML = `
              ${msg.text}
              <div class="timestamp">
                ${msg.timestamp
                    ? msg.timestamp.toDate().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                    : ""}
              </div>
          `;

          chatBox.appendChild(div);
      });

      chatBox.scrollTop = chatBox.scrollHeight;
  });


// ================================
// Send Message
// ================================
function sendMessage() {
    const input = document.getElementById("messageInput");
    const text = input.value.trim();
    if (!text) return;

    db.collection("chats")
      .doc(chatId)
      .collection("messages")
      .add({
          sender: currentUser,
          text: text,
          timestamp: firebase.firestore.FieldValue.serverTimestamp()
      });

    input.value = "";
}


// Enter key support
document.getElementById("messageInput")
  .addEventListener("keypress", e => {
      if (e.key === "Enter") sendMessage();
  });
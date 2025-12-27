const API = "http://127.0.0.1:8000";

const ENDPOINTS = {
    USERS: `${API}/users`,
    SKILLS: `${API}/skills`,
    USER_SKILLS: `${API}/user-skills`,
    MENTORSHIPS: `${API}/mentorships`,
    OPPORTUNITIES: `${API}/opportunities`,
    OPPORTUNITY_SKILLS: `${API}/opportunity-skills`,
    MATCH: `${API}/match/match`
};

const token = localStorage.getItem("token");
const username = localStorage.getItem("username");
const role = localStorage.getItem("role");

if (!token || !username) {
    alert("Session expired");
    window.location.href = "index.html";
}

const AUTH_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
};

// ========== UTILITY FUNCTIONS ==========

function getInitials(name) {
    if (!name) return "??";
    const parts = name.split(" ");
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function showNotification(msg, type = "info") {
    const container = document.getElementById("notificationContainer");
    const notif = document.createElement("div");
    notif.className = `notification ${type}`;
    notif.textContent = msg;
    container.appendChild(notif);
    
    setTimeout(() => {
        notif.style.opacity = "0";
        notif.style.transform = "translateX(400px)";
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}

// ========== INITIALIZATION ==========

let currentUserData = {};
let allSkills = [];

async function init() {
    // Set header info
    document.getElementById("headerUsername").textContent = username;
    document.getElementById("headerAvatar").textContent = getInitials(username);
    
    // Load all data
    await loadProfile();
    await loadAllSkills();
    await loadUserSkills();
    await loadMentorships();
    await loadOpportunities();
    await loadAllUsers();
}

// ========== LOGOUT ==========

document.getElementById("logoutBtn").onclick = () => {
    if (confirm("Are you sure you want to logout?")) {
        localStorage.clear();
        window.location.href = "index.html";
    }
};

// ========== PROFILE ==========

async function loadProfile() {
    try {
        const res = await fetch(`${ENDPOINTS.USERS}/${username}`, { headers: AUTH_HEADERS });
        currentUserData = await res.json();
        
        const initials = getInitials(currentUserData.name);
        document.getElementById("profileAvatar").textContent = initials;
        document.getElementById("profileName").textContent = currentUserData.name || username;
        
        const roleSpan = document.getElementById("profileRole");
        roleSpan.textContent = currentUserData.role || "User";
        roleSpan.className = currentUserData.role === "mentor" ? "badge badge-mentor" : "badge badge-mentee";
        
    } catch (err) {
        console.error("Failed to load profile:", err);
        showNotification("Failed to load profile", "error");
    }
}

// Edit Profile Modal
const editModal = document.getElementById("editProfileModal");

document.getElementById("editProfileBtn").onclick = () => {
    editModal.classList.add("show");
    document.getElementById("editName").value = currentUserData.name || "";
    document.getElementById("editRole").value = currentUserData.role || "";
    document.getElementById("editExperience").value = currentUserData.experience_level || "";
    document.getElementById("editSummary").value = currentUserData.profile_summary || "";
};

document.getElementById("closeModalBtn").onclick = () => {
    editModal.classList.remove("show");
};

document.getElementById("cancelEditBtn").onclick = () => {
    editModal.classList.remove("show");
};

editModal.onclick = (e) => {
    if (e.target === editModal) {
        editModal.classList.remove("show");
    }
};

document.getElementById("saveProfileBtn").onclick = async () => {
    const updatedData = {
        name: document.getElementById("editName").value,
        role: document.getElementById("editRole").value,
        experience_level: document.getElementById("editExperience").value,
        profile_summary: document.getElementById("editSummary").value
    };
    
    try {
        const res = await fetch(`${ENDPOINTS.USERS}/${username}`, {
            method: "PUT",
            headers: AUTH_HEADERS,
            body: JSON.stringify(updatedData)
        });
        
        if (!res.ok) throw new Error("Failed to update profile");
        
        showNotification("Profile updated successfully", "success");
        editModal.classList.remove("show");
        loadProfile();
    } catch (err) {
        console.error(err);
        showNotification("Failed to update profile", "error");
    }
};

// Delete Account
document.getElementById("deleteAccountBtn").onclick = async () => {
    if (confirm("⚠️ Are you sure you want to delete your account? This cannot be undone!")) {
        try {
            await fetch(`${ENDPOINTS.USERS}/${username}`, {
                method: "DELETE",
                headers: AUTH_HEADERS
            });
            localStorage.clear();
            window.location.href = "index.html";
        } catch (err) {
            console.error(err);
            showNotification("Failed to delete account", "error");
        }
    }
};

// ========== SKILLS ==========

async function loadAllSkills() {
    try {
        const res = await fetch(`${ENDPOINTS.SKILLS}/`, { headers: AUTH_HEADERS });
        allSkills = await res.json();
        
        const dropdown = document.getElementById("skillDropdown");
        dropdown.innerHTML = '<option value="">Select a skill</option>';
        allSkills.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s.name;
            opt.textContent = s.name;
            dropdown.appendChild(opt);
        });
        
        const oppSkills = document.getElementById("oppSkills");
        if (oppSkills) {
            oppSkills.innerHTML = '';
            allSkills.forEach(s => {
                const o = document.createElement("option");
                o.value = s.name;
                o.textContent = s.name;
                oppSkills.appendChild(o);
            });
        }
    } catch (err) {
        console.error("Failed to load skills:", err);
    }
}

async function loadUserSkills() {
    try {
        const res = await fetch(`${ENDPOINTS.USER_SKILLS}/${username}`, { headers: AUTH_HEADERS });
        const skills = res.ok ? await res.json() : [];
        
        const list = document.getElementById("userSkillsList");
        list.innerHTML = "";
        
        document.getElementById("skillCount").textContent = skills.length;
        
        if (skills.length === 0) {
            list.innerHTML = '<div class="no-data">No skills added yet</div>';
            return;
        }
        
        skills.forEach(s => {
            const tag = document.createElement("div");
            tag.className = "skill-tag";
            tag.innerHTML = `
                ${s.name || s.skill_name || "Unknown"}
                <button class="btn-delete" style="background: transparent; color: var(--danger); padding: 0; margin-left: 0.5rem;" onclick="removeUserSkill('${s.name || s.skill_name}')">×</button>
            `;
            list.appendChild(tag);
        });
    } catch (err) {
        console.error("Failed to load user skills:", err);
    }
}

document.getElementById("addSkillBtn").onclick = async () => {
    const skillName = document.getElementById("skillDropdown").value;
    if (!skillName) {
        showNotification("Please select a skill", "error");
        return;
    }
    
    try {
        const res = await fetch(`${ENDPOINTS.USER_SKILLS}/`, {
            method: "POST",
            headers: AUTH_HEADERS,
            body: JSON.stringify({ username, skill_names: [skillName] })
        });
        
        if (!res.ok) {
            const e = await res.json();
            throw new Error(e.detail || "Failed to add skill");
        }
        
        showNotification("Skill added successfully", "success");
        document.getElementById("skillDropdown").value = "";
        loadUserSkills();
    } catch (err) {
        console.error(err);
        showNotification(err.message, "error");
    }
};

async function removeUserSkill(skillName) {
    if (!confirm(`Remove skill: ${skillName}?`)) return;
    
    try {
        const res = await fetch(`${ENDPOINTS.USER_SKILLS}/${username}/${skillName}`, {
            method: "DELETE",
            headers: AUTH_HEADERS
        });
        
        if (!res.ok) {
            const e = await res.json();
            throw new Error(e.detail || "Failed to remove skill");
        }
        
        showNotification(`Skill removed`, "success");
        loadUserSkills();
    } catch (err) {
        console.error(err);
        showNotification(err.message, "error");
    }
}

// ========== MATCHING ==========

document.getElementById("findMatchesBtn").onclick = findMatches;

async function findMatches() {
    const matchResult = document.getElementById("matchResult");
    matchResult.innerHTML = '<div class="loading">🔍 Finding your best matches...</div>';
    
    try {
        const res = await fetch(`${ENDPOINTS.MATCH}/`, {
            method: "POST",
            headers: AUTH_HEADERS,
            body: JSON.stringify({ username })
        });
        
        const data = await res.json();
        matchResult.innerHTML = "";
        
        if (!data.matches || data.matches.length === 0) {
            matchResult.innerHTML = '<div class="no-data">No matches found. Try adding more skills!</div>';
            return;
        }
        
        data.matches.forEach(match => {
            const item = document.createElement("div");
            item.className = "match-item";
            item.innerHTML = `
                <div class="match-info">
                    <div class="match-name">${match.name} (@${match.username})</div>
                    <span class="badge ${match.role === 'mentor' ? 'badge-mentor' : 'badge-mentee'}">${match.role}</span>
                    <div class="match-score">${(match.score * 100).toFixed(0)}% Match</div>
                    <div class="match-skills">Skills: ${match.skills.join(", ") || "None"}</div>
                </div>
                <button class="btn btn-primary" onclick="addMentorship('${match.username}', '${match.role}')">Connect</button>
            `;
            matchResult.appendChild(item);
        });
    } catch (err) {
        console.error(err);
        matchResult.innerHTML = '<div class="no-data">Failed to find matches</div>';
        showNotification("Failed to find matches", "error");
    }
}

// ========== MENTORSHIPS ==========

async function addMentorship(other, otherRole) {
    const mentor = role === "mentor" ? username : other;
    const mentee = role === "mentee" ? username : other;
    
    try {
        const res = await fetch(`${ENDPOINTS.MENTORSHIPS}/`, {
            method: "POST",
            headers: AUTH_HEADERS,
            body: JSON.stringify({ mentor_name: mentor, mentee_name: mentee })
        });
        
        if (!res.ok) {
            const e = await res.json();
            throw new Error(e.detail || "Failed to create connection");
        }
        
        showNotification("Connection created successfully", "success");
        loadMentorships();
    } catch (err) {
        console.error(err);
        showNotification(err.message, "error");
    }
}

async function loadMentorships() {
    try {
        const res = await fetch(ENDPOINTS.MENTORSHIPS, { headers: AUTH_HEADERS });
        const data = await res.json();
        
        const list = document.getElementById("mentorshipList");
        list.innerHTML = "";
        
        const userMentorships = data.filter(m => m.mentor_name === username || m.mentee_name === username);
        
        document.getElementById("mentorshipCount").textContent = userMentorships.length;
        
        if (userMentorships.length === 0) {
            list.innerHTML = '<div class="no-data">No connections yet</div>';
            return;
        }
        
        userMentorships.forEach(m => {
            const item = document.createElement("div");
            item.className = "match-item";
            
            const otherUser = m.mentor_name === username ? m.mentee_name : m.mentor_name;
            const myRole = m.mentor_name === username ? "Mentor" : "Mentee";
            
            item.innerHTML = `
                <div class="match-info">
                    <div class="match-name">${m.mentor_name} → ${m.mentee_name}</div>
                    <span class="badge ${myRole === 'Mentor' ? 'badge-mentor' : 'badge-mentee'}">${myRole}</span>
                </div>
                <button class="btn btn-secondary" onclick="openChat('${otherUser}')" style="padding: 0.5rem 1rem;">💬 Chat</button>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        console.error("Failed to load mentorships:", err);
    }
}

function openChat(otherUser) {
    window.location.href = `chat.html?user=${encodeURIComponent(username)}&chatWith=${encodeURIComponent(otherUser)}`;
}

// ========== OPPORTUNITIES ==========

document.getElementById("createOppBtn").onclick = () => {
    document.getElementById("createOppForm").style.display = "block";
};

document.getElementById("cancelOppBtn").onclick = () => {
    document.getElementById("createOppForm").style.display = "none";
};

document.getElementById("saveOppBtn").onclick = async () => {
    const title = document.getElementById("oppTitle").value.trim();
    const description = document.getElementById("oppDescription").value.trim();
    const type = document.getElementById("oppType").value;
    
    const selectedSkills = Array.from(
        document.getElementById("oppSkills").selectedOptions
    ).map(o => o.value);
    
    if (!title) {
        showNotification("Please enter a title", "error");
        return;
    }
    
    try {
        const res = await fetch(`${ENDPOINTS.OPPORTUNITIES}/`, {
            method: "POST",
            headers: AUTH_HEADERS,
            body: JSON.stringify({
                title,
                description: description || "No description provided",
                posted_by: username,
                type
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to create opportunity");
        }
        
        const newOpp = await res.json();
        const oppId = newOpp.opp_id;
        
        if (selectedSkills.length > 0 && oppId) {
            const skillRes = await fetch(`${ENDPOINTS.OPPORTUNITY_SKILLS}/`, {
                method: "POST",
                headers: AUTH_HEADERS,
                body: JSON.stringify({
                    opportunity_id: oppId,
                    skill_names: selectedSkills
                })
            });
            
            if (!skillRes.ok) {
                console.warn("Failed to assign skills");
            }
        }
        
        showNotification("Opportunity created successfully!", "success");
        
        document.getElementById("createOppForm").style.display = "none";
        document.getElementById("oppTitle").value = "";
        document.getElementById("oppDescription").value = "";
        document.getElementById("oppType").value = "job";
        document.getElementById("oppSkills").selectedIndex = -1;
        
        loadOpportunities();
        
    } catch (err) {
        console.error("Error creating opportunity:", err);
        showNotification(err.message, "error");
    }
};

async function loadOpportunities() {
    try {
        const res = await fetch(`${ENDPOINTS.OPPORTUNITIES}/`, { headers: AUTH_HEADERS });
        
        if (!res.ok) throw new Error("Failed to load opportunities");
        
        const opportunities = await res.json();
        const oppList = document.getElementById("opportunityList");
        oppList.innerHTML = "";
        
        if (!opportunities || opportunities.length === 0) {
            oppList.innerHTML = '<div class="no-data">No opportunities available</div>';
            return;
        }
        
        opportunities.forEach(opp => {
            const card = document.createElement("div");
            card.className = "opportunity-card";
            
            let typeColor = "var(--primary)";
            if (opp.type === "mentorship") typeColor = "var(--secondary)";
            if (opp.type === "job") typeColor = "var(--accent)";
            
            card.innerHTML = `
                <span class="opportunity-type" style="background: ${typeColor};">${opp.type}</span>
                <div class="opportunity-title">${opp.title}</div>
                <div class="opportunity-description">${opp.description || ""}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                    <small style="color: var(--text-secondary);">by @${opp.posted_by}</small>
                    ${opp.posted_by === username ? `<button class="btn-delete" onclick="deleteOpportunity('${opp.opp_id}')">Delete</button>` : ""}
                </div>
            `;
            oppList.appendChild(card);
        });
        
    } catch (err) {
        console.error("Error loading opportunities:", err);
        const oppList = document.getElementById("opportunityList");
        oppList.innerHTML = '<div class="no-data">Failed to load opportunities</div>';
    }
}

async function deleteOpportunity(oppId) {
    if (!confirm("Delete this opportunity?")) return;
    
    try {
        const res = await fetch(`${ENDPOINTS.OPPORTUNITIES}/${oppId}`, {
            method: "DELETE",
            headers: AUTH_HEADERS
        });
        
        if (!res.ok) throw new Error("Failed to delete opportunity");
        
        showNotification("Opportunity deleted!", "success");
        loadOpportunities();
    } catch (err) {
        console.error("Error deleting opportunity:", err);
        showNotification(err.message, "error");
    }
}

// ========== ALL USERS ==========

async function loadAllUsers() {
    try {
        const res = await fetch(`${ENDPOINTS.USERS}/`, { headers: AUTH_HEADERS });
        const users = await res.json();
        
        const list = document.getElementById("allUsersList");
        list.innerHTML = "";
        
        users.forEach(u => {
            if (u.username === username) return; // Skip current user
            
            const item = document.createElement("div");
            item.className = "user-item";
            item.innerHTML = `
                <strong>${u.name}</strong> (@${u.username})
                <span class="badge ${u.role === 'mentor' ? 'badge-mentor' : 'badge-mentee'}" style="margin-left: 0.5rem;">${u.role}</span>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        console.error(err);
    }
}

document.getElementById("refreshUsersBtn").onclick = loadAllUsers;

// ========== SEARCH ==========

document.getElementById("searchInput").addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase();
    // You can implement search functionality here
    console.log("Search query:", query);
});

// ========== INITIALIZE ==========

init();
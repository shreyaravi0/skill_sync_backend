const API = "http://127.0.0.1:8000";

const ENDPOINTS = {
    USERS: `${API}/users`,
    SKILLS: `${API}/skills`,
    USER_SKILLS: `${API}/user-skills`,
    MENTORSHIPS: `${API}/mentorships`,
    OPPORTUNITIES: `${API}/opportunities`,
    OPPORTUNITY_SKILLS: `${API}/opportunity-skills/opportunity-skills`,
    MATCH: `${API}/match/match`
};

const token = localStorage.getItem("token");
const username = localStorage.getItem("username");

if (!token || !username) {
    alert("Session expired");
    window.location.href = "index.html";
}

document.getElementById("userDisplay").innerText = `👋 ${username}`;

const AUTH_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
};

// ---------- LOGOUT ----------
document.getElementById("logoutBtn").onclick = () => {
    if (confirm("Logout?")) {
        localStorage.clear();
        window.location.href = "index.html";
    }
};

// ---------- PROFILE ----------
let currentUserData = {};

async function loadProfile() {
    try {
        const res = await fetch(`${ENDPOINTS.USERS}/${username}`, { headers: AUTH_HEADERS });
        currentUserData = await res.json();

        const profileList = document.getElementById("profileList");
        profileList.innerHTML = "";
        ["name", "role", "experience_level", "profile_summary"].forEach(f => {
            const li = document.createElement("li");
            li.innerHTML = `<strong>${f.replace(/_/g," ").replace(/\b\w/g,l=>l.toUpperCase())}:</strong> ${currentUserData[f] || "N/A"}`;
            profileList.appendChild(li);
        });
    } catch (err) { console.error(err); }
}

// Edit Profile
document.getElementById("editProfileBtn").onclick = () => {
    document.getElementById("editProfileForm").style.display = "block";
    document.getElementById("editName").value = currentUserData.name || "";
    document.getElementById("editRole").value = currentUserData.role || "";
    document.getElementById("editExperience").value = currentUserData.experience_level || "";
    document.getElementById("editSummary").value = currentUserData.profile_summary || "";
};

document.getElementById("cancelEditBtn").onclick = () => {
    document.getElementById("editProfileForm").style.display = "none";
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
            method:"PUT",
            headers: AUTH_HEADERS,
            body: JSON.stringify(updatedData)
        });
        if(!res.ok) throw new Error("Failed");
        showNotification("Profile updated","success");
        document.getElementById("editProfileForm").style.display="none";
        loadProfile();
    } catch(err){ console.error(err); showNotification("Failed","error"); }
};

document.getElementById("deleteAccountBtn").onclick = async () => {
    if(confirm("Delete account?")) {
        try {
            await fetch(`${ENDPOINTS.USERS}/${username}`, { method:"DELETE", headers:AUTH_HEADERS });
            localStorage.clear(); window.location.href="index.html";
        } catch(err){ console.error(err); showNotification("Failed","error"); }
    }
};

loadProfile();
// ---------------- USER SKILLS ----------------

async function loadAllSkills() {
    const res = await fetch(`${ENDPOINTS.SKILLS}/`, { headers: AUTH_HEADERS });
    const skills = await res.json();

    // Populate dropdown for adding skills
    const dropdown = document.getElementById("skillDropdown");
    dropdown.innerHTML = '<option value="">Select a skill</option>';
    skills.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.name;
        opt.textContent = s.name;
        dropdown.appendChild(opt);
    });

    // Populate multi-select for opportunities
    const oppSkills = document.getElementById("oppSkills");
    if (oppSkills) {
        oppSkills.innerHTML = '';
        skills.forEach(s => {
            const o = document.createElement("option");
            o.value = s.name;
            o.textContent = s.name;
            oppSkills.appendChild(o);
        });
    }
}

async function loadUserSkills() {
    const res = await fetch(`${ENDPOINTS.USER_SKILLS}/${username}`, { headers: AUTH_HEADERS });
    const skills = res.ok ? await res.json() : [];
    const list = document.getElementById("userSkillsList");
    list.innerHTML = "";

    if (skills.length === 0) {
        list.innerHTML = "<li class='no-data'>No skills added yet</li>";
        return;
    }

    skills.forEach(s => {
        const li = document.createElement("li");
        li.className = "skill-tag";
        li.textContent = s.name || s.skill_name || "Unknown";

        // Add delete button
        const btn = document.createElement("button");
        btn.className = "btn-delete";
        btn.textContent = "×";
        btn.style.marginLeft = "6px";
        btn.onclick = () => removeUserSkill(s.name || s.skill_name);

        li.appendChild(btn);
        list.appendChild(li);
    });
}

// ADD SKILL
document.getElementById("addSkillBtn").onclick = async () => {
    const skillName = document.getElementById("skillDropdown").value;
    if (!skillName) {
        showNotification("Select a skill", "error");
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

        showNotification("Skill added", "success");
        loadUserSkills();
    } catch (err) {
        console.error(err);
        showNotification(err.message, "error");
    }
};

// REMOVE SKILL
async function removeUserSkill(skillName) {
    try {
        const res = await fetch(`${ENDPOINTS.USER_SKILLS}/${username}/${skillName}`, {
            method: "DELETE",
            headers: AUTH_HEADERS
        });

        if (!res.ok) {
            const e = await res.json();
            throw new Error(e.detail || "Failed to remove skill");
        }

        showNotification(`Skill '${skillName}' removed`, "success");
        loadUserSkills();
    } catch (err) {
        console.error(err);
        showNotification(err.message, "error");
    }
}

// Initial load
loadAllSkills();
loadUserSkills();


// ---------- MATCH ----------
async function findMatches() {
    const matchResult = document.getElementById("matchResult");
    matchResult.innerHTML = '<li class="loading">🔍 Finding matches...</li>';
    try {
        const res = await fetch(`${ENDPOINTS.MATCH}/`, {
            method:"POST", headers:AUTH_HEADERS, body:JSON.stringify({ username })
        });
        const data = await res.json();
        matchResult.innerHTML="";
        if(!data.matches || data.matches.length===0){ matchResult.innerHTML="<li class='no-data'>No matches found</li>"; return; }
        data.matches.forEach(match=>{
            const li=document.createElement("li"); li.className="match-item";
            li.innerHTML=`
                <div class="match-info">
                    <strong>${match.name} (${match.username})</strong>
                    <span class="badge">${match.role}</span>
                    <span class="score">Match Score: ${(match.score*100).toFixed(1)}%</span>
                    <p style="margin:4px 0; font-size:13px; color:#6b7280;">Skills: ${match.skills.join(", ") || "None"}</p>
                </div>
                <div class="match-actions">
                    <button class="btn-small secondary-btn" onclick="addMentorship('${match.username}','${match.role}')">➕ Connect</button>
                </div>`;
            matchResult.appendChild(li);
        });
    } catch(err){ console.error(err); matchResult.innerHTML="<li class='error'>Failed to find matches</li>"; }
}

// ---------- MENTORSHIP ----------
async function addMentorship(other, role) {
    const mentor = role==="mentee"?username:other; const mentee = role==="mentee"?other:username;
    try{
        const res=await fetch(`${ENDPOINTS.MENTORSHIPS}/`, { method:"POST", headers:AUTH_HEADERS, body:JSON.stringify({ mentor_name:mentor, mentee_name:mentee }) });
        if(!res.ok){ const e=await res.json(); throw new Error(e.detail||"Failed"); }
        showNotification("Mentorship added","success"); loadMentorships();
    }catch(err){ console.error(err); showNotification(err.message,"error"); }
}
// ----------------- LOAD MENTORSHIPS -----------------
async function loadMentorships() {
    try {
        const res = await fetch(ENDPOINTS.MENTORSHIPS, { headers: AUTH_HEADERS });
        const data = await res.json();

        const list = document.getElementById("mentorshipList");
        list.innerHTML = "";

        // Filter mentorships involving the current user
        const userMentorships = data.filter(m => m.mentor_name === username || m.mentee_name === username);

        if (userMentorships.length === 0) {
            list.innerHTML = "<li class='no-data'>No mentorships yet</li>";
            return;
        }

        userMentorships.forEach(m => {
            const li = document.createElement("li");
            li.className = "mentorship-item";

            // Determine the other user in this mentorship
            const otherUser = m.mentor_name === username ? m.mentee_name : m.mentor_name;
            const role = m.mentor_name === username ? "Mentor" : "Mentee";

            li.innerHTML = `
                <div class="mentorship-info">
                    <strong>${m.mentor_name}</strong> → <strong>${m.mentee_name}</strong>
                    <span class="badge-small">${role}</span>
                </div>
                <div class="mentorship-actions">
                    <button class="btn-small primary-btn" onclick="openChat('${otherUser}')">💬 Chat</button>
                </div>
            `;
            list.appendChild(li);
        });
    } catch (err) {
        console.error("Failed to load mentorships:", err);
    }
}

// Redirect to chat page with proper query params
function openChat(otherUser) {
    // Pass the current user and the other user to chat.html
    window.location.href = `chat.html?user=${encodeURIComponent(username)}&chatWith=${encodeURIComponent(otherUser)}`;
}

loadMentorships();

// ---------- OPPORTUNITIES ----------

// ---------------- OPPORTUNITIES ----------------

// Show create form
document.getElementById("createOppBtn").onclick = () => {
    document.getElementById("createOppForm").style.display = "block";
};

// Hide create form
document.getElementById("cancelOppBtn").onclick = () => {
    document.getElementById("createOppForm").style.display = "none";
};
// CREATE OPPORTUNITY
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
        // 1️⃣ Create opportunity (remove trailing slash)
        const res = await fetch(`${ENDPOINTS.OPPORTUNITIES}`, {
            method: "POST",
            headers: AUTH_HEADERS,
            body: JSON.stringify({
                title,
                description: description || "No description provided",
                posted_by: username,
                type // must be job | internship | mentorship
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to create opportunity");
        }

        const newOpp = await res.json();
        const oppId = newOpp.opp_id;

        // 2️⃣ Assign skills (remove trailing slash)
        if (selectedSkills.length > 0 && oppId) {
            const skillRes =await fetch(`${ENDPOINTS.OPPORTUNITY_SKILLS}`, {
    method: "POST",
    headers: AUTH_HEADERS,
    body: JSON.stringify({
        opportunity_id: oppId,
        skill_names: selectedSkills
    })
});

            if (!skillRes.ok) {
                const err = await skillRes.json();
                throw new Error(err.detail || "Failed to assign skills");
            }
        }

        showNotification("Opportunity created successfully!", "success");

        // 3️⃣ Reset form
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

// ---------------- LOAD OPPORTUNITIES ----------------
async function loadOpportunities() {
    try {
        const res = await fetch(`${ENDPOINTS.OPPORTUNITIES}/`, {
            headers: AUTH_HEADERS
        });

        if (!res.ok) throw new Error("Failed to load opportunities");

        const opportunities = await res.json();
        const oppList = document.getElementById("opportunityList");
        oppList.innerHTML = "";

        if (!opportunities || opportunities.length === 0) {
            oppList.innerHTML = `<li class="no-data">No opportunities available</li>`;
            return;
        }

        opportunities.forEach(opp => {
            const li = document.createElement("li");
            li.className = "opportunity-item";

            li.innerHTML = `
                <div>
                    <strong>${opp.title}</strong> <span class="badge">${opp.type}</span>
                    <p>${opp.description || ""}</p>
                </div>
                <div>
                    <button class="btn-delete" onclick="deleteOpportunity('${opp.opp_id}')">Delete</button>
                </div>
            `;
            oppList.appendChild(li);
        });

    } catch (err) {
        console.error("Error loading opportunities:", err);
        const oppList = document.getElementById("opportunityList");
        oppList.innerHTML = `<li class="error">Failed to load opportunities</li>`;
    }
}

// ---------------- DELETE OPPORTUNITY ----------------
async function deleteOpportunity(oppId) {
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

// ✅ Call loadOpportunities on page load
window.addEventListener("load", () => {
    loadOpportunities();
});


// ---------- ALL USERS ----------
async function loadAllUsers(){
    try{
        const res=await fetch(`${ENDPOINTS.USERS}/`, { headers: AUTH_HEADERS });
        const users=await res.json();
        const list=document.getElementById("allUsersList"); list.innerHTML="";
        users.forEach(u=>{
            const li=document.createElement("li"); li.className="user-item";
            li.innerHTML=`<strong>${u.name}</strong> (${u.username}) <span class="badge-small">${u.role}</span>`;
            list.appendChild(li);
        });
    }catch(err){ console.error(err); }
}

document.getElementById("refreshUsersBtn").onclick=loadAllUsers;
loadAllUsers();

// ---------- NOTIFICATION ----------
function showNotification(msg,type="info"){
    const notif=document.createElement("div"); notif.className=`notification ${type}`; notif.innerText=msg;
    document.body.appendChild(notif);
    setTimeout(()=>{ notif.style.opacity=0; setTimeout(()=>notif.remove(),300); },3000);
}

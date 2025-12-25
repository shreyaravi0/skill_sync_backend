const API = "http://127.0.0.1:8000";

const ENDPOINTS = {
  USERS: `${API}/users`,
  SKILLS: `${API}/skills`,
  USER_SKILLS: `${API}/user-skills/user-skills`,
  MENTORSHIPS: `${API}/mentorships/mentorships`,
  OPPORTUNITIES: `${API}/opportunities`,
  MATCH: `${API}/match/match/all`   
};

// ---------- SESSION CHECK ----------
const token = localStorage.getItem("token");
const username = localStorage.getItem("username");

if (!token || !username) {
  alert("Session expired");
  window.location.href = "index.html";
}

document.getElementById("userDisplay").innerText = username;

const AUTH_HEADERS = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${token}`
};

// ---------- LOGOUT ----------
document.getElementById("logoutBtn").onclick = () => {
  localStorage.clear();
  window.location.href = "index.html";
};

// ---------- PROFILE ----------
async function loadProfile() {
  const res = await fetch(`${ENDPOINTS.USERS}/${username}`, { headers: AUTH_HEADERS });
  const user = await res.json();

  profileList.innerHTML = "";
  ["name", "role", "experience_level", "profile_summary"].forEach(f => {
    const li = document.createElement("li");
    li.textContent = `${f}: ${user[f] || "N/A"}`;
    profileList.appendChild(li);
  });
}
loadProfile();

// ---------- SKILLS ----------
async function loadAllSkills() {
  const res = await fetch(ENDPOINTS.SKILLS, { headers: AUTH_HEADERS });
  const skills = await res.json();

  skillDropdown.innerHTML = "";
  skills.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.name;
    opt.textContent = s.name;
    skillDropdown.appendChild(opt);
  });
}

async function loadUserSkills() {
  const res = await fetch(`${ENDPOINTS.USER_SKILLS}/${username}`, {
    headers: AUTH_HEADERS
  });
  const skills = await res.json();

  userSkillsList.innerHTML = "";
  skills.forEach(s => {
    const li = document.createElement("li");
    li.textContent = s.name;
    userSkillsList.appendChild(li);
  });
}

addSkillBtn.onclick = async () => {
  await fetch(ENDPOINTS.USER_SKILLS, {
    method: "POST",
    headers: AUTH_HEADERS,
    body: JSON.stringify({
      username,
      skill_names: [skillDropdown.value]
    })
  });
  loadUserSkills();
};

loadAllSkills();
loadUserSkills();

// ---------- MATCH ----------
async function findMatches() {
  const role = matchRoleDropdown.value;

  const res = await fetch(ENDPOINTS.MATCH, {
    method: "POST",
    headers: AUTH_HEADERS,
    body: JSON.stringify({ username })
  });

  const data = await res.json();
  matchResult.innerHTML = "";

  if (!data.matches || data.matches.length === 0) {
    matchResult.innerHTML = "<li>No matches found</li>";
    return;
  }

  data.matches
    .filter(m => m.role === role)
    .forEach(m => {
      const li = document.createElement("li");
      li.innerHTML = `
        ${m.username} (${m.role}) — ${m.score.toFixed(2)}
        <button onclick="openChat('${m.username}')">Chat</button>
        <button onclick="addMentorship('${m.username}','${m.role}')">Add</button>
      `;
      matchResult.appendChild(li);
    });
}

// ---------- MENTORSHIP ----------
async function addMentorship(other, role) {
  const mentor = role === "mentee" ? username : other;
  const mentee = role === "mentee" ? other : username;

  await fetch(ENDPOINTS.MENTORSHIPS, {
    method: "POST",
    headers: AUTH_HEADERS,
    body: JSON.stringify({ mentor_name: mentor, mentee_name: mentee })
  });

  loadMentorships();
}

async function loadMentorships() {
  const res = await fetch(ENDPOINTS.MENTORSHIPS, { headers: AUTH_HEADERS });
  const data = await res.json();

  mentorshipList.innerHTML = "";
  data.forEach(m => {
    if (m.mentor_name === username || m.mentee_name === username) {
      const li = document.createElement("li");
      li.innerHTML = `
        ${m.mentor_name} → ${m.mentee_name}
        <button onclick="openChat('${m.mentor_name === username ? m.mentee_name : m.mentor_name}')">
          Chat
        </button>
      `;
      mentorshipList.appendChild(li);
    }
  });
}
loadMentorships();

// ---------- CHAT (REDIRECT ONLY – SAFE) ----------
function openChat(user) {
   window.location.href = `chat.html?user=${user}`;
}

// ---------- OPPORTUNITIES ----------
async function loadOpportunities() {
  const res = await fetch(ENDPOINTS.OPPORTUNITIES, { headers: AUTH_HEADERS });
  const opps = await res.json();

  opportunityList.innerHTML = "";
  opps.forEach(o => {
    const li = document.createElement("li");
    li.innerHTML = `<b>${o.title}</b><br>${o.description || ""}`;
    opportunityList.appendChild(li);
  });
}
loadOpportunities();
 
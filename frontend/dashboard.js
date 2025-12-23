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

if (!token || !username || username === "null") {
  alert("Session expired. Please login again.");
  localStorage.clear();
  window.location.href = "index.html";
}

document.getElementById("userDisplay").innerText = username;

const AUTH_HEADERS = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${token}`
};

// ---------- LOGOUT ----------
logoutBtn.onclick = () => {
  localStorage.clear();
  window.location.href = "index.html";
};

// ---------- PROFILE ----------
async function loadProfile() {
  const res = await fetch(`${ENDPOINTS.USERS}/${username}`, {
    headers: AUTH_HEADERS
  });
  const user = await res.json();

  profileList.innerHTML = "";
  ["name","role","experience_level","profile_summary"].forEach(f => {
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
  const skill = skillDropdown.value;
  await fetch(ENDPOINTS.USER_SKILLS, {
    method: "POST",
    headers: AUTH_HEADERS,
    body: JSON.stringify({
      username: username,
      skill_names: [skill]
    })
  });
  loadUserSkills();
};

loadAllSkills();
loadUserSkills();

// ---------- MATCH ----------
async function findMatches() {
  const role = matchRoleDropdown.value; // mentor or mentee

  try {
    const res = await fetch(ENDPOINTS.MATCH, {
      method: "POST",
      headers: AUTH_HEADERS,
      body: JSON.stringify({ username }) // send current username
    });

    if (!res.ok) {
      matchResult.innerHTML = `<li>Error fetching matches: ${res.status}</li>`;
      return;
    }

    const data = await res.json();
    matchResult.innerHTML = "";

    if (data.matches && data.matches.length > 0) {
      const filteredMatches = data.matches.filter(m => m.role === role);

      if (filteredMatches.length === 0) {
        matchResult.innerHTML = "<li>No matches found for this role</li>";
        return;
      }

      filteredMatches.forEach(match => {
        const li = document.createElement("li");
        li.innerHTML = `
          ${match.username} (${match.role}) — Score: ${match.score.toFixed(2)}
          <button onclick="startChat('${match.username}')">Chat</button>
          <button onclick="addMentorship('${match.username}', '${match.role}')">Add to Mentorship</button>
        `;
        matchResult.appendChild(li);
      });
    } else {
      matchResult.innerHTML = "<li>No matches found</li>";
    }
  } catch (err) {
    console.error(err);
    matchResult.innerHTML = "<li>Error fetching matches</li>";
  }
}

// ---------- ADD TO MENTORSHIP ----------
async function addMentorship(otherUsername, otherRole) {
  const mentor = otherRole === "mentee" ? username : otherUsername;
  const mentee = otherRole === "mentee" ? otherUsername : username;

  try {
    const res = await fetch(`${ENDPOINTS.MENTORSHIPS}`, {
      method: "POST",
      headers: AUTH_HEADERS,
      body: JSON.stringify({
        mentor_name: mentor,
        mentee_name: mentee
      })
    });

    if (!res.ok) {
      alert(`Error creating mentorship: ${res.status}`);
      return;
    }

    alert(`Mentorship added: ${mentor} → ${mentee}`);
    loadMentorships(); // refresh mentorship list
  } catch (err) {
    console.error(err);
    alert("Error adding mentorship");
  }
}

// ---------- MENTORSHIPS ----------
async function loadMentorships() {
  const res = await fetch(ENDPOINTS.MENTORSHIPS, {
    headers: AUTH_HEADERS
  });
  const data = await res.json();

  mentorshipList.innerHTML = "";
  data.forEach(m => {
    if (m.mentor_name === username || m.mentee_name === username) {
      const li = document.createElement("li");
      li.textContent = `${m.mentor_name} → ${m.mentee_name}`;
      mentorshipList.appendChild(li);
    }
  });
}
loadMentorships();

// ---------- CHAT ----------
function addChatUser(user) {
  if ([...chatUser.options].some(o => o.value === user)) return;
  const opt = document.createElement("option");
  opt.value = user;
  opt.textContent = user;
  chatUser.appendChild(opt);
}

function startChat(toUser) {
  addChatUser(toUser);
}

function sendMessage() {
  const msg = chatInput.value;
  const to = chatUser.value;
  if (!msg || !to) return;

  const div = document.createElement("div");
  div.textContent = `You → ${to}: ${msg}`;
  chatBox.appendChild(div);
  chatInput.value = "";
}

// ---------- OPPORTUNITIES ----------
async function loadOpportunities() {
  const res = await fetch(ENDPOINTS.OPPORTUNITIES, {
    headers: AUTH_HEADERS
  });
  const opps = await res.json();

  opportunityList.innerHTML = "";
  opps.forEach(o => {
    const li = document.createElement("li");
    li.innerHTML = `<b>${o.title}</b><br>${o.description || ""}`;
    opportunityList.appendChild(li);
  });
}
loadOpportunities();

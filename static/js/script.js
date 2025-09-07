const API_BASE = "/accounts";

// Helper: always attach Bearer token
function authHeaders() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "/auth/login";
    return {};
  }
  return {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };
}

// Function to set up the WebSocket connection for real-time updates
function setupWebSocket() {
    const token = localStorage.getItem("token");
    if (!token) {
        console.warn("No authentication token found. Not connecting to WebSocket.");
        return;
    }

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Pass the authentication token as a query parameter
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/posts/?token=${token}`;

    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log("WebSocket connected for real-time updates.");
    };

    websocket.onmessage = (event) => {
        console.log("Received a message from the server:", event.data);
        // When a message is received, re-fetch all data to ensure the UI is up-to-date.
        fetchAndDisplayPosts();
        fetchAccounts();
    };

    websocket.onclose = (event) => {
        console.log("WebSocket connection closed:", event);
        // Attempt to reconnect after a short delay
        if (event.code !== 4000) { // Don't reconnect on a 4000 (invalid token) error
            setTimeout(setupWebSocket, 3000);
        } else {
            console.error("Connection closed due to invalid token. Please log in again.");
        }
    };

    websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}


async function fetchAccounts() {
  try {
    const res = await fetch(`${API_BASE}/me`, { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to fetch accounts");
    const accountData = await res.json();

    const accountsList = document.getElementById("accounts-list");

    const addAccountButton = `
      <button onclick="linkNewAccount()"
        class="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-xl shadow transition">
        ➕ Add New Account
      </button>
    `;

    if (Array.isArray(accountData) && accountData.length > 0) {
      accountsList.innerHTML = accountData
        .map(
          acc => `
            <li class="bg-gray-800 p-4 rounded-xl shadow border border-gray-700 flex justify-between items-center">
              <div>
                <span>@${acc.username} (${acc.platform || "Unknown"})</span>
                <span class="text-gray-400 text-sm block">${acc.followers_count} followers · ${acc.following_count} following</span>
              </div>
             <button onclick="deleteAccount('${acc.username}', '${acc.platform}')"
                   class="text-red-500 hover:text-red-600 ml-4 font-bold">
                <i class="fa-solid fa-trash-can"></i>
            </button>
            </li>
          `
        )
        .join("") + addAccountButton;
    } else {
      accountsList.innerHTML = `
        <li class="bg-gray-800 p-4 rounded-xl shadow border border-gray-700 text-gray-400">
          No accounts linked
        </li>
        ${addAccountButton}
      `;
    }
  } catch (err) {
    document.getElementById("accounts-list").innerHTML = `
      <li class="bg-gray-800 p-4 rounded-xl shadow border border-gray-700 text-red-400">
        Error loading accounts
      </li>
      <button onclick="linkNewAccount()"
        class="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-xl shadow transition">
        ➕ Add New Account
      </button>
    `;
  }
}

// Delete account function
async function deleteAccount(username, platform) {
  if (!confirm(`Are you sure you want to delete @${username} (${platform})?`)) return;

  try {
    const res = await fetch(`${API_BASE}/${platform}/${username}`, {
      method: 'DELETE',
      headers: authHeaders()
    });

    if (!res.ok) throw new Error("Failed to delete account");

    alert(`Account @${username} deleted successfully`);
    fetchAccounts();
  } catch (err) {
    alert("Error deleting account: " + err.message);
  }
}


function linkNewAccount() {
  document.getElementById("add-account-form").classList.remove("hidden");
}

function cancelAccountForm() {
  document.getElementById("add-account-form").classList.add("hidden");
}

// Handle form submit
document.getElementById("accountForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = {
    platform: formData.get("platform"),
    username: formData.get("username"),
  };

  try {
    const res = await fetch(`${API_BASE}/add-platform`, {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Failed to add account");
    alert("Account added successfully!");
    cancelAccountForm();
    fetchAccounts();
  } catch (err) {
    alert("Error: " + err.message);
  }
});


async function fetchAndDisplayPosts() {
    try {
        const res = await fetch(`${API_BASE}/tweets`, { headers: authHeaders() });
        if (!res.ok) throw new Error("Failed to fetch posts");
        const posts = await res.json();

        const publishedPosts = posts.filter(p => p.status === "published");
        const scheduledPosts = posts.filter(p => p.status === "scheduled");

        renderPosts(publishedPosts, "feed");
        renderPosts(scheduledPosts, "schedule");

    } catch (err) {
        // Handle error for both sections
        const feedList = document.getElementById("posts-list");
        if (feedList) {
            feedList.innerHTML = `
                <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
                    <p class="text-red-400">⚠️ Error loading posts</p>
                </div>`;
        }

        const scheduleList = document.getElementById("scheduled-posts-list");
        if (scheduleList) {
            scheduleList.innerHTML = `
                <br/>
                <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
                    <p class="text-red-400">⚠️ Error loading scheduled posts</p>
                </div>`;
        }
    }
}

function renderPosts(posts, sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;

    let postsList;
    if (sectionId === "schedule") {
        postsList = document.getElementById("scheduled-posts-list");
    } else {
        postsList = document.getElementById("posts-list");
    }

    if (!postsList) {
        console.error(`Container for ${sectionId} not found.`);
        return;
    }

    if (posts.length > 0) {
        postsList.innerHTML = posts
            .map(p => {
                let statusText = p.status;
                if (p.status === "scheduled") {
                    const scheduledTime = new Date(p.created_at).toLocaleString();
                    statusText = `Scheduled (will post at ${scheduledTime})`;
                }
               return `
                   <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 mt-4">
                       <p class="text-gray-200 mb-2">${p.text || "No text"}</p>
                       <p class="text-gray-500 text-sm">Status: ${statusText}</p>
                   </div>`;
            })
            .join("");
    } else {
        postsList.innerHTML = `
            <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
                <p class="text-gray-400">No ${sectionId === "feed" ? "recent posts" : "scheduled posts"} to display.</p>
            </div>`;
    }
}

async function fetchFollowers() {
  try {
    const res = await fetch(`${API_BASE}/followers`, { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to fetch followers");
    const followers = await res.json();

    const followersList = document.getElementById("followers-list");

    if (Array.isArray(followers) && followers.length > 0) {
      followersList.innerHTML = followers.map(f => `
        <li class="bg-gray-800 p-4 rounded-2xl shadow-lg border border-gray-700 flex items-center justify-between gap-4 hover:bg-gray-700 transition">
          <div class="flex items-center gap-4">
            ${f.profilePicUrl
              ? `<img src="${f.profilePicUrl}" alt="${f.username}" class="w-10 h-10 rounded-full border-2 border-gray-600">`
              : `<div class="w-10 h-10 rounded-full border-2 border-gray-600 bg-gray-600 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-6 h-6 text-gray-400">
                    <path fill-rule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.714.77l-.025-.002-.025-.002a7.487 7.487 0 00-14.966 0l-.025.002-.025.002a.75.75 0 01-.714-.77z" clip-rule="evenodd" />
                  </svg>
                </div>`
            }
            <div class="flex-grow">
              <p class="text-gray-200 font-semibold">@${f.username || "Unknown"}</p>
              <p class="text-gray-400 text-sm">${f.name || ""}</p>
            </div>
          </div>
          <button onclick="unfollowUser('${f.username}')" class="bg-red-500 text-white font-bold py-1 px-4 rounded-full text-sm hover:bg-red-600 transition">
            <i class="fa-solid fa-user-minus"></i> Unfollow
          </button>
        </li>
      `).join('');
    } else {
      followersList.innerHTML = `
        <li class="bg-gray-800 p-6 rounded-2xl shadow-inner border border-gray-700 text-gray-400 text-center">
          <p class="text-lg mb-2">✨ You don't have any followers yet!</p>
          <p class="text-sm">Share your profile to connect with others.</p>
        </li>
      `;
    }
  } catch (err) {
    console.error("Error loading followers:", err);
    document.getElementById("followers-list").innerHTML = `
      <li class="bg-gray-800 p-4 rounded-2xl shadow-lg border border-gray-700 text-red-400 text-center">
        Error loading followers. Please try again later.
      </li>
    `;
  }
}

async function fetchFollowing() {
  try {
    const res = await fetch(`${API_BASE}/following`, { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to fetch following");
    const following = await res.json();

    const followingList = document.getElementById("following-list");

    if (Array.isArray(following) && following.length > 0) {
      followingList.innerHTML = following.map(f => `
        <li class="bg-gray-800 p-4 rounded-2xl shadow-lg border border-gray-700 flex items-center justify-between gap-4 hover:bg-gray-700 transition">
          <div class="flex items-center gap-4">
            ${f.profilePicUrl
              ? `<img src="${f.profilePicUrl}" alt="${f.username}" class="w-10 h-10 rounded-full border-2 border-gray-600">`
              : `<div class="w-10 h-10 rounded-full border-2 border-gray-600 bg-gray-600 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-6 h-6 text-gray-400">
                    <path fill-rule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.714.77l-.025-.002-.025-.002a7.487 7.487 0 00-14.966 0l-.025.002-.025.002a.75.75 0 01-.714-.77z" clip-rule="evenodd" />
                  </svg>
                </div>`
            }
            <div>
              <p class="text-gray-200 font-semibold">@${f.username || "Unknown"}</p>
              <p class="text-gray-400 text-sm">${f.name || ""}</p>
            </div>
          </div>
          <button onclick="unfollowUser('${f.username}')" class="bg-gray-600 text-white font-bold py-1 px-4 rounded-full text-sm hover:bg-gray-700 transition">
            <i class="fa-solid fa-user-xmark"></i> Unfollow
          </button>
        </li>
      `).join('');
    } else {
      followingList.innerHTML = `
        <li class="bg-gray-800 p-6 rounded-2xl shadow-inner border border-gray-700 text-gray-400 text-center">
          <p class="text-lg mb-2">😔 You aren't following anyone yet.</p>
          <p class="text-sm">Find someone to follow and start connecting!</p>
        </li>
      `;
    }
  } catch (err) {
    console.error("Error loading following:", err);
    document.getElementById("following-list").innerHTML = `
      <li class="bg-gray-800 p-4 rounded-2xl shadow-lg border border-gray-700 text-red-400 text-center">
        Error loading who you're following. Please try again.
      </li>
    `;
  }
}

async function schedulePost() {
  const content = document.getElementById("post-content").value;
  let scheduled_time = document.getElementById("scheduled-time").value;

  if (!content || !scheduled_time) {
    alert("Please fill out both fields");
    return;
  }

  const localDate = new Date(scheduled_time);
  scheduled_time = localDate.toISOString();

  try {
    const res = await fetch(`${API_BASE}/schedule`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ content, scheduled_time })
    });

    const data = await res.json();
    
    if (!res.ok) {
        const errorMsg = data.detail || "An unexpected error occurred.";
        alert(`Error: ${errorMsg}`);
        return;
    }

    const localScheduled = new Date(data.scheduled_time).toLocaleString();

    alert(`${data.msg} (Scheduled at ${localScheduled})`);

    // Clear the form fields after successful scheduling
    document.getElementById("post-content").value = "";
    document.getElementById("scheduled-time").value = "";

    fetchAndDisplayPosts();
  } catch (err) {
    alert("Error scheduling post");
  }
}

// Auto-fetch data on load
window.addEventListener("DOMContentLoaded", () => {
    fetchAccounts();
    fetchAndDisplayPosts();
    fetchFollowers();
    fetchFollowing();
    setupWebSocket(); // Start the WebSocket connection
});

document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const signupContainer = document.getElementById("signup-container");
  const messageDiv = document.getElementById("message");
  const adminLoginButton = document.getElementById("admin-login-button");
  const adminLogoutButton = document.getElementById("admin-logout-button");
  const adminLoginDialog = document.getElementById("admin-login-dialog");
  const adminLoginForm = document.getElementById("admin-login-form");
  const adminLoginMessage = document.getElementById("admin-login-message");
  const adminPassword = document.getElementById("admin-password");
  let isAdmin = false;

  function setAdminState(authenticated) {
    isAdmin = authenticated;
    adminLoginButton.classList.toggle("hidden", isAdmin);
    adminLogoutButton.classList.toggle("hidden", !isAdmin);
    signupContainer.classList.toggle("hidden", !isAdmin);
  }

  function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML =
        '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => `<li>
                      <span class="participant-email">${email}</span>
                      ${
                        isAdmin
                          ? `<button class="delete-btn" data-activity="${name}" data-email="${email}" aria-label="Unregister ${email} from ${name}">❌</button>`
                          : ""
                      }
                    </li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function fetchAdminSession() {
    try {
      const response = await fetch("/admin/session");
      if (!response.ok) {
        throw new Error("Failed to check administrator session");
      }

      const result = await response.json();
      setAdminState(result.authenticated === true);
    } catch (error) {
      setAdminState(false);
      console.error("Error checking administrator session:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        // Refresh activities list to show updated participants
        await fetchActivities();
        showMessage(result.message, "success");
      } else {
        if (response.status === 401) {
          setAdminState(false);
          await fetchActivities();
        }
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  adminLoginButton.addEventListener("click", () => {
    adminLoginDialog.showModal();
  });

  document
    .getElementById("admin-login-cancel")
    .addEventListener("click", () => {
      adminLoginDialog.close();
    });

  adminLoginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    adminLoginMessage.textContent = "";
    adminLoginMessage.className = "message hidden";

    try {
      const response = await fetch("/admin/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: document.getElementById("admin-username").value,
          password: adminPassword.value,
        }),
      });

      const result = await response.json();
      adminPassword.value = "";

      if (!response.ok) {
        adminLoginMessage.textContent =
          result.detail || "Unable to sign in. Please try again.";
        adminLoginMessage.className = "message error";
        return;
      }

      setAdminState(true);
      adminLoginDialog.close();
      await fetchActivities();
      showMessage("Signed in as a teacher.", "info");
    } catch (error) {
      adminPassword.value = "";
      adminLoginMessage.textContent = "Unable to sign in. Please try again.";
      adminLoginMessage.className = "message error";
      console.error("Error signing in:", error);
    }
  });

  adminLogoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/admin/logout", { method: "POST" });
      if (!response.ok) {
        throw new Error("Failed to sign out");
      }

      setAdminState(false);
      await fetchActivities();
      showMessage("Signed out.", "info");
    } catch (error) {
      showMessage("Unable to sign out. Please try again.", "error");
      console.error("Error signing out:", error);
    }
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        signupForm.reset();

        // Refresh activities list to show updated participants
        await fetchActivities();
        showMessage(result.message, "success");
      } else {
        if (response.status === 401) {
          setAdminState(false);
          await fetchActivities();
        }
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchAdminSession().then(fetchActivities);
});

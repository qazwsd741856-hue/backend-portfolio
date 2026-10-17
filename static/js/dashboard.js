const token = sessionStorage.getItem("access_token");

const loginLink = document.getElementById("login-link");
const logoutButton = document.getElementById("logout-button");
const welcomeMessage = document.getElementById("welcome-message")
const adminLink = document.getElementById("admin-link");

if (token) {
    loginLink.hidden = true;
    loadCurrentUser();
}

logoutButton.addEventListener("click", function() {
    sessionStorage.removeItem("access_token");
    window.location.reload();
});

async function loadCurrentUser() {
    try {
        const response = await fetch("/users/me", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (response.status === 401 || response.status === 403) {
            sessionStorage.removeItem("access_token");
            window.location.reload();
            return;
        }

        if (!response.ok) {
            throw new Error("Load current user failed: " + response.status);
        }

        const user = await response.json();

        welcomeMessage.textContent = `Welcome, ${user.name}!`;
        welcomeMessage.hidden = false;
        logoutButton.hidden=false;
        if (user.role === "admin") {
            adminLink.hidden = false;
        }

    } catch (error) {
        console.error("Load current user failed:", error);
    }
}

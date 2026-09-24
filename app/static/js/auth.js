/**
 * PocketSmart AI - Authentication Form Handlers
 */

document.addEventListener("DOMContentLoaded", () => {
    // Register Form Handler
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const errorBox = document.getElementById("auth-error");
            if (errorBox) errorBox.style.display = "none";

            const name = document.getElementById("name").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirm_password") ? document.getElementById("confirm_password").value : password;

            if (password !== confirmPassword) {
                showAuthError("Passwords do not match.");
                return;
            }

            const submitBtn = registerForm.querySelector("button[type='submit']");
            const originalText = submitBtn.innerText;
            submitBtn.disabled = true;
            submitBtn.innerText = "Creating Account...";

            try {
                const res = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, password })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Registration failed.");
                }

                // Redirect to dashboard
                window.location.href = "/dashboard";
            } catch (err) {
                showAuthError(err.message);
                submitBtn.disabled = false;
                submitBtn.innerText = originalText;
            }
        });
    }

    // Login Form Handler
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const errorBox = document.getElementById("auth-error");
            if (errorBox) errorBox.style.display = "none";

            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            const submitBtn = loginForm.querySelector("button[type='submit']");
            const originalText = submitBtn.innerText;
            submitBtn.disabled = true;
            submitBtn.innerText = "Signing In...";

            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Invalid credentials.");
                }

                // Redirect to dashboard
                window.location.href = "/dashboard";
            } catch (err) {
                showAuthError(err.message);
                submitBtn.disabled = false;
                submitBtn.innerText = originalText;
            }
        });
    }

    // Helper demo account filler
    const demoFillBtn = document.getElementById("demo-fill-btn");
    if (demoFillBtn) {
        demoFillBtn.addEventListener("click", () => {
            const emailInput = document.getElementById("email");
            const passInput = document.getElementById("password");
            if (emailInput && passInput) {
                emailInput.value = "alex.demo@pocketsmart.ai";
                passInput.value = "PocketSmart2026!";
            }
        });
    }
});

function showAuthError(msg) {
    const errorBox = document.getElementById("auth-error");
    if (errorBox) {
        errorBox.innerText = msg;
        errorBox.style.display = "flex";
    } else {
        alert(msg);
    }
}

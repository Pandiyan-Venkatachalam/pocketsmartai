/**
 * PocketSmart AI - Global Main Script
 */

// -------------------------------------------------------------
// 1. Global Sidebar Open / Close Functions
// -------------------------------------------------------------
function isMobileView() {
    return window.innerWidth <= 900;
}

function openSidebar(e) {
    if (e && e.preventDefault) { e.preventDefault(); e.stopPropagation(); }
    document.body.classList.remove("sidebar-closed");
    document.documentElement.classList.remove("sidebar-closed");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (isMobileView()) {
        sidebar?.classList.add("open");
        overlay?.classList.add("active");
    }
    try { localStorage.setItem("ps_sidebar_closed", "false"); } catch (err) {}
}

function closeSidebar(e) {
    if (e && e.preventDefault) { e.preventDefault(); e.stopPropagation(); }
    document.body.classList.add("sidebar-closed");
    document.documentElement.classList.add("sidebar-closed");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    sidebar?.classList.remove("open");
    overlay?.classList.remove("active");
    try { localStorage.setItem("ps_sidebar_closed", "true"); } catch (err) {}
}

function toggleSidebar(forceOpen, e) {
    if (e && e.preventDefault) { e.preventDefault(); e.stopPropagation(); }
    const isClosed = document.body.classList.contains("sidebar-closed") || 
                     document.documentElement.classList.contains("sidebar-closed");
    if (forceOpen === true || isClosed) {
        openSidebar(e);
    } else {
        closeSidebar(e);
    }
}

// -------------------------------------------------------------
// 2. Universal Card Click Redirection Handler
// -------------------------------------------------------------
function handleCardClick(e, url, target) {
    if (!url) return;
    // Don't intercept clicks on links, buttons, inputs, icons
    if (e && e.target && e.target.closest && e.target.closest("a, button, input, select, textarea, .icon-btn, .delete-history-btn, .sidebar-toggle-btn")) {
        return;
    }
    if (target === "_blank") {
        window.open(url, "_blank", "noopener,noreferrer");
    } else {
        window.location.href = url;
    }
}

// Expose on window immediately so inline onclicks can never fail
window.openSidebar = openSidebar;
window.closeSidebar = closeSidebar;
window.toggleSidebar = toggleSidebar;
window.handleCardClick = handleCardClick;

document.addEventListener("DOMContentLoaded", () => {
    // Keyboard shortcut: Ctrl+B or Cmd+B to toggle sidebar
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
            e.preventDefault();
            toggleSidebar();
        }
    });

    // Close mobile drawer when clicking navigation links
    document.querySelectorAll(".sidebar-link").forEach(link => {
        link.addEventListener("click", () => {
            if (isMobileView()) {
                closeSidebar();
            }
        });
    });

    // Event delegation fallback for any elements with [data-href]
    document.addEventListener("click", (e) => {
        if (e.target.closest("a, button, input, select, textarea, .icon-btn, .sidebar-toggle-btn, .sidebar-open-btn, .sidebar-close-btn, .delete-history-btn")) {
            return;
        }
        const clickable = e.target.closest("[data-href], .planner-card, .clickable-card, .clickable-row, .stat-card");
        if (!clickable) return;
        const targetUrl = clickable.dataset.href;
        if (targetUrl) {
            handleCardClick(e, targetUrl, clickable.dataset.target);
        }
    });

    // Logout button handler
    const logoutBtn = document.getElementById("nav-logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                const res = await fetch("/api/auth/logout", { method: "POST" });
                if (res.ok) {
                    window.location.href = "/login";
                }
            } catch (err) {
                console.error("Logout error:", err);
                window.location.href = "/login";
            }
        });
    }
});

// Toast notification helper
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.style.position = "fixed";
        container.style.bottom = "20px";
        container.style.right = "20px";
        container.style.zIndex = "9999";
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.gap = "10px";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `alert alert-${type === 'error' ? 'error' : 'success'}`;
    toast.style.minWidth = "250px";
    toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.5)";
    toast.innerText = message;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

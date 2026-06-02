const GOOGLE_CLIENT_ID = "822402579088-cr2ea0olrf87stpqe9r7dg6qonqsja6r.apps.googleusercontent.com";
const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? "http://127.0.0.1:8000" 
    : "https://smartweather-xyja.onrender.com";
window.BACKEND_URL = BACKEND_URL;

// Ensure auth functions are globally accessible
window.auth = {
    getUser: () => {
        const user = localStorage.getItem('user_profile');
        return user ? JSON.parse(user) : null;
    },
    
    isLoggedIn: () => {
        return window.auth.getUser() !== null;
    },
    
    logout: () => {
        localStorage.removeItem('user_profile');
        window.location.href = 'index.html';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inject GIS Client Script
    if (!document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
        script.onload = initializeGoogleAuth;
    } else {
        initializeGoogleAuth();
    }

    // 2. Adjust navbar UI
    setupNavbarUI();

    // 3. Navigation Guard checks
    applyRouteGuard();
});

function initializeGoogleAuth() {
    if (typeof google === 'undefined') {
        setTimeout(initializeGoogleAuth, 100);
        return;
    }

    google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true
    });

    // Render login button if auth container is present
    renderAuthControls();
}

async function handleCredentialResponse(response) {
    try {
        const res = await fetch(`${BACKEND_URL}/api/auth/google`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token: response.credential })
        });

        if (!res.ok) {
            throw new Error('Verification failed');
        }

        const userData = await res.json();
        localStorage.setItem('user_profile', JSON.stringify(userData));
        
        // Sync local prediction history to backend if exists
        await syncLocalHistory(userData.google_id);

        // Reload page to reflect authenticated state
        window.location.reload();
    } catch (error) {
        console.error('Authentication Error:', error);
        alert('Google Sign-In failed. Please try again.');
    }
}

async function syncLocalHistory(googleId) {
    const localHistory = localStorage.getItem('predictionHistory');
    if (!localHistory) return;

    try {
        const historyArray = JSON.parse(localHistory);
        for (const item of historyArray) {
            // If it hasn't been synced (no backend record)
            if (item.inputs && !item.is_synced) {
                await fetch(`${BACKEND_URL}/api/recommend_crop`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...item.inputs,
                        google_id: googleId
                    })
                });
            }
        }
        // Once synced, we can remove predictionHistory to avoid duplicate syncs, or mark them
        localStorage.removeItem('predictionHistory');
    } catch (e) {
        console.error('Failed to sync history:', e);
    }
}

function setupNavbarUI() {
    const navLinks = document.querySelector('.navbar .nav-links');
    if (!navLinks) return;

    // Check if Dashboard link exists, if not create it
    let dashboardLink = document.getElementById('nav-dashboard');
    if (!dashboardLink) {
        dashboardLink = document.createElement('a');
        dashboardLink.id = 'nav-dashboard';
        dashboardLink.href = 'dashboard.html';
        dashboardLink.setAttribute('data-translate-key', 'dashboard');
        dashboardLink.textContent = 'Dashboard';
        
        // Insert before language-selector or at the end
        const langSelector = document.getElementById('language-selector');
        if (langSelector) {
            navLinks.insertBefore(dashboardLink, langSelector);
        } else {
            navLinks.appendChild(dashboardLink);
        }
    }

    // Add CSS transition/pointer-events helper for profile dropdown
    let authContainer = document.getElementById('navbar-auth-container');
    if (!authContainer) {
        authContainer = document.createElement('div');
        authContainer.id = 'navbar-auth-container';
        authContainer.style.marginLeft = '20px';
        authContainer.style.display = 'inline-block';
        
        const langSelector = document.getElementById('language-selector');
        if (langSelector) {
            navLinks.insertBefore(authContainer, langSelector);
        } else {
            navLinks.appendChild(authContainer);
        }
    }

    const isLoggedIn = window.auth.isLoggedIn();
    if (isLoggedIn) {
        dashboardLink.style.display = 'inline-block';
    } else {
        dashboardLink.style.display = 'none';
    }
}

function renderAuthControls() {
    const container = document.getElementById('navbar-auth-container');
    if (!container) return;

    const isLoggedIn = window.auth.isLoggedIn();

    if (isLoggedIn) {
        const user = window.auth.getUser();
        container.innerHTML = `
            <div class="user-profile-menu">
                <img src="${user.picture}" alt="${user.name}" class="navbar-avatar" id="avatar-toggle">
                <div class="profile-dropdown" id="profile-dropdown">
                    <div class="dropdown-header">
                        <p class="dropdown-name">${user.name}</p>
                        <p class="dropdown-email">${user.email}</p>
                    </div>
                    <hr>
                    <a href="dashboard.html" class="dropdown-item">📊 Dashboard</a>
                    <a href="#" class="dropdown-item" id="btn-logout">🚪 Sign Out</a>
                </div>
            </div>
        `;

        const avatarToggle = document.getElementById('avatar-toggle');
        const dropdown = document.getElementById('profile-dropdown');
        
        avatarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
        });

        document.addEventListener('click', () => {
            dropdown.classList.remove('active');
        });

        document.getElementById('btn-logout').addEventListener('click', (e) => {
            e.preventDefault();
            window.auth.logout();
        });
    } else {
        container.innerHTML = `<div id="google-signin-btn"></div>`;
        
        if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
            google.accounts.id.renderButton(
                document.getElementById("google-signin-btn"),
                { 
                    theme: "outline", 
                    size: "medium",
                    shape: "pill",
                    text: "signin_with"
                }
            );
        }
    }
}

function applyRouteGuard() {
    const protectedPages = ['input.html', 'disease.html', 'chatbot.html', 'dashboard.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage) && !window.auth.isLoggedIn()) {
        showLoginOverlay();
    }
}

function showLoginOverlay() {
    // Remove if already exists
    const existing = document.getElementById('auth-guard-overlay');
    if (existing) return;

    const overlay = document.createElement('div');
    overlay.id = 'auth-guard-overlay';
    overlay.innerHTML = `
        <div class="overlay-card">
            <h2 data-translate-key="access_restricted">🔒 Access Restricted</h2>
            <p data-translate-key="access_restricted_desc">Please sign in with your Google account to access this feature, track your farm's recommendation history, and utilize the advanced dashboard tools.</p>
            <div id="overlay-signin-btn" class="overlay-signin-btn"></div>
            <a href="index.html" class="btn btn-secondary" style="margin-top: 15px; width: 100%;" data-translate-key="return_home">Return to Home</a>
        </div>
    `;

    document.body.appendChild(overlay);
    if (window.applyTranslations) window.applyTranslations(localStorage.getItem('selectedLanguage') || 'en');

    // Stop all keyboard/click interaction with the rest of the page
    document.body.style.overflow = 'hidden';

    // Initialize google button in the overlay
    renderOverlaySignInButton();
}

function renderOverlaySignInButton() {
    if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) {
        setTimeout(renderOverlaySignInButton, 100);
        return;
    }

    google.accounts.id.renderButton(
        document.getElementById("overlay-signin-btn"),
        { 
            theme: "filled_blue", 
            size: "large",
            shape: "rectangular",
            text: "signin_with",
            width: 250
        }
    );
}

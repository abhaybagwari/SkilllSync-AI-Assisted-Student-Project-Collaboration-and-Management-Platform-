
const SESSION_KEY = "skillsync_session";

function setSession(user) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function getSession() {
    const stored = sessionStorage.getItem(SESSION_KEY);

    if (!stored) return null;

    try {
        return JSON.parse(stored);
    } catch {
        return null;
    }
}

function clearSession() {
    sessionStorage.removeItem(SESSION_KEY);
}

function logout() {
    clearSession();
    window.location.href = "login.html";
}

function requireRole(allowedRoles) {
    const user = getSession();

    if (!user || !allowedRoles.includes(user.role)) {
        window.location.href = "login.html";
        return null;
    }

    return user;
}

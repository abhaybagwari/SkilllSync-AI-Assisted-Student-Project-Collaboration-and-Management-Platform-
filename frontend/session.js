const SESSION_KEY = "skillsync_session";
const API_PATTERN = /^https?:\/\/(127\.0\.0\.1|localhost):8000\//;

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

const originalFetch = window.fetch.bind(window);

window.fetch = async function (input, init = {}) {
    const url = typeof input === "string" ? input : input.url;
    const user = getSession();
    const isApiCall = API_PATTERN.test(url);
    let sentToken = false;

    if (isApiCall && user && user.token) {
        const headers = new Headers(init.headers || (typeof input !== "string" ? input.headers : undefined));

        if (!headers.has("Authorization")) {
            headers.set("Authorization", "Bearer " + user.token);
            sentToken = true;
        }

        init = { ...init, headers };
    }

    const response = await originalFetch(input, init);

    if (sentToken && response.status === 401 && !url.includes("/auth/")) {
        clearSession();
        window.location.href = "login.html";
    }

    return response;
};
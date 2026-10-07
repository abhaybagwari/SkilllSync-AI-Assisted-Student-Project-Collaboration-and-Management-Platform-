function showPassword() {
    let password = document.getElementById("password");
    let button = document.querySelector(".password-box button");

    if (password.type === "password") {
        password.type = "text";
        button.innerText = "Hide";
    } else {
        password.type = "password";
        button.innerText = "Show";
    }
}

async function login(event) {
    event.preventDefault();

    let role = document.getElementById("role").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    if (role === "" || email === "" || password === "") {
        alert("Please fill all the details.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password,
                role: role
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Login failed.");
            return;
        }

        alert(data.message);

        localStorage.setItem("userId", data.user.user_id);
        localStorage.setItem("userEmail", data.user.email);
        localStorage.setItem("userRole", data.user.role);
        localStorage.setItem("userName", data.name);

        if (data.user.role === "Team Member") {
            window.location.href = "student-dashboard.html";
        } else if (data.user.role === "Team Leader") {
            window.location.href = "leader-dashboard.html";
        } else if (data.user.role === "Mentor") {
            window.location.href = "mentor-dashboard.html";
        }

    } catch (error) {
        console.error("Login error:", error);
        alert("Unable to connect to the SkillSync backend. Make sure FastAPI is running.");
    }
}
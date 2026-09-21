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

function login(event) {
    event.preventDefault();

    let role = document.getElementById("role").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    if (role === "" || email === "" || password === "") {
        alert("Please fill all the details.");
        return;
    }

    if (role === "student") {
        window.location.href = "student-dashboard.html";
    }
    else if (role === "leader") {
        window.location.href = "leader-dashboard.html";
    }
    else if (role === "mentor") {
        window.location.href = "mentor-dashboard.html";
    }
}
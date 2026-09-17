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
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    if (email === "" || password === "") {
        alert("Please enter your email and password.");
    } else {
        alert("Login successful!");
    }
}
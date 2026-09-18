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

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (email === "" || password === "") {
        alert("Please enter your email and password.");
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
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert(data.message);
        } else {
            alert("Login failed.");
        }

    } catch (error) {
        console.error(error);
        alert("Could not connect to the backend.");
    }
}
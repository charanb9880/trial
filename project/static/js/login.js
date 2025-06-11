document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const loginError = document.getElementById('login-error');
    const signupError = document.getElementById('signup-error');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                credentials: 'same-origin', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            if (data.success) {
                window.location.href = '/applications';  
            } else {
                loginError.textContent = data.message || 'Invalid login credentials.';
            }
        } catch (error) {
            loginError.textContent = 'An error occurred. Please try again.';
        }
    });

    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('signup-username').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;

        try {
            const response = await fetch('/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            const data = await response.json();
            if (data.success) {
                window.location.href = '/applications';  // redirect to applications
            } else {
                signupError.textContent = data.message || 'Signup failed.';
            }
        } catch (error) {
            signupError.textContent = 'An error occurred. Please try again.';
        }
    });
});

function showTab(tab, event) {
    event.preventDefault();
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const tabs = document.querySelectorAll('.tab');

    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');

    if (tab === 'login') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
    }
}

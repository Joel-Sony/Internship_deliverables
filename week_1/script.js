// Mobile Menu Toggle
const hamburger = document.querySelector(".hamburger");
const navMenu = document.querySelector(".nav-menu");

hamburger.addEventListener("click", () => {
    hamburger.classList.toggle("active");
    navMenu.classList.toggle("active");
});

// Smooth Scroll & Active Link Highlighting
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('section');

window.addEventListener('scroll', () => {
    let current = "";
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= (sectionTop - 150)) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(current)) {
            link.classList.add('active');
        }
    });
});

// Form Validation
const contactForm = document.getElementById('contactForm');
const statusMsg = document.getElementById('formStatus');

contactForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {
        statusMsg.style.color = "#ef4444";
        statusMsg.innerText = "Please enter a valid email address.";
        return;
    }

    // Success Mockup
    statusMsg.style.color = "#10b981";
    statusMsg.innerText = "Message sent successfully!";
    contactForm.reset();
    
    setTimeout(() => { statusMsg.innerText = ""; }, 4000);
});
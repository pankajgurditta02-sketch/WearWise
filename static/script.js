document.addEventListener('DOMContentLoaded', () => {
    // Scroll Reveal Animation
    const reveals = document.querySelectorAll('.reveal');
    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const elementVisible = 100;
        reveals.forEach(reveal => {
            const elementTop = reveal.getBoundingClientRect().top;
            if (elementTop < windowHeight - elementVisible) {
                reveal.classList.add('active');
            }
        });
    };
    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Trigger on load

    // Navbar Scrolled State
    const nav = document.querySelector('nav');
    if (nav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        });
    }

    // Drag and Drop Image Upload
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const imagePreview = document.getElementById('imagePreview');
    const previewContainer = document.getElementById('preview-container');

    if (dropZone && fileInput) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updatePreview(fileInput.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                updatePreview(fileInput.files[0]);
            }
        });
    }

    function updatePreview(file) {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                previewContainer.style.display = 'flex';
                dropZone.querySelector('i').className = 'fas fa-check-circle';
                dropZone.querySelector('p').innerText = 'Image Selected: ' + file.name;
            };
            reader.readAsDataURL(file);
        }
    }

    // AI Loading Screen Interception
    const uploadForm = document.getElementById('uploadForm');
    const loadingScreen = document.getElementById('loadingScreen');
    
    if (uploadForm && loadingScreen) {
        uploadForm.addEventListener('submit', (e) => {
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select or drop an image first.');
                return;
            }
            // Show loading screen before actually submitting
            loadingScreen.style.display = 'flex';
        });
    }

    // Animated Count-Up Stats
    const counters = document.querySelectorAll('.count-up');
    const speed = 200; // lower is faster
    const animateCounters = () => {
        counters.forEach(counter => {
            const updateCount = () => {
                const target = +counter.getAttribute('data-target');
                const count = +counter.innerText;
                const inc = target / speed;
                if (count < target) {
                    counter.innerText = Math.ceil(count + inc);
                    setTimeout(updateCount, 15);
                } else {
                    counter.innerText = target + (counter.getAttribute('data-suffix') || '');
                }
            };
            
            const elementTop = counter.getBoundingClientRect().top;
            if (elementTop < window.innerHeight && counter.innerText == "0") {
                updateCount();
            }
        });
    };
    window.addEventListener('scroll', animateCounters);

    // Chatbot UI Toggle
    const chatbotBubble = document.getElementById('chatbotBubble');
    const chatbotWindow = document.getElementById('chatbotWindow');
    if (chatbotBubble && chatbotWindow) {
        chatbotBubble.addEventListener('click', () => {
            chatbotWindow.style.display = chatbotWindow.style.display === 'flex' ? 'none' : 'flex';
        });
    }

    // Chatbot Logic
    const chatInput = document.getElementById('chatInput');
    const chatBtn = document.getElementById('chatBtn');
    const chatBody = document.getElementById('chatBody');

    if (chatBtn && chatInput) {
        const sendMessage = () => {
            const text = chatInput.value.trim();
            if (!text) return;
            
            // Add user message
            chatBody.innerHTML += `<div class="chat-msg user">${text}</div>`;
            chatInput.value = '';
            chatBody.scrollTop = chatBody.scrollHeight;

            // Add typing indicator bot message
            const typingId = 'typing-' + Date.now();
            chatBody.innerHTML += `
                <div class="chat-msg bot" id="${typingId}">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatBody.scrollTop = chatBody.scrollHeight;

            const startTime = Date.now();

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            })
            .then(res => res.json())
            .then(data => {
                const elapsedTime = Date.now() - startTime;
                const delay = Math.max(0, 1500 - elapsedTime); // Wait at least 1.5 seconds
                
                setTimeout(() => {
                    const typingElement = document.getElementById(typingId);
                    if (typingElement) {
                        typingElement.innerHTML = data.reply;
                    }
                    chatBody.scrollTop = chatBody.scrollHeight;
                }, delay);
            })
            .catch(err => {
                const elapsedTime = Date.now() - startTime;
                const delay = Math.max(0, 1500 - elapsedTime);
                
                setTimeout(() => {
                    const typingElement = document.getElementById(typingId);
                    if (typingElement) {
                        typingElement.innerHTML = "I apologize, but I am experiencing issues connecting to the styling engine. Please try again shortly.";
                    }
                    chatBody.scrollTop = chatBody.scrollHeight;
                }, delay);
            });
        };
        chatBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
});

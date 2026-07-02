
function showSection(id){
    document.querySelectorAll('.page').forEach(page=>{
        page.classList.remove('active');
    });

    document.getElementById(id).classList.add('active');
}
function openCertificate(image) {
    document.getElementById("modalCertificate").src = image;

    document
        .getElementById("certificateModal")
        .classList.add("active");
}

function closeCertificate(){
    document
        .getElementById('certificateModal')
        .classList.remove('active');
}
function togglePractice(element){
    const item = element.parentElement;
    item.classList.toggle('active');
}

/* ГАЛЕРЕЯ */

let galleryImages = [];
let galleryIndex = 0;

function openGallery(img) {
    const gallery = img.parentElement;
    galleryImages = Array.from(gallery.querySelectorAll('img')).map(i => i.src);
    galleryIndex = galleryImages.indexOf(img.src);
    showGalleryImage();
    document.getElementById('galleryModal').classList.add('active');
}

function showGalleryImage() {
    document.getElementById('galleryImage').src = galleryImages[galleryIndex];
}

function galleryNav(dir) {
    galleryIndex = (galleryIndex + dir + galleryImages.length) % galleryImages.length;
    showGalleryImage();
}

function closeGallery() {
    document.getElementById('galleryModal').classList.remove('active');
}

document.addEventListener('keydown', (e) => {
    const modal = document.getElementById('galleryModal');
    if (!modal.classList.contains('active')) return;
    if (e.key === 'Escape') closeGallery();
    if (e.key === 'ArrowLeft') galleryNav(-1);
    if (e.key === 'ArrowRight') galleryNav(1);
});

/* ОЦЕНКА НАВЫКОВ */

document.querySelectorAll('.rating-dots').forEach(container => {
    const rating = parseInt(container.dataset.rating);
    for (let i = 1; i <= 5; i++) {
        const dot = document.createElement('span');
        dot.className = 'dot' + (i <= rating ? ' active' : '');
        container.appendChild(dot);
    }
});

/* СВЕЧЕНИЕ КУРСОРА + СЕКРЕТНАЯ НАДПИСЬ */

const cursorGlow = document.getElementById('cursorGlow');
const steamSecret = document.querySelector('.steam-secret');

document.addEventListener('mousemove', (e) => {
    cursorGlow.style.left = e.clientX + 'px';
    cursorGlow.style.top = e.clientY + 'px';
    cursorGlow.classList.add('active');

    if (steamSecret) {
        const rect = steamSecret.getBoundingClientRect();
        const dist = Math.hypot(
            e.clientX - (rect.left + rect.width / 2),
            e.clientY - (rect.top + rect.height / 2)
        );
        if (dist < 50) {
            steamSecret.classList.add('revealed');
        } else {
            steamSecret.classList.remove('revealed');
        }
    }
});

document.addEventListener('mouseleave', () => {
    cursorGlow.classList.remove('active');
});

/* ===== ИИ-ПОМОЩНИК ===== */

const questionCountSlider = document.getElementById('questionCount');
const questionCountLabel = document.getElementById('questionCountLabel');

if (questionCountSlider) {
    questionCountSlider.addEventListener('input', function() {
        questionCountLabel.textContent = this.value;
    });
}

const fileInput = document.getElementById('fileInput');
const aiTextInput = document.getElementById('aiTextInput');

if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function(event) {
            aiTextInput.value = event.target.result;
            showToast('Файл загружен! Нажмите «Сгенерировать»', '#7c3aed');
        };
        reader.onerror = function() {
            showToast('Ошибка чтения файла', '#e87060');
        };
        reader.readAsText(file, 'UTF-8');
        fileInput.value = '';
    });
}

async function generateQuestions() {
    const text = aiTextInput.value.trim();
    const count = questionCountSlider ? parseInt(questionCountSlider.value) : 3;
    const container = document.getElementById('aiQuestionsContainer');
    const loading = document.getElementById('aiLoading');

    if (!text || text.length < 10) {
        showToast('Введите текст (минимум 10 символов)', '#e87060');
        return;
    }

    loading.style.display = 'block';
    container.innerHTML = '';

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, count: count })
        });
        const data = await response.json();
        if (data.error) {
            showToast('Ошибка: ' + data.error, '#e87060');
            return;
        }
        displayQuestions(data.questions || [], count);
    } catch (error) {
        console.error(error);
        showToast('Ошибка соединения с сервером. Запустите Flask.', '#e87060');
    } finally {
        loading.style.display = 'none';
    }
}

function displayQuestions(questions, expectedCount) {
    const container = document.getElementById('aiQuestionsContainer');
    container.innerHTML = '';

    if (!questions || questions.length === 0) {
        container.innerHTML = '<div class="ai-empty"><i class="fas fa-info-circle"></i> Не удалось сгенерировать вопросы. Попробуйте другой текст.</div>';
        return;
    }

    const levelColors = { 'Легкий': '#48bb78', 'Средний': '#ed8936', 'Сложный': '#fc8181' };
    const displayCount = Math.min(questions.length, expectedCount || questions.length);

    for (let i = 0; i < displayCount; i++) {
        const q = questions[i];
        const color = levelColors[q.level] || '#7c3aed';
        const card = document.createElement('div');
        card.className = 'ai-question-card';
        card.style.borderLeftColor = color;
        card.style.animationDelay = (i * 0.1) + 's';
        card.innerHTML = `
            <div class="ai-question-level" style="color:${color};">${q.level || 'Вопрос'}</div>
            <div class="ai-question-text">${q.question || 'Вопрос не сгенерирован'}</div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <span class="ai-answer-toggle" onclick="toggleAiAnswer(this)"><i class="fas fa-chevron-right"></i> Показать ответ для учителя</span>
                <span class="ai-q-number">#${i + 1}</span>
            </div>
            <div class="ai-teacher-answer">${q.teacher_answer || 'Ответ не указан'}</div>
        `;
        container.appendChild(card);
    }
}

window.toggleAiAnswer = function(element) {
    const wrapper = element.closest('div');
    const answer = wrapper.nextElementSibling;
    if (answer.classList.contains('visible')) {
        answer.classList.remove('visible');
        element.innerHTML = '<i class="fas fa-chevron-right"></i> Показать ответ для учителя';
    } else {
        answer.classList.add('visible');
        element.innerHTML = '<i class="fas fa-chevron-down"></i> Скрыть ответ';
    }
};

function showToast(message, color) {
    const toastEl = document.getElementById('toastMessage');
    toastEl.textContent = message;
    toastEl.style.background = color || '#7c3aed';
    toastEl.classList.add('show');
    setTimeout(() => toastEl.classList.remove('show'), 3000);
}

const aiDemoBtn = document.getElementById('aiDemoBtn');
if (aiDemoBtn) {
    aiDemoBtn.addEventListener('click', function() {
        const demoText = `Фотосинтез — это процесс преобразования световой энергии в химическую энергию органических веществ. Он происходит в хлоропластах растительных клеток. Основные этапы: световая и темновая фазы. В световой фазе происходит фотолиз воды и синтез АТФ. В темновой фазе углекислый газ связывается и образуется глюкоза. Ключевой фермент — рибулозобисфосфат-карбоксилаза (Рубиско).`;
        aiTextInput.value = demoText;
        if (questionCountSlider) {
            questionCountSlider.value = 5;
            questionCountLabel.textContent = '5';
        }
        generateQuestions();
    });
}

const aiGenerateBtn = document.getElementById('aiGenerateBtn');
if (aiGenerateBtn) {
    aiGenerateBtn.addEventListener('click', generateQuestions);
}

if (aiTextInput) {
    aiTextInput.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            generateQuestions();
        }
    });
}
let audioBlob = null;
let isEnglish = window.location.pathname.includes('/english');

document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.tts-container')) {
        setupEventListeners();
    }
});

function setupEventListeners() {
    document.getElementById('startBtn').addEventListener('click', startConversion);
    document.getElementById('saveBtn').addEventListener('click', saveAudio);
    
    const uploadBtn = document.getElementById('imageUploadBtn');
    const imageInput = document.getElementById('imageInput');
    uploadBtn.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', handleImageUpload);
}

async function startConversion() {
    const textInput = document.getElementById('textInput');
    const text = textInput.value.trim();
    
    if (!text) {
        updateStatus('⚠️ لطفا متن را وارد کنید', 'error');
        return;
    }
    
    const gender = document.getElementById('gender').value;
    const rate = document.getElementById('rate').value;
    
    document.getElementById('startBtn').disabled = true;
    document.getElementById('saveBtn').disabled = true;
    updateStatus('⏳ در حال تبدیل متن به صدا...', 'info');
    
    const progressSection = document.querySelector('.progress-section');
    progressSection.style.display = 'flex';
    updateProgress(0);
    
    try {
        const response = await fetch('/generate-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                language: isEnglish ? 'english' : 'persian',
                voice: gender,
                rate: rate
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'خطا در ارتباط با سرور');
        }
        
        audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const audio = document.getElementById('audioPlayer');
        audio.src = audioUrl;
        await audio.play();
        
        updateProgress(100);
        updateStatus('✅ تبدیل با موفقیت انجام شد', 'success');
        document.getElementById('saveBtn').disabled = false;
        
    } catch (error) {
        console.error('Error:', error);
        updateStatus('❌ خطا: ' + error.message, 'error');
    } finally {
        document.getElementById('startBtn').disabled = false;
        setTimeout(() => {
            document.querySelector('.progress-section').style.display = 'none';
        }, 3000);
    }
}

function updateProgress(value) {
    document.getElementById('progressBar').value = value;
    document.getElementById('progressText').textContent = value + '%';
}

function updateStatus(message, type = 'info') {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = 'status ' + type;
}

function saveAudio() {
    if (!audioBlob) {
        updateStatus('⚠️ فایل صوتی برای ذخیره وجود ندارد', 'error');
        return;
    }
    
    const url = URL.createObjectURL(audioBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `voice_output_${Date.now()}.mp3`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    updateStatus('✅ فایل صوتی با موفقیت ذخیره شد', 'success');
}

async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    updateStatus('📷 در حال پردازش تصویر...', 'info');
    
    try {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        
        reader.onload = async function() {
            const response = await fetch('/extract-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: reader.result })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'خطا در پردازش تصویر');
            }
            
            const data = await response.json();
            
            if (data.text) {
                document.getElementById('textInput').value = data.text;
                updateStatus('✅ متن با موفقیت استخراج شد', 'success');
            } else {
                updateStatus('⚠️ متنی در تصویر یافت نشد', 'error');
            }
        };
        
    } catch (error) {
        console.error('Error:', error);
        updateStatus('❌ خطا: ' + error.message, 'error');
    }
    
    event.target.value = '';
}

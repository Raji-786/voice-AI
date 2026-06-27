from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import pytesseract
from PIL import Image
import base64
import io
from google.cloud import texttospeech
import time

app = Flask(__name__)

# CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# مسیر Tesseract
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ============================================
# راه‌اندازی Google TTS
# ============================================
# کلید API خودت رو اینجا بذار
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your-service-account-file.json'

def text_to_speech_google(text, language):
    client = texttospeech.TextToSpeechClient()
    
    # تنظیمات ورودی
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # تنظیمات صدا
    if language == 'persian':
        voice = texttospeech.VoiceSelectionParams(
            language_code='fa-IR',
            name='fa-IR-Standard-A',  # صدای فارسی
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code='en-US',
            name='en-US-Neural2-J',  # صدای انگلیسی (Neural)
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
    
    # تنظیمات خروجی
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0.0
    )
    
    # درخواست
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    return response.audio_content

# ============================================
# صفحات
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/persian')
def persian_page():
    return render_template('persian.html')

@app.route('/english')
def english_page():
    return render_template('english.html')

# ============================================
# تبدیل متن به صدا
# ============================================
@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'persian')
        
        if not text:
            return jsonify({'error': 'لطفا متن را وارد کنید'}), 400
        
        # تبدیل با Google TTS
        audio_content = text_to_speech_google(text, language)
        
        # فایل موقت
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, 'wb') as f:
            f.write(audio_content)
        
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='speech_output.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# استخراج متن از تصویر
# ============================================
@app.route('/extract-text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'error': 'تصویر ارسال نشده است'}), 400
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        text = pytesseract.image_to_string(image, lang='eng+fas').strip()
        
        if not text:
            return jsonify({'error': 'متنی در تصویر یافت نشد'}), 404
        
        return jsonify({'text': text})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# دانلود
# ============================================
@app.route('/download', methods=['POST'])
def download_audio():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'persian')
        
        if not text:
            return jsonify({'error': 'متن وارد نشده است'}), 400
        
        audio_content = text_to_speech_google(text, language)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, 'wb') as f:
            f.write(audio_content)
        
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='voice_output.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# اجرا
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

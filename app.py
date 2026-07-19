from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS
import os
import tempfile
import pytesseract
from PIL import Image
import base64
import io
import time

app = Flask(__name__)

# CORS دستی
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# مسیر Tesseract
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# تنظیمات زبان‌ها برای gTTS
# gTTS از کدهای زبان استاندارد استفاده می‌کند
LANGUAGE_CODES = {
    'persian': 'fa',  # فارسی
    'english': 'en'   # انگلیسی
}

# gTTS سرعت (تنظیم سرعت در gTTS محدودتر است)
# gTTS از پارامتر slow=True/False برای سرعت آهسته/عادی استفاده می‌کند
# برای تغییر سرعت بیشتر باید از کتابخانه‌های دیگر یا پردازش بعدی استفاده کرد

def text_to_speech(text, language, slow=False):
    """
    تبدیل متن به گفتار با استفاده از gTTS
    
    Args:
        text: متن ورودی
        language: کد زبان ('fa' یا 'en')
        slow: سرعت آهسته (True) یا عادی (False)
    
    Returns:
        مسیر فایل موقت MP3
    """
    try:
        # ایجاد فایل موقت
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        # ایجاد شیء gTTS
        tts = gTTS(text=text, lang=language, slow=slow)
        
        # ذخیره فایل
        tts.save(temp_path)
        
        return temp_path
        
    except Exception as e:
        raise Exception(f"خطا در تبدیل متن به گفتار: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/persian')
def persian_page():
    return render_template('persian.html')

@app.route('/english')
def english_page():
    return render_template('english.html')

@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'persian')
        voice_type = data.get('voice', 'male')  # gTTS از جنسیت پشتیبانی نمی‌کند
        rate = data.get('rate', '+0%')  # gTTS از تنظیم سرعت دقیق پشتیبانی نمی‌کند
        
        if not text:
            return jsonify({'error': 'لطفا متن را وارد کنید'}), 400
        
        # تبدیل کد زبان
        lang_code = LANGUAGE_CODES.get(language, 'fa')
        
        # تنظیم سرعت آهسته اگر rate منفی باشد
        slow = False
        if rate and rate.startswith('-'):
            slow = True
        
        # تبدیل متن به گفتار
        temp_path = text_to_speech(text, lang_code, slow)
        
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='speech_output.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/download', methods=['POST'])
def download_audio():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'persian')
        voice_type = data.get('voice', 'male')  # gTTS از جنسیت پشتیبانی نمی‌کند
        
        if not text:
            return jsonify({'error': 'متن وارد نشده است'}), 400
        
        # تبدیل کد زبان
        lang_code = LANGUAGE_CODES.get(language, 'fa')
        
        # تبدیل متن به گفتار
        temp_path = text_to_speech(text, lang_code)
        
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='voice_output.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

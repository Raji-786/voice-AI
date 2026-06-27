from flask import Flask, render_template, request, jsonify, send_file
import edge_tts
import os
import asyncio
import tempfile
import pytesseract
from PIL import Image
import base64
import io
import time
from gtts import gTTS  # اضافه شده برای انگلیسی

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

# صداها
VOICES = {
    'persian': {
        'male': 'fa-IR-FaridNeural',
        'female': 'fa-IR-DilaraNeural'
    },
    'english': {
        'male': 'en-US-GuyNeural',
        'female': 'en-US-JennyNeural'
    }
}

# تابع تبدیل با تلاش مجدد برای edge-tts
async def text_to_speech_edge(text, voice, rate, retries=3):
    for attempt in range(retries):
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_path = temp_file.name
            temp_file.close()
            
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
            await communicate.save(temp_path)
            
            return temp_path
            
        except Exception as e:
            if attempt < retries - 1:
                print(f"تلاش {attempt+1} ناموفق بود، دوباره تلاش می‌شود...")
                await asyncio.sleep(2)
                continue
            else:
                raise e

# تابع تبدیل با gTTS برای انگلیسی
def text_to_speech_gtts(text):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_path = temp_file.name
    temp_file.close()
    
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(temp_path)
    
    return temp_path

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
        voice_type = data.get('voice', 'male')
        rate = data.get('rate', '+0%')
        
        if not text:
            return jsonify({'error': 'لطفا متن را وارد کنید'}), 400
        
        # اگر زبان فارسی است از edge-tts استفاده کن
        if language == 'persian':
            try:
                voice = VOICES['persian'][voice_type]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                temp_path = loop.run_until_complete(text_to_speech_edge(text, voice, rate))
                loop.close()
            except Exception as e:
                # اگر خطای 403 داد، پیام مناسب برگردان
                if '403' in str(e) or 'Invalid response' in str(e):
                    return jsonify({
                        'error': '⚠️ سرویس تبدیل صدای فارسی به دلیل تحریم در دسترس نیست. لطفاً از VPN استفاده کنید یا زبان انگلیسی را انتخاب کنید.'
                    }), 403
                else:
                    raise e
        else:
            # انگلیسی - از gTTS استفاده کن (بدون تحریم)
            temp_path = text_to_speech_gtts(text)
        
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
        voice_type = data.get('voice', 'male')
        
        if not text:
            return jsonify({'error': 'متن وارد نشده است'}), 400
        
        # اگر زبان فارسی است از edge-tts استفاده کن
        if language == 'persian':
            try:
                voice = VOICES['persian'][voice_type]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                temp_path = loop.run_until_complete(text_to_speech_edge(text, voice, '+0%'))
                loop.close()
            except Exception as e:
                if '403' in str(e) or 'Invalid response' in str(e):
                    return jsonify({
                        'error': '⚠️ سرویس فارسی در دسترس نیست. لطفاً از VPN استفاده کنید.'
                    }), 403
                else:
                    raise e
        else:
            # انگلیسی - از gTTS استفاده کن
            temp_path = text_to_speech_gtts(text)
        
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

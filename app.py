from flask import Flask, send_from_directory, request, send_file, jsonify, Response
from flask_cors import CORS
import os
import uuid
import traceback
import requests
from werkzeug.utils import secure_filename
from faster_whisper import WhisperModel
import ffmpeg
import threading
import time
import glob
import shutil

UPLOAD_FOLDER = '/tmp/uploads'
TRANSCRIPT_FOLDER = '/tmp/transcripts'
ALLOWED_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'webm'}
MAX_FILE_SIZE_MB = 200
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Carrega o modelo Whisper (pode ser 'base', 'small', 'medium', 'large-v2', etc)
whisper_model = WhisperModel('base', device="cpu", compute_type="int8")

# Estado das transcrições
transcription_status = {}

# Limpeza periódica de arquivos temporários
CLEANUP_INTERVAL = 60 * 60  # 1 hora
CLEANUP_AGE = 60 * 60 * 6  # 6 horas

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_temp_files():
    now = time.time()
    for folder in [UPLOAD_FOLDER, TRANSCRIPT_FOLDER]:
        for f in glob.glob(os.path.join(folder, '*')):
            if os.path.isfile(f) and now - os.path.getmtime(f) > CLEANUP_AGE:
                try:
                    os.remove(f)
                except Exception:
                    pass
cleanup_thread = threading.Thread(target=lambda: (time.sleep(CLEANUP_INTERVAL), cleanup_temp_files()), daemon=True)
cleanup_thread.start()

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    try:
        transcript_id = str(uuid.uuid4())
        video_path = None
        # Upload
        if 'file' in request.files:
            file = request.files['file']
            filename = secure_filename(file.filename)
            if not allowed_file(filename):
                return jsonify({'error': 'Formato de vídeo não suportado.'}), 400
            file.seek(0, os.SEEK_END)
            size_mb = file.tell() / (1024 * 1024)
            file.seek(0)
            if size_mb > MAX_FILE_SIZE_MB:
                return jsonify({'error': f'Arquivo muito grande (>{MAX_FILE_SIZE_MB}MB).'}), 400
            video_path = os.path.join(UPLOAD_FOLDER, f"{transcript_id}_{filename}")
            file.save(video_path)
        else:
            data = request.get_json()
            url = data.get('url')
            if not url:
                return jsonify({'error': 'URL do vídeo é obrigatória.'}), 400
            filename = f"{transcript_id}.mp4"
            video_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                r = requests.get(url, stream=True, timeout=30)
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            except Exception:
                return jsonify({'error': 'Falha ao baixar o vídeo do link.'}), 400
        # Inicia transcrição em thread
        transcription_status[transcript_id] = {'status': 'processing', 'progress': 0, 'error': None}
        threading.Thread(target=run_transcription, args=(video_path, transcript_id), daemon=True).start()
        return jsonify({'transcript_id': transcript_id})
    except Exception as e:
        print('Erro na transcrição:', str(e))
        print(traceback.format_exc())
        return jsonify({'error': f'Erro na transcrição: {str(e)}'}), 500

def run_transcription(video_path, transcript_id):
    try:
        audio_path = video_path + '.wav'
        (
            ffmpeg.input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(quiet=True)
        )
        segments, info = whisper_model.transcribe(audio_path, beam_size=5, language='pt')
        srt_lines = []
        for i, segment in enumerate(segments):
            start = segment.start
            end = segment.end
            text = segment.text.strip()
            srt_lines.append(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{text}\n")
            if i % 5 == 0:
                transcription_status[transcript_id]['progress'] = int(100 * (i+1) / info["num_segments"])
        srt_content = '\n'.join(srt_lines)
        srt_path = os.path.join(TRANSCRIPT_FOLDER, f'{transcript_id}.srt')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        transcription_status[transcript_id]['status'] = 'done'
        transcription_status[transcript_id]['progress'] = 100
        os.remove(video_path)
        os.remove(audio_path)
    except Exception as e:
        transcription_status[transcript_id]['status'] = 'error'
        transcription_status[transcript_id]['error'] = str(e)
        print('Erro na transcrição:', str(e))
        print(traceback.format_exc())
        try:
            if os.path.exists(video_path): os.remove(video_path)
            if os.path.exists(audio_path): os.remove(audio_path)
        except Exception:
            pass

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

@app.route('/api/transcribe/status/<transcript_id>')
def transcribe_status(transcript_id):
    status = transcription_status.get(transcript_id)
    if not status:
        return jsonify({'error': 'Transcrição não encontrada.'}), 404
    return jsonify(status)

@app.route('/api/subtitle/<transcript_id>', methods=['GET', 'POST'])
def subtitle(transcript_id):
    srt_path = os.path.join(TRANSCRIPT_FOLDER, f'{transcript_id}.srt')
    if request.method == 'GET':
        if not os.path.exists(srt_path):
            return jsonify({'error': 'Legenda não encontrada.'}), 404
        with open(srt_path, 'r', encoding='utf-8') as f:
            return jsonify({'srt': f.read()})
    elif request.method == 'POST':
        data = request.get_json()
        srt = data.get('srt')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt)
        return jsonify({'success': True})

@app.route('/api/subtitle/<transcript_id>/download', methods=['GET'])
def download_subtitle(transcript_id):
    srt_path = os.path.join(TRANSCRIPT_FOLDER, f'{transcript_id}.srt')
    if not os.path.exists(srt_path):
        return jsonify({'error': 'Legenda não encontrada.'}), 404
    return send_file(srt_path, as_attachment=True, download_name=f'{transcript_id}.srt')

@app.route('/api/subtitle/<transcript_id>/download-txt', methods=['GET'])
def download_subtitle_txt(transcript_id):
    srt_path = os.path.join(TRANSCRIPT_FOLDER, f'{transcript_id}.srt')
    if not os.path.exists(srt_path):
        return jsonify({'error': 'Legenda não encontrada.'}), 404
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt = f.read()
    # Extrai apenas o texto
    lines = [line for line in srt.splitlines() if not line.strip().isdigit() and '-->' not in line and line.strip()]
    txt = '\n'.join(lines)
    return Response(txt, mimetype='text/plain', headers={'Content-Disposition': f'attachment;filename={transcript_id}.txt'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
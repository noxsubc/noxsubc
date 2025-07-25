from flask import Flask, send_from_directory, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import os
import uuid
import traceback

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/message')
def get_message():
    return {"message": "Hello from Python Backend!"}

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            return jsonify({'error': f'No suitable video stream found for {yt.title}.'}), 404
        filename = f"{uuid.uuid4()}.mp4"
        filepath = os.path.join('/tmp', filename)
        stream.download(output_path='/tmp', filename=filename)
        response = send_file(filepath, as_attachment=True, download_name=f"{yt.title}.mp4")
        os.remove(filepath)
        return response
    except Exception as e:
        print('Erro ao baixar vídeo:', str(e))
        print(traceback.format_exc())
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
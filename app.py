from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/message')
def get_message():
    return {"message": "Hello from Python Backend!"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
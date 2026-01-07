from flask import Flask, request, jsonify, send_from_directory
import os
from utils import with_user_info

app = Flask(__name__, static_folder='vue-project/dist', static_url_path='')

@app.route("/api/")
@with_user_info
def hello_world(user_name, org_name, org_id):
    return {
        "username": user_name,
        "org_name": org_name,
        "org_id": org_id
    }

# serve Vue static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue(path):
    print(path)
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
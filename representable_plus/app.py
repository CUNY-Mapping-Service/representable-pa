from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='vue-project/dist', static_url_path='')

@app.route("/api/")
def hello_world():
    username = request.headers.get('X-Authenticated-User', 'Guest')
    email = request.headers.get('X-User-Email', '')
    user_id = request.headers.get('X-User-ID', '')
    return f"<p>Hello, {username}!. Your email is {email}, and id is {user_id}</p>"

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
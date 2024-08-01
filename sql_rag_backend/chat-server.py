from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_agent.support_agent import getResponseFromAgent


app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    message = data['message']
    response = getResponseFromAgent(message)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=False, port=5001)

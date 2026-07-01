import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Provenance Guard API is running.",
        "endpoints": ["/submit"]
    })


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()
    creator_id = data.get("creator_id", "").strip()

    if not text or not creator_id:
        return jsonify({
            "error": "Both 'text' and 'creator_id' are required."
        }), 400

    content_id = str(uuid.uuid4())

    return jsonify({
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": "uncertain",
        "confidence": 0.5,
        "label": "The system could not confidently determine whether this content was human-written or AI-generated.",
        "status": "classified"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
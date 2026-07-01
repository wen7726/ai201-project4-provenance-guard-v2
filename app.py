import json
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from detector import (
    llm_detection_score,
    stylometric_score,
    combine_scores,
    attribution_from_score,
    transparency_label,
)

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

LOG_FILE = "audit_log.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_log():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_log(entries):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_log_entry(entry):
    entries = read_log()
    entries.append(entry)
    write_log(entries)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Provenance Guard API is running.",
        "endpoints": ["/submit", "/appeal", "/log"]
    })


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()
    creator_id = data.get("creator_id", "").strip()

    if not text or not creator_id:
        return jsonify({
            "error": "Both 'text' and 'creator_id' are required."
        }), 400

    content_id = str(uuid.uuid4())

    llm_result = llm_detection_score(text)
    style_result = stylometric_score(text)

    llm_score = llm_result["score"]
    style_score = style_result["score"]

    confidence = combine_scores(llm_score, style_score)
    attribution = attribution_from_score(confidence)
    label = transparency_label(attribution)

    log_entry = {
        "event_type": "submission",
        "timestamp": now_iso(),
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "llm_reason": llm_result.get("reason"),
        "stylometric_score": style_score,
        "stylometric_metrics": style_result.get("metrics"),
        "status": "classified",
        "appeal_filed": False
    }

    add_log_entry(log_entry)

    return jsonify({
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "signals": {
            "llm_score": llm_score,
            "llm_reason": llm_result.get("reason"),
            "stylometric_score": style_score,
            "stylometric_metrics": style_result.get("metrics"),
        },
        "label": label,
        "status": "classified"
    })


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(silent=True) or {}

    content_id = data.get("content_id", "").strip()
    creator_reasoning = data.get("creator_reasoning", "").strip()

    if not content_id or not creator_reasoning:
        return jsonify({
            "error": "Both 'content_id' and 'creator_reasoning' are required."
        }), 400

    entries = read_log()

    found_submission = False

    for entry in entries:
        if entry.get("content_id") == content_id:
            found_submission = True
            entry["status"] = "under_review"
            entry["appeal_filed"] = True
            entry["appeal_reasoning"] = creator_reasoning

    if not found_submission:
        return jsonify({
            "error": "No original submission found for this content_id."
        }), 404

    appeal_entry = {
        "event_type": "appeal",
        "timestamp": now_iso(),
        "content_id": content_id,
        "creator_reasoning": creator_reasoning,
        "status": "under_review"
    }

    entries.append(appeal_entry)
    write_log(entries)

    return jsonify({
        "message": "Appeal received.",
        "content_id": content_id,
        "status": "under_review",
        "creator_reasoning": creator_reasoning
    })


@app.route("/log", methods=["GET"])
def get_log():
    entries = read_log()
    return jsonify({
        "entries": entries[-20:]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
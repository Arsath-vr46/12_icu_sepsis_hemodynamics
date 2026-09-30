import os
import json
from flask import Flask, request, jsonify, render_template

from chatbot_config import SYSTEM_PROMPT, BOT_TITLE, MODEL_NAME

from google import genai
from google.genai import types

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")

with open(KB_PATH, "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

_client = None


def get_client():
    """Lazily create the GenAI client so import/startup never fails
    even if the API key is not yet configured."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


def build_kb_context():
    terms = KNOWLEDGE_BASE.get("glossary", [])
    if not terms:
        return ""
    lines = ["Reference glossary you may draw on when relevant:"]
    for item in terms:
        lines.append(f"- {item['term']}: {item['definition']}")
    return "\n".join(lines)


def to_genai_contents(history, message):
    """Convert a simple [{role, text}] history plus the new message into
    google-genai Content objects."""
    contents = []
    for turn in history or []:
        role = "model" if turn.get("role") == "assistant" else "user"
        text = turn.get("text", "") or turn.get("content", "")
        if not text:
            continue
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=text)])
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    return contents


@app.route("/")
def index():
    return render_template("index.html", bot_title=BOT_TITLE)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"reply": "Please enter a message."}), 400

    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify(
            {
                "reply": (
                    "Server is missing GEMINI_API_KEY. Set the GEMINI_API_KEY "
                    "environment variable and restart the service."
                )
            }
        ), 500

    try:
        client = get_client()
        kb_context = build_kb_context()
        full_system_prompt = SYSTEM_PROMPT
        if kb_context:
            full_system_prompt = f"{SYSTEM_PROMPT}\n\n{kb_context}"

        contents = to_genai_contents(history, message)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
            ),
        )

        reply_text = getattr(response, "text", None) or "I could not generate a response."
        return jsonify({"reply": reply_text})

    except Exception as exc:  # noqa: BLE001
        return jsonify({"reply": f"An error occurred while contacting the model: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

# DeltaForge AI

Black-Scholes-Merton, Volatility Surfaces & Exotics

## Run locally
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_api_key_here
python app.py
```

Then open http://localhost:5000

## Deploy (Render / Railway / VPS)
1. Push this folder to its own Git repo (or a subfolder Render/Railway can target).
2. Set the `GEMINI_API_KEY` environment variable in your host's dashboard.
3. Start command: `gunicorn app:app`
4. Build command (if needed): `pip install -r requirements.txt`

No external database is required — `knowledge_base.json` is loaded in-memory at startup.

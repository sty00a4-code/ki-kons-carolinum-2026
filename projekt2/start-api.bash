cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli migrate
uvicorn app.main:app --reload --port 8000
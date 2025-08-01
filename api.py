# backend/api.py
from fastapi import FastAPI
import json, os

app = FastAPI()
BASE = os.path.dirname(__file__)

@app.get("/api/scores")
def get_scores():
    path = os.path.join(BASE, "scores.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

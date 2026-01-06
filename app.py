from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

@app.route("/")
def home():
    return "Backend ApuestasX5 OK"

@app.route("/fixtures/today")
def fixtures_today():
    r = requests.get(
        f"{BASE_URL}/fixtures?date=2026-01-06",
        headers=HEADERS,
        timeout=10
    )
    return jsonify(r.json())

@app.route("/status")
def status():
    return jsonify({"status": "ok"})


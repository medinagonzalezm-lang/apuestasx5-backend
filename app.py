from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/matches")
def matches():
    return [
        {
            "home": "Real Madrid",
            "away": "Barcelona",
            "odds": 1.85
        },
        {
            "home": "Atletico Madrid",
            "away": "Sevilla",
            "odds": 2.10
        }
    ]

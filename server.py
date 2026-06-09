from fastapi import FastAPI
import requests

app = FastAPI()

BASE_URL = "https://gamma-api.polymarket.com"

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/markets")
def markets():

    response = requests.get(
        f"{BASE_URL}/markets"
    )

    return response.json()[:10]
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

@app.get("/search/{keyword}")
def search_market(keyword: str):

    markets = requests.get(
        f"{BASE_URL}/markets"
    ).json()

    results = []

    for m in markets:

        question = m.get("question", "")

        if keyword.lower() in question.lower():

            results.append({
                "question": question,
                "slug": m.get("slug")
            })

    return results[:20]
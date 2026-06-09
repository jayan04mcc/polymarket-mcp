from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="Polymarket Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://gamma-api.polymarket.com"


@app.get("/")
def home():
    return {"status": "ok", "description": "Polymarket Analysis API"}


@app.get("/markets")
def markets(limit: int = 10, active: bool = True):
    """Retorna los mercados más recientes"""
    params = {"active": active, "limit": limit}
    response = requests.get(f"{BASE_URL}/markets", params=params)
    data = response.json()
    return data[:limit]


@app.get("/search/{keyword}")
def search_market(keyword: str, limit: int = 10):
    """Busca mercados por palabra clave"""
    markets = requests.get(f"{BASE_URL}/markets", params={"limit": 200}).json()
    results = []
    for m in markets:
        question = m.get("question", "")
        if keyword.lower() in question.lower():
            results.append({
                "question": question,
                "slug": m.get("slug"),
                "volume": m.get("volume"),
                "liquidity": m.get("liquidity"),
                "active": m.get("active"),
                "end_date": m.get("endDate"),
                "outcomes": parse_outcomes(m),
            })
    return results[:limit]


@app.get("/market/{slug}")
def market_detail(slug: str):
    """Retorna detalles completos de un mercado específico"""
    markets = requests.get(f"{BASE_URL}/markets", params={"limit": 500}).json()
    for m in markets:
        if m.get("slug") == slug:
            return {
                "question": m.get("question"),
                "slug": slug,
                "description": m.get("description", ""),
                "volume": m.get("volume"),
                "liquidity": m.get("liquidity"),
                "active": m.get("active"),
                "closed": m.get("closed"),
                "end_date": m.get("endDate"),
                "outcomes": parse_outcomes(m),
                "category": m.get("category", ""),
                "tags": m.get("tags", []),
            }
    return {"error": "Market not found"}


@app.get("/top")
def top_markets(
    by: str = Query("volume", description="Ordenar por: volume, liquidity"),
    limit: int = 10
):
    """Retorna los mercados con mayor volumen o liquidez"""
    markets = requests.get(f"{BASE_URL}/markets", params={"limit": 200}).json()
    
    def sort_key(m):
        val = m.get(by, 0)
        try:
            return float(val) if val else 0
        except (ValueError, TypeError):
            return 0

    sorted_markets = sorted(markets, key=sort_key, reverse=True)
    
    return [
        {
            "question": m.get("question"),
            "slug": m.get("slug"),
            "volume": m.get("volume"),
            "liquidity": m.get("liquidity"),
            "outcomes": parse_outcomes(m),
            "end_date": m.get("endDate"),
        }
        for m in sorted_markets[:limit]
    ]


@app.get("/categories")
def list_categories():
    """Lista todas las categorías disponibles en Polymarket"""
    markets = requests.get(f"{BASE_URL}/markets", params={"limit": 300}).json()
    categories = {}
    for m in markets:
        cat = m.get("category") or "Uncategorized"
        categories[cat] = categories.get(cat, 0) + 1
    return sorted(
        [{"category": k, "count": v} for k, v in categories.items()],
        key=lambda x: x["count"],
        reverse=True
    )


@app.get("/summary")
def market_summary():
    """Resumen general del estado del mercado"""
    markets = requests.get(f"{BASE_URL}/markets", params={"limit": 300}).json()
    
    active = [m for m in markets if m.get("active")]
    total_volume = sum(
        float(m.get("volume", 0) or 0) for m in active
    )
    total_liquidity = sum(
        float(m.get("liquidity", 0) or 0) for m in active
    )
    
    return {
        "total_markets": len(markets),
        "active_markets": len(active),
        "total_volume_usd": round(total_volume, 2),
        "total_liquidity_usd": round(total_liquidity, 2),
        "top_by_volume": sorted(
            [{"q": m.get("question"), "v": float(m.get("volume", 0) or 0)} for m in active],
            key=lambda x: x["v"], reverse=True
        )[:5],
    }


def parse_outcomes(market: dict) -> list:
    """Extrae los outcomes (YES/NO y sus precios) de un mercado"""
    outcomes = []
    raw_outcomes = market.get("outcomes", "[]")
    raw_prices = market.get("outcomePrices", "[]")
    
    try:
        if isinstance(raw_outcomes, str):
            import json
            raw_outcomes = json.loads(raw_outcomes)
        if isinstance(raw_prices, str):
            import json
            raw_prices = json.loads(raw_prices)
        
        for i, outcome in enumerate(raw_outcomes):
            price = raw_prices[i] if i < len(raw_prices) else None
            outcomes.append({
                "outcome": outcome,
                "price": float(price) if price else None,
                "implied_probability": f"{round(float(price) * 100, 1)}%" if price else None,
            })
    except Exception:
        pass
    
    return outcomes

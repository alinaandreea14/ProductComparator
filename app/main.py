"""
Product Comparison Engine cu Instructor + OpenAI client pentru Ollama.
Garantează output structurat validat Pydantic prin Instructor.
"""

import os
from dotenv import load_dotenv
from diskcache import Cache
from fastapi import FastAPI
from models.pydantic_models import ComparisonResult, ComparisonRequest
from services.scraper import scrape_product, parse_text_input
from services.llm_service import compara_produse_instructor, comparison_with_cot_retry, client, MODEL

load_dotenv()
# =============================================================================
# CONFIGURARE
# =============================================================================
cache = Cache(directory=os.getenv("CACHE_DIR", "./cache"))

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Product Comparison cu Instructor",
    description="""
    Comparare produs cu garantie Pydantic via Instructor.
    
    **Flow:**
    1. Extrage date (scraping sau text)
    2. Instructor + OpenAI client forțează output validat
    3. Returnează JSON garantat valid conform ComparisonResult
    
    **De ce Instructor?**
    - Garantează schema Pydantic sau reîncearcă automat
    - Nu mai e nevoie de parsing manual JSON
    - Tipuri Python native în tot codul
    """,
    version="3.0.0"
)


@app.post("/compare", response_model=ComparisonResult)
async def compare(request: ComparisonRequest):
    """
    Compară două produse cu Instructor garantat.
    
    **Exemple:**
    
    Cu URL:
    ```json
    {
        "produs_a": {"sursa": "https://example.com/laptop-a", "este_url": true},
        "produs_b": {"sursa": "https://example.com/laptop-b", "este_url": true},
        "preferinte": "Programare, 16GB RAM minim, tastatură bună, sub 2kg"
    }
    ```
    
    Cu text:
    ```json
    {
        "produs_a": {"sursa": "MacBook Air M3 8GB 256GB 1.24kg", "este_url": false},
        "produs_b": {"sursa": "ThinkPad X1 i7 16GB 512GB 1.13kg", "este_url": false},
        "preferinte": "Dezvoltare software și transport zilnic"
    }
    ```
    """
    import time
    start = time.time()
    
    # Cache key
    #cache_key = f"inv:{hashlib.sha256(request.model_dump_json().encode()).hexdigest()}"
    #cached = cache.get(cache_key)
    #if cached:
        # Reconstruim din cache
    #    return ComparisonResult.model_validate(cached)
    
    # Extrage date produse
    if request.produs_a.este_url:
        date_a = await scrape_product(request.produs_a.sursa)
    else:
        date_a = parse_text_input(request.produs_a.sursa)
        
    if request.produs_b.este_url:
        date_b = await scrape_product(request.produs_b.sursa)
    else:
        date_b = parse_text_input(request.produs_b.sursa)
    
    # INSTRUCTOR: Garantat returnează ComparisonResult validat
    result = await compara_produse_instructor(date_a, date_b, request.preferinte)
    
    # Adăugăm metadate
    result_dict = result.model_dump()
    result_dict["_timp_ms"] = int((time.time() - start) * 1000)
    result_dict["_din_cache"] = False
    
    # Salvăm în cache
    #cache.set(cache_key, result_dict, expire=3600*24)
    
    return result


@app.post("/compare/cot", response_model=dict)
async def compare_cot(request: ComparisonRequest):
    if request.produs_a.este_url:
        date_a = await scrape_product(request.produs_a.sursa)
    else:
        date_a = parse_text_input(request.produs_a.sursa)
        
    if request.produs_b.este_url:
        date_b = await scrape_product(request.produs_b.sursa)
    else:
        date_b = parse_text_input(request.produs_b.sursa)

    final_data = await comparison_with_cot_retry(date_a, date_b, request.preferinte)

    return final_data


@app.get("/health")
async def health():
    """Verificare stare."""
    try:
        # Test rapid Ollama
        client.models.list()
        ollama_ok = True
    except:
        ollama_ok = False
    
    return {
        "status": "ok" if ollama_ok else "degraded",
        "instructor": "active",
        "model": MODEL,
        "mode": "instructor-json"
    }


@app.delete("/cache")
async def clear_cache():
    """Golește cache."""
    cache.clear()
    return {"message": "Cache cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
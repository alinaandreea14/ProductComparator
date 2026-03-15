import instructor
from openai import OpenAI
from fastapi import HTTPException
from models.pydantic_models import ProductData, ComparisonResult

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# Patch cu Instructor pentru structured outputs
instructor_client = instructor.from_openai(client, mode=instructor.Mode.JSON)
MODEL = "qwen3:0.6b"

# =============================================================================
# INSTRUCTOR + LLM LOGIC
# =============================================================================

async def compara_produse_instructor(
    prod_a: ProductData,
    prod_b: ProductData,
    preferinte: str
) -> ComparisonResult:
    """
    Folosește Instructor pentru a forța output validat Pydantic.
    
    Instructor.wrap(client) + response_model=ComparisonResult
    = Garantat returnează obiect validat sau reîncearcă automat.
    """
    
    system_prompt = """Ești un expert în compararea produselor. 
                    Analizează datele reale ale produselor și compară-le STRICT pe criteriile userului.
                    Fii precis cu specificațiile tehnice extrase."""

    user_prompt = f"""Compară aceste produse pentru userul care vrea: "{preferinte}"

                    PRODUS A: {prod_a.titlu}
                    Descriere: {prod_a.descriere[:6000]}
                    Spec: {prod_a.specificatii[:4000]}

                    PRODUS B: {prod_b.titlu}
                    Descriere: {prod_b.descriere[:6000]}
                    Spec: {prod_b.specificatii[:4000]}

                    Generează tabel comparativ cu DOAR feature-urile relevante pentru preferințele userului.
                    Câștigătorul trebuie determinat bazat pe aceste preferințe, nu generic."""

    # INSTRUCTOR AICI: response_model=forțează structura exactă
    try:
        result = instructor_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_model=ComparisonResult,  # MAGIC: garantează validare Pydantic
            max_retries=2,  # Dacă e invalid, retrimite de 2 ori
            temperature=0,
            max_tokens=3000
        )
        return result
        
    except Exception as e:
        raise HTTPException(503, f"Instructor/LLM error: {str(e)}")
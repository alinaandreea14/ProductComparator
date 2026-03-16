import instructor
from openai import OpenAI
from fastapi import HTTPException
from models.pydantic_models import ProductData, ComparisonResult
from models.cot_models import CoTResponse, VerificationResult

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
    
async def comparison_with_cot_retry(prod_a, prod_b, preferinte, max_retries=3):
    feedback = ""
    attempt = 0

    while attempt < max_retries:
        # Generator prompt cu feedback din încercările anterioare
        generator_prompt = f"Compară {prod_a.titlu} vs {prod_b.titlu}. User: {preferinte}. {feedback}"

        prediction = instructor_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": generator_prompt}],
            response_model=CoTResponse,
        )

        # Verificare
        verifier_prompt = f"Evaluează logica: {prediction.gandire}. Concluzie: {prediction.raspuns}. Confidence: {prediction.confidence}"

        verification = instructor_client.chat.completions.create(
            model=MODEL,
            response_model=VerificationResult,
            messages=[
                {"role": "system", "content": "Ești un critic logic strict. Verifică dacă argumentele susțin concluzia."},
                {"role": "user", "content": verifier_prompt}
            ]
        )

        if verification.valid and prediction.confidence > 0.7:
            return {"result": prediction, "verification": verification, "attempts": attempt + 1}
        
        # Feedback
        feedback = f"\n\nREJECTED BY VERIFIER: {verification.motiv}. Please adjust your reasoning."
        attempt += 1

    raise HTTPException(status_code=422, detail="Nu s-a putut genera un răspuns valid după 3 încercări.")


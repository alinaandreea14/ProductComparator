from pydantic import BaseModel, Field
from typing import Optional

class CoTResponse(BaseModel):
    gandire: str = Field(description="Procesul detaliat de raționament, pas cu pas, care duce la soluție.")
    raspuns: str = Field(description="Rezultatul final extras în urma analizei comparative.")
    confidence: float = Field(ge=0, le=1, description="Gradul de certitudine al modelului în acuratețea răspunsului (0 = incert, 1 = certitudine totală).")

class VerificationResult(BaseModel):
    valid: bool = Field(..., description="Indicator boolean: True dacă logica este coerentă și corectă, False în caz contrar.")
    motiv: Optional[str] = Field(None, description="Explicația detaliată a erorilor sau inconsistențelor identificate (obligatoriu dacă valid=False).")
    recomandare: Optional[str] = Field(None, description="Sugestii specifice pentru corectarea sau îmbunătățirea raționamentului.")
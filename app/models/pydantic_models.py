# =============================================================================
# MODELE PYDANTIC (Instructor le folosește pentru validare)
# =============================================================================

from pydantic import BaseModel, Field
from typing import List, Optional

class ProductData(BaseModel):
    """Date extrase despre produs."""
    titlu: str = Field(description="Numele complet al produsului (ex. 'Apple MacBook Neo 13').")
    descriere: str = Field(description="O descriere scurtă a produsului, evidențiind caracteristicile principale.")
    specificatii: str = Field(description="Lista specificațiilor tehnice cheie ale produsului (ex. 'Procesor Intel i7, 16GB RAM, SSD 512GB').")
    preț: str = Field(
        default="",
        description="Prețul produsului, exprimat ca text (ex. '4999 lei' sau '1200 EUR')."
    )
    extras_din: str = Field(
        description="Sursa din care au fost extrase datele despre produs: 'scraping' (date preluate automat) sau 'text' (date introduse manual)."
    )

class FeatureComparison(BaseModel):
    """O linie din tabelul comparativ."""
    feature_name: str = Field(description="Numele caracteristicii comparate (ex. 'Durată baterie', 'Greutate', 'Culoare', 'Pret').")
    produs_a_value: str = Field(description="Valoarea caracteristicii pentru produsul A (ex. '10 ore', '1.2 kg', 'rosu', '4567 lei').")
    produs_b_value: str = Field(description="Valoarea caracteristicii pentru produsul B (ex. '8 ore', '1.5 kg', 'gri', '3456 lei').")
    winner_score: int = Field(
        ge=1, le=10, 
        description="Scorul diferenței dintre produse, pe o scară de la 1 la 10, "
        "unde 1 indică o diferență minimă, iar 10 o diferență semnificativă."
    )
    rationale: str = Field(description="Motivul pentru care un produs câștigă la această caracteristică.")
    winner: str = Field(
        pattern="^(A|B|Egal)$",
        description="Indică produsul câștigător pentru această caracteristică: "
        "'A' pentru produsul A, 'B' pentru produsul B, sau 'Egal' dacă sunt egale."
    )
    relevant_pentru_user: bool


class Verdict(BaseModel):
    """Verdict final al comparației."""
    rationale: str = Field(description="Motivul principal pentru care un produs este considerat câștigător în comparația generală.")
    câștigător: str = Field(
        pattern="^(A|B|Egal)$",
        description="Indică produsul câștigător al comparației generale: "
        "'A' pentru produsul A, 'B' pentru produsul B, sau 'Egal' dacă sunt egale."
    )
    scor_a: int = Field(
        ge=0, le=100, 
        description="Scorul total obținut de produsul A, pe o scară de la 0 la 100."
    )
    scor_b: int = Field(
        ge=0, le=100, 
        description="Scorul total obținut de produsul B, pe o scară de la 0 la 100."
    )
    diferență_semificativă: bool = Field(
        description="Indică dacă există o diferență semnificativă între cele două produse (True/False)."
    )
    argument_principal: str = Field(
        max_length=500,
        description="Argumentul principal care susține verdictul final, cu o lungime maximă de 500 de caractere."
    )
    compromisuri: str = Field(
        max_length=500,
        description="Descrierea compromisurilor făcute în comparație, cu o lungime maximă de 500 de caractere."
    )


# AICI ESTE MAGIA INSTRUCTOR: response_model garantează structura
class ComparisonResult(BaseModel):
    """
    Model final pe care Instructor îl forțează din LLM.
    Dacă LLM returnează JSON invalid, Instructor retrimite automat.
    """
    produs_a_titlu: str = Field(description="Titlul complet al produsului A (ex. 'Apple MacBook Neo 13').")
    produs_b_titlu: str = Field(description="Titlul complet al produsului B (ex. 'Laptop MacBook Air M2').")
    features: List[FeatureComparison] = Field(
        description="Lista caracteristicilor comparate între cele două produse, "
        "fiecare reprezentată printr-un obiect de tip FeatureComparison."
    )
    verdict: Verdict = Field(
        description="Verdictul final al comparației, incluzând câștigătorul, scorurile și justificările."
    )
    preferinte_procesate: str = Field(description="Rezumatul preferințelor utilizatorului, procesate și utilizate pentru a influența comparația.")


class ProductInput(BaseModel):
    sursa: str = Field(..., min_length=3)
    este_url: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sursa": "iPhone 15: A16, 6GB RAM, 48MP camera",
                "este_url": False
            }
        }


class ComparisonRequest(BaseModel):
    produs_a: ProductInput
    produs_b: ProductInput
    preferinte: str = Field(..., min_length=5, max_length=1000)
    buget_maxim: Optional[int] = Field(None, ge=100)
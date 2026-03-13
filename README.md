# Product Comparator
Product Comparator este o aplicație care permite compararea a două produse pe baza unor caracteristici definite, oferind un verdict final și un rezumat al preferințelor utilizatorului.

## Structura Proiectului

### Clase principale

#### 1. `FeatureComparison`
Această clasă ajută la obținerea unui rezultat comparativ între două produse. Fiecare linie conține informații despre o caracteristică specifică, valorile acesteia pentru fiecare produs și scorul diferenței.

#### 2. `Verdict`
Această clasă reprezintă verdictul final al comparației între două produse.

#### 3. `ComparisonResult`
Această clasă reprezintă rezultatul final al comparației.

## Cum funcționează

1. **Introducerea datelor**:
   - Utilizatorul introduce link-urile către produsele pe care dorește să le compare sau numele și caracteristicile acestora.

2. **Compararea caracteristicilor**:
   - Fiecare caracteristică este evaluată, iar un scor este atribuit pentru a indica diferența dintre produse.

3. **Generarea verdictului**:
   - Pe baza scorurilor și a justificărilor, se generează un verdict final care indică produsul câștigător.

4. **Rezumatul preferințelor**:
   - Preferințele utilizatorului sunt procesate și incluse în rezultatul final.
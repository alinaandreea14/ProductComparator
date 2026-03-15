# =============================================================================
# SCRAPING
# =============================================================================

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from fastapi import HTTPException

from models.pydantic_models import ProductData

async def scrape_product(url: str) -> ProductData:
    """
    Scrapează orice pagină de produs cu BeautifulSoup.
    Elimină elemente inutile, păstrează tot conținutul relevant.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            await page.goto(url, wait_until="networkidle", timeout=25000)
            await page.wait_for_timeout(2000)
            
            html = await page.content()
            title = await page.title()
            await browser.close()
            
            # BeautifulSoup pentru curățare
            soup = BeautifulSoup(html, 'html.parser')
            
            # ELIMINĂ elemente complet inutile
            for tag in soup.find_all([
                'script', 'style', 'nav', 'footer', 'header', 
                'aside', 'noscript', 'iframe', 'svg', 'canvas',
                'button', 'input', 'form', 'select', 'textarea',
                '[class*="cookie"]', '[class*="popup"]', '[class*="modal"]',
                '[id*="cookie"]', '[id*="popup"]', '[id*="modal"]',
                'advertisement', 'ad', 'banner'
            ]):
                tag.decompose()
            
            # EXTRAGE conținut util în ordinea importanței
            
            content_parts = []
            
            # 1. Titlu produs (din h1 sau meta)
            h1 = soup.find('h1')
            if h1:
                product_title = h1.get_text(strip=True)
                if product_title:
                    content_parts.append(f"PRODUCT: {product_title}")
            
            # 2. Descriere principală (meta description sau primele paragrafe)
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content_parts.append(f"DESCRIPTION: {meta_desc['content'][:500]}")
            
            # 3. Toate paragrafele cu text substanțial
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 30:  # Ignoră paragrafe scurte (menu items, etc.)
                    content_parts.append(text)
            
            # 4. Liste (de obicei specs sau features)
            for ul in soup.find_all(['ul', 'ol']):
                items = []
                for li in ul.find_all('li'):
                    item_text = li.get_text(strip=True)
                    if len(item_text) > 5:
                        items.append(item_text)
                if items:
                    content_parts.append(" | ".join(items[:15]))
            
            # 5. Tabele (specs tehnice)
            for table in soup.find_all('table'):
                rows = []
                for tr in table.find_all('tr')[:25]:
                    row_cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row_cells and any(cell for cell in row_cells):
                        rows.append(": ".join(row_cells[:2]))  # Label: Value
                if rows:
                    content_parts.append("SPECS: " + " | ".join(rows[:10]))
            
            # 6. Div-uri și secțiuni cu text dens (articole, descrieri)
            for element in soup.find_all(['div', 'section', 'article', 'main']):
                # Doar elemente cu mult text, nu containeri goi
                text = element.get_text(strip=True)
                if 200 < len(text) < 2000:  # Text substanțial dar nu enorm
                    # Verifică dacă nu e duplicat parțial
                    is_new = True
                    for existing in content_parts[-5:]:  # Compară cu ultimele 5
                        if text[:100] in existing or existing[:100] in text:
                            is_new = False
                            break
                    if is_new:
                        content_parts.append(text[:800])
            
            # Combină și deduplică
            seen_fragments = set()
            final_content = []
            
            for part in content_parts:
                # Normalizare pentru comparare
                normalized = " ".join(part.lower().split())[:100]
                if normalized not in seen_fragments and len(part) > 20:
                    seen_fragments.add(normalized)
                    final_content.append(part)
            
            # Text final curat
            full_text = "\n\n".join(final_content[:40])  # Limităm la 40 blocuri
            
            # Extrage preț simplu
            price = ""
            price_indicators = ['price', 'pret', 'preț', 'cost', '€', '$', 'lei', 'ron']
            for part in final_content[:10]:
                lower = part.lower()
                if any(ind in lower for ind in price_indicators):
                    # Caută pattern numeric lângă indicator
                    import re
                    matches = re.findall(r'[\d\s.,]+(?:lei|ron|€|\$|eur|usd)?', part, re.IGNORECASE)
                    if matches:
                        price = " ".join(matches[:2])
                        break
            
            return ProductData(
                titlu=title[:300] if title else url.split('/')[-1][:50],
                descriere=full_text[:6000],  # Tot conținutul curat
                specificatii="",  # Nu separăm - LLM extrage ce trebuie
                preț=price[:100],
                extras_din="beautifulsoup_clean"
            )
            
    except Exception as e:
        raise HTTPException(422, f"Scraping failed: {str(e)}")


def parse_text_input(text: str) -> ProductData:
    """Parsează input text liber."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return ProductData(
        titlu=lines[0][:200] if lines else "Unknown",
        descriere='\n'.join(lines[:20]),
        specificatii="",
        preț="",
        extras_din="text"
    )
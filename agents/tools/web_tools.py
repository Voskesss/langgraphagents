from langchain_core.tools import tool
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
import logging
import json

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def _search_web(query: str) -> str:
    """Zoek informatie op het web via DuckDuckGo.
    
    Args:
        query: De zoekterm om naar te zoeken
    """
    logger.info(f"Start web search met query: {query}")
    try:
        with DDGS() as ddgs:
            results = []
            logger.info("DuckDuckGo search gestart...")
            
            # Gebruik ddgs.text() met max_results
            search_results = list(ddgs.text(query, max_results=10))
            logger.info(f"Aantal resultaten gevonden: {len(search_results)}")
            
            if not search_results:
                logger.warning("Geen resultaten gevonden!")
                return "Geen resultaten gevonden voor deze zoekopdracht."
            
            # Format de resultaten
            for r in search_results:
                try:
                    result = {
                        "title": r.get('title', 'Geen titel'),
                        "link": r.get('link', 'Geen link'),
                        "snippet": r.get('body', 'Geen samenvatting')
                    }
                    results.append(
                        f"TITEL: {result['title']}\n"
                        f"URL: {result['link']}\n"
                        f"SAMENVATTING: {result['snippet']}\n"
                        "---"
                    )
                    logger.info(f"Resultaat verwerkt: {result['title']}")
                except Exception as e:
                    logger.error(f"Error bij verwerken resultaat: {str(e)}")
                    continue
            
            return "\n\n".join(results) if results else "Geen geldige resultaten gevonden."
            
    except Exception as e:
        error_msg = f"Error bij web search: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@tool
def _fetch_webpage_content(url: str) -> str:
    """Haal de inhoud van een webpage op.
    
    Args:
        url: De URL van de webpage om op te halen
    """
    logger.info(f"Start webpage fetch: {url}")
    try:
        logger.info("Maken HTTP request...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception voor niet-200 status codes
        
        logger.info("Parsen van HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verwijder scripts, styles en andere niet-relevante elementen
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Haal tekst op en verwijder lege regels
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        logger.info(f"Succesvol opgehaald, {len(cleaned_text)} karakters gevonden")
        # Log een preview van de content
        preview = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
        logger.info(f"Content preview: {preview}")
        
        return cleaned_text
        
    except requests.RequestException as e:
        error_msg = f"HTTP error bij ophalen webpage: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
    except Exception as e:
        error_msg = f"Onverwachte error bij ophalen webpage: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

# Exporteer de tool objecten
search_web = _search_web
fetch_webpage_content = _fetch_webpage_content

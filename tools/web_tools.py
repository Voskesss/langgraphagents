from langchain_core.tools import tool
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests

@tool
def _search_web(query: str) -> str:
    """Zoek informatie op het web via DuckDuckGo.
    
    Args:
        query: De zoekterm om naar te zoeken
    """
    with DDGS() as ddgs:
        results = []
        for r in ddgs.text(query, max_results=5):
            results.append(f"Title: {r['title']}\nLink: {r['link']}\nSnippet: {r['body']}\n")
        return "\n".join(results)

@tool
def _fetch_webpage_content(url: str) -> str:
    """Haal de inhoud van een webpage op.
    
    Args:
        url: De URL van de webpage om op te halen
    """
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Verwijder scripts en style elementen
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

# Exporteer de tool objecten
search_web = _search_web
fetch_webpage_content = _fetch_webpage_content

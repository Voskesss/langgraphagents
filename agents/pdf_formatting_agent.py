from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
import json
import logging

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Laad environment variables
load_dotenv()

def format_pdf(state: Dict[str, Any]) -> Dict[str, Any]:
    """PDF formatting agent functie."""
    research_results = state.get("research_results")
    if not research_results:
        return {"messages": [AIMessage(content="Geen onderzoeksresultaten gevonden om te verwerken.")]}
    
    logger.info(f"Ontvangen onderzoeksresultaten: {research_results}")
    
    # Initialiseer de agent
    agent = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        temperature=0,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Laat de agent de JSON structuur maken
    format_message = HumanMessage(content=f"""
    Maak een JSON structuur van deze onderzoeksresultaten voor een PDF rapport:

    {research_results}

    De JSON moet deze exacte structuur hebben:
    {{
        "title": "Titel van het rapport",
        "sections": {{
            "Introductie": "tekst...",
            "Bevindingen": "tekst...",
            "Analyse": "tekst...",
            "Conclusie": "tekst..."
        }}
    }}

    Belangrijke regels:
    1. Gebruik ALLEEN informatie uit de onderzoeksresultaten
    2. Gebruik NOOIT placeholders zoals [onderwerp] of [resultaat]
    3. Als informatie ontbreekt, schrijf dan expliciet "Deze informatie is niet gevonden in het onderzoek"
    4. Zorg dat de JSON geldig is en gebruik dubbele quotes

    Geef ALLEEN de JSON terug, geen andere tekst.
    """)
    
    # Krijg de JSON structuur
    json_response = agent.invoke([format_message])
    logger.info(f"Gegenereerde JSON: {json_response.content}")
    
    try:
        # Test of het geldige JSON is
        json.loads(json_response.content)
        return {
            "messages": [AIMessage(content="PDF wordt gegenereerd...")],
            "pdf_content": json_response.content
        }
    except json.JSONDecodeError as e:
        error_msg = f"Error bij het maken van de PDF structuur: {str(e)}"
        logger.error(error_msg)
        return {"messages": [AIMessage(content=error_msg)]}

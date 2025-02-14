from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
import json
import logging

# Update imports naar nieuwe locatie
from agents.tools.web_tools import search_web, fetch_webpage_content

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Laad environment variables
load_dotenv()

def web_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """Web research agent functie."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, HumanMessage):
        return {"messages": [AIMessage(content="Ik kan alleen reageren op gebruikersvragen.")]}
    
    # Initialiseer de agent
    agent = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        temperature=0,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    ).bind_tools([search_web, fetch_webpage_content])
    
    # Stap 1: Interpreteer de vraag en maak zoektermen
    interpret_message = HumanMessage(content=f"""
    Je bent een onderzoeksassistent. Interpreteer deze vraag en bedenk gerichte zoektermen:

    VRAAG: {last_message.content}

    1. Wat wil de gebruiker precies weten?
    2. Welke specifieke zoektermen zijn relevant?
    3. Geef een lijst van 2-3 concrete zoektermen.

    Geef je antwoord in dit formaat:
    {{
        "doel": "wat de gebruiker wil weten",
        "zoektermen": ["term1", "term2", "term3"]
    }}

    Gebruik ALLEEN JSON, geen andere tekst.
    """)
    
    interpret_response = agent.invoke([interpret_message])
    logger.info(f"Interpretatie resultaat: {interpret_response.content}")
    
    try:
        # Parse de JSON response
        if isinstance(interpret_response.content, str):
            search_info = json.loads(interpret_response.content)
        else:
            for item in interpret_response.content:
                if isinstance(item, dict) and 'text' in item:
                    search_info = json.loads(item['text'])
                    break
        
        # Voer searches uit voor elke zoekterm
        all_results = []
        for term in search_info["zoektermen"]:
            search_message = HumanMessage(content=f"Gebruik de search_web tool om te zoeken naar: {term}")
            search_response = agent.invoke([search_message])
            all_results.append(search_response.content)
            logger.info(f"Zoekresultaten voor '{term}': {search_response.content}")
        
        # Laat de agent de resultaten analyseren
        analyze_message = HumanMessage(content=f"""
        Analyseer deze zoekresultaten voor de originele vraag:

        VRAAG: {last_message.content}
        DOEL: {search_info["doel"]}
        
        RESULTATEN:
        {json.dumps(all_results, indent=2)}

        Maak een JSON rapport met deze structuur:
        {{
            "title": "Een titel die de vraag beantwoordt",
            "sections": {{
                "Samenvatting": "Kort overzicht van de bevindingen",
                "Belangrijkste Resultaten": "Concrete feiten en data",
                "Context en Details": "Achtergrond en extra informatie",
                "Bronnen": "Lijst van gebruikte bronnen"
            }}
        }}

        Belangrijk:
        1. Focus op het beantwoorden van de originele vraag
        2. Gebruik ALLEEN informatie uit de zoekresultaten
        3. Als je iets niet weet, zeg dat eerlijk
        4. Geen placeholders of algemene tekst gebruiken
        """)
        
        analysis_response = agent.invoke([analyze_message])
        logger.info(f"Analyse resultaat: {analysis_response.content}")
        
        return {
            "messages": messages + [analysis_response],
            "research_results": analysis_response.content
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"Error bij verwerken van zoekresultaten: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }
    except Exception as e:
        error_msg = f"Onverwachte error: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

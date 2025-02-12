from typing import Annotated, TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
import json
import logging

from tools import search_web, fetch_webpage_content, generate_pdf

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Laad environment variables
load_dotenv()

# Definieer de state structuur
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialiseer de agents
web_research_agent = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
).bind_tools([search_web, fetch_webpage_content])  # Alleen web search tools

pdf_formatting_agent = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
).bind_tools([generate_pdf])  # Alleen PDF tool

# Agent functies
def web_research(state: State) -> Dict[str, Any]:
    """Web research agent functie."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, HumanMessage):
        return {"messages": [AIMessage(content="Ik kan alleen reageren op gebruikersvragen.")]}
    
    # Stap 1: Interpreteer de vraag
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
    
    interpret_response = web_research_agent.invoke([interpret_message])
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
            # Gebruik direct de search_web tool
            results = search_web(term)
            all_results.append(results)
            logger.info(f"Zoekresultaten voor '{term}': {results}")
        
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
        5. Als er geen relevante resultaten zijn, zeg dat dan expliciet
        """)
        
        analysis_response = web_research_agent.invoke([analyze_message])
        logger.info(f"Analyse resultaat: {analysis_response.content}")
        
        # Valideer dat er geen standaardtekst wordt gebruikt
        if "zeespiegel" in analysis_response.content.lower():
            raise ValueError("Agent gebruikt standaardtekst over zeespiegelstijging")
            
        if "klimaat" in analysis_response.content.lower():
            raise ValueError("Agent gebruikt standaardtekst over klimaatverandering")
        
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

def format_pdf(state: State) -> Dict[str, Any]:
    """PDF formatting agent functie."""
    messages = state["messages"]
    research_results = state.get("research_results", "")
    
    logger.info(f"Ontvangen research resultaten voor PDF: {research_results}")
    
    # Laat de agent de PDF structureren en opmaken
    format_message = HumanMessage(content=f"""
    Je bent een documentspecialist. Verwerk deze onderzoeksresultaten in een professioneel PDF rapport:

    {research_results}

    Maak een JSON string met deze exacte structuur:
    {{
        "title": "Een specifieke titel gebaseerd op het onderwerp",
        "sections": {{
            "Samenvatting": "Korte overview van de concrete bevindingen",
            "Belangrijkste Resultaten": "Gedetailleerde uitwerking met specifieke feiten en data",
            "Context en Details": "Relevante achtergrond en aanvullende informatie",
            "Bronnen": "Lijst van gebruikte bronnen met URLs indien beschikbaar"
        }}
    }}

    Belangrijk:
    1. Gebruik ALLEEN informatie uit de onderzoeksresultaten
    2. Vul ALLE secties met concrete, specifieke informatie
    3. GEEN placeholders of algemene tekst
    4. Zorg dat elke sectie minimaal 2-3 zinnen bevat
    """)
    
    ai_message = pdf_formatting_agent.invoke([format_message])
    logger.info(f"PDF formatting resultaat: {ai_message.content}")
    
    # Parse de JSON output en maak de PDF
    try:
        content = ""
        if isinstance(ai_message.content, list):
            for item in ai_message.content:
                if isinstance(item, dict) and item.get('type') == 'tool_use':
                    content = item.get('input', {}).get('content', '')
                    logger.info("Content gevonden in tool gebruik")
                    break
        else:
            content = ai_message.content
            
        logger.info(f"Content voor PDF generatie: {content}")
        
        # Valideer dat er geen placeholders zijn
        if '[' in content or ']' in content:
            raise ValueError("PDF content bevat nog placeholders")
            
        pdf_path = generate_pdf(content)
        return {
            "messages": messages + [ai_message],
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        error_msg = f"Error bij PDF generatie: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

def process_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Verwerk een zoekopdracht en genereer een PDF."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, HumanMessage):
        return {"messages": [AIMessage(content="Ik kan alleen reageren op gebruikersvragen.")]}

    # Stap 1: Web research
    research_message = HumanMessage(content=f"""
    Je bent een onderzoeksassistent. Lees deze vraag zorgvuldig:
    {last_message.content}

    1. Gebruik de search_web tool om relevante bronnen te vinden
    2. Analyseer de resultaten en maak een duidelijke samenvatting
    3. Gebruik ALLEEN informatie die je echt vindt
    4. Als je iets niet kunt vinden, zeg dat dan eerlijk
    """)
    
    ai_message = web_research_agent.invoke([research_message])
    logger.info(f"Web research resultaten: {ai_message.content}")
    
    # Stap 2: PDF formatting
    format_message = HumanMessage(content=f"""
    Je bent een documentspecialist. Maak een PDF rapport van deze onderzoeksresultaten:
    {ai_message.content}

    Gebruik deze JSON structuur:
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
    1. Gebruik ALLEEN informatie uit de onderzoeksresultaten
    2. Geen placeholders of algemene tekst
    3. Als informatie ontbreekt, zeg dat dan expliciet
    """)
    
    pdf_message = pdf_formatting_agent.invoke([format_message])
    logger.info(f"PDF formatting resultaat: {pdf_message.content}")
    
    # Parse de JSON en genereer PDF
    try:
        content = ""
        if isinstance(pdf_message.content, list):
            for item in pdf_message.content:
                if isinstance(item, dict) and item.get('type') == 'tool_use':
                    content = item.get('input', {}).get('content', '')
                    logger.info("Content gevonden in tool gebruik")
                    break
        else:
            content = pdf_message.content
            
        logger.info(f"Content voor PDF generatie: {content}")
        
        # Valideer dat er geen placeholders zijn
        if '[' in content or ']' in content:
            raise ValueError("PDF content bevat nog placeholders")
            
        pdf_path = generate_pdf(content)
        return {
            "messages": messages + [AIMessage(content=f"PDF rapport is gegenereerd: {pdf_path}")],
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        error_msg = f"Error bij PDF generatie: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

# Bouw de workflow graph
workflow = StateGraph(State)

# Voeg nodes toe
workflow.add_node("web_research", web_research)
workflow.add_node("format_pdf", format_pdf)
workflow.add_node("process_query", process_query)

# Definieer edges
workflow.add_edge(START, "web_research")
workflow.add_edge("web_research", "format_pdf")
workflow.add_edge("format_pdf", "process_query")
workflow.add_edge("process_query", END)

# Compileer de graph
agent_workflow = workflow.compile()

def process_query_external(query: str, thread_id: str = "default") -> Dict[str, Any]:
    """
    Verwerk een zoekopdracht door de multi-agent workflow.
    
    Args:
        query: De zoekopdracht
        thread_id: Unieke identifier voor het gesprek
    
    Returns:
        Dictionary met de eindstatus van de workflow
    """
    # Initialiseer de state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "research_results": "",
        "pdf_path": ""
    }
    
    # Voer de workflow uit
    final_state = agent_workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}}
    )
    
    return final_state

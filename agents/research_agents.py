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
    messages: Annotated[list[BaseMessage], add_messages]
    research_results: str
    pdf_path: str

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
    
    try:
        # Direct zoeken met de vraag
        results = search_web(last_message.content)
        logger.info(f"Zoekresultaten: {results}")
        
        # Laat de agent de resultaten analyseren
        analyze_message = HumanMessage(content=f"""
        Je bent een onderzoeksassistent. Analyseer deze zoekresultaten en maak een gestructureerd rapport.
        
        VRAAG: {last_message.content}
        
        RESULTATEN:
        {results}
        
        Maak een rapport in dit JSON formaat:
        {{
            "title": "Een duidelijke titel die de vraag samenvat",
            "sections": {{
                "Samenvatting": "Korte samenvatting van de bevindingen",
                "Belangrijkste Resultaten": "Belangrijkste feiten en data",
                "Context en Details": "Meer gedetailleerde informatie",
                "Bronnen": "Lijst van gebruikte bronnen met URLs"
            }}
        }}
        
        Geef ALLEEN de JSON terug, geen andere tekst.
        """)
        
        analysis_response = web_research_agent.invoke([analyze_message])
        logger.info(f"Analyse resultaat: {analysis_response}")
        
        # Probeer de JSON te parsen uit de response
        try:
            content = analysis_response.content
            # Verwijder eventuele markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            # Valideer de JSON
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Response moet een dictionary zijn")
                
            if "title" not in parsed or "sections" not in parsed:
                raise ValueError("Response mist verplichte velden 'title' of 'sections'")
                
            required_sections = ["Samenvatting", "Belangrijkste Resultaten", "Context en Details", "Bronnen"]
            for section in required_sections:
                if section not in parsed["sections"]:
                    raise ValueError(f"Response mist verplichte sectie: {section}")
            
            # Geef de research results door aan de volgende agent
            logger.info("Research resultaten succesvol gegenereerd")
            return {
                "messages": messages + [AIMessage(content="Onderzoek voltooid, nu maken we er een PDF van.")],
                "research_results": content  # De JSON string voor de PDF agent
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            logger.error(f"Content was: {content}")
            return {
                "messages": messages + [AIMessage(content=f"Error bij verwerken van onderzoeksresultaten: {str(e)}")]
            }
            
    except Exception as e:
        error_msg = f"Error bij web research: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

def format_pdf(state: State) -> Dict[str, Any]:
    """PDF formatting agent functie."""
    messages = state["messages"]
    research_results = state.get("research_results", "")
    
    logger.info(f"Ontvangen research resultaten voor PDF: {research_results}")
    
    # Controleer of we geldige research results hebben
    if not research_results:
        return {
            "messages": messages + [AIMessage(content="Geen onderzoeksresultaten om te verwerken")]
        }
    
    try:
        # Gebruik de generate_pdf tool direct
        pdf_path = generate_pdf(research_results)
        logger.info(f"PDF gegenereerd op pad: {pdf_path}")
            
        return {
            "messages": messages + [AIMessage(content=f"PDF succesvol gegenereerd: {pdf_path}")],
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

# Definieer edges
workflow.add_edge(START, "web_research")
workflow.add_edge("web_research", "format_pdf")
workflow.add_edge("format_pdf", END)

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

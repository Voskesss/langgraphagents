from typing import Annotated, TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
import json

from tools import search_web, fetch_webpage_content, generate_pdf

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
    
    # Laat de agent zoeken en de resultaten analyseren
    research_message = HumanMessage(content=f"""
    Zoek informatie over het volgende onderwerp: {last_message.content}
    
    1. Gebruik de search_web tool om relevante bronnen te vinden
    2. Gebruik fetch_webpage_content voor gedetailleerde informatie
    3. Organiseer de informatie in een duidelijke structuur
    4. Geef een samenvatting van je bevindingen
    """)
    
    ai_message = web_research_agent.invoke([research_message])
    
    # Sla de resultaten op in de state
    return {
        "messages": [AIMessage(content="Onderzoek voltooid, nu ga ik een PDF maken.")],
        "research_results": ai_message.content
    }

def format_pdf(state: State) -> Dict[str, Any]:
    """PDF formatting agent functie."""
    research_results = state.get("research_results", "")
    
    # Laat de agent de PDF structureren en opmaken
    format_message = HumanMessage(content=f"""
    Maak een goed gestructureerde PDF van de volgende onderzoeksresultaten:
    
    {research_results}
    
    Geef de output als een JSON string met de volgende structuur:
    {{
        "title": "Titel van het rapport",
        "sections": {{
            "Sectie 1 titel": "Sectie 1 content",
            "Sectie 2 titel": "Sectie 2 content",
            ...
        }}
    }}
    """)
    
    ai_message = pdf_formatting_agent.invoke([format_message])
    
    # Parse de JSON output en maak de PDF
    try:
        # Haal de JSON string uit het AI bericht
        if isinstance(ai_message.content, list):
            # Als het een lijst is, pak dan het laatste bericht
            content = ai_message.content[-1].get('content', '')
        else:
            # Anders gebruik de content direct
            content = ai_message.content
            
        # Genereer de PDF met de tool
        pdf_result = generate_pdf.invoke(content)
        
        return {
            "messages": [AIMessage(content=f"PDF gegenereerd: {pdf_result}")],
            "pdf_content": {"path": "output.pdf"}
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"Error bij het genereren van de PDF: {str(e)}")],
            "pdf_content": {}
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

def process_query(query: str, thread_id: str = "default") -> Dict[str, Any]:
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
        "pdf_content": {}
    }
    
    # Voer de workflow uit
    final_state = agent_workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}}
    )
    
    return final_state

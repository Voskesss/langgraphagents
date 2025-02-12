from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
from tools import search_web, fetch_webpage_content

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
    
    # Laat de agent zoeken en de resultaten analyseren
    research_message = HumanMessage(content=f"""
    Zoek informatie over het volgende onderwerp: {last_message.content}
    
    1. Gebruik de search_web tool om relevante bronnen te vinden
    2. Gebruik fetch_webpage_content voor gedetailleerde informatie
    3. Organiseer de informatie in een duidelijke structuur
    4. Geef een samenvatting van je bevindingen
    """)
    
    ai_message = agent.invoke([research_message])
    
    # Sla de resultaten op in de state
    return {
        "messages": [AIMessage(content="Onderzoek voltooid, nu ga ik een PDF maken.")],
        "research_results": ai_message.content
    }

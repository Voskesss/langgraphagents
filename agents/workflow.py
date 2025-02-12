from typing import Annotated, TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

from .web_research_agent import web_research
from .pdf_formatting_agent import format_pdf

# Definieer de state structuur
class State(TypedDict):
    messages: Annotated[list, add_messages]

def create_workflow() -> StateGraph:
    """Maak en configureer de workflow."""
    # Maak de graph
    workflow = StateGraph(State)
    
    # Voeg nodes toe
    workflow.add_node("web_research", web_research)
    workflow.add_node("format_pdf", format_pdf)
    
    # Definieer edges
    workflow.add_edge(START, "web_research")
    workflow.add_edge("web_research", "format_pdf")
    workflow.add_edge("format_pdf", END)
    
    return workflow.compile()

# Maak een singleton instance van de workflow
agent_workflow = create_workflow()

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

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, BaseMessage
from dataclasses import dataclass
import logging

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definieer de state structuur
@dataclass
class State:
    """State voor de workflow."""
    messages: List[BaseMessage]
    research_results: Optional[str] = None
    pdf_path: Optional[str] = None

def get_next_step(state: Dict[str, Any]) -> str:
    """Bepaal de volgende stap in de workflow."""
    logger.info("Bepalen volgende stap...")
    
    # Als er nog geen research_results zijn, begin met web research
    if not state.get("research_results"):
        logger.info("Volgende stap: web_research")
        return "web_research"
    
    # Als er research_results zijn maar geen pdf_path, ga naar format_pdf
    if not state.get("pdf_path"):
        logger.info("Volgende stap: format_pdf")
        return "format_pdf"
    
    # Als alles klaar is, beëindig de workflow
    logger.info("Workflow compleet")
    return END

def create_workflow() -> StateGraph:
    """Maak en configureer de workflow."""
    # Maak de graph
    workflow = StateGraph(State)
    
    # Voeg nodes toe
    from .web_research_agent import web_research
    from .pdf_formatting_agent import format_pdf

    workflow.add_node("web_research", web_research)
    workflow.add_node("format_pdf", format_pdf)
    
    # Definieer edges met conditionele routing
    workflow.add_conditional_edges(
        START,
        get_next_step
    )
    workflow.add_conditional_edges(
        "web_research",
        get_next_step
    )
    workflow.add_conditional_edges(
        "format_pdf",
        get_next_step
    )

    return workflow.compile()

# Maak een singleton instance van de workflow
agent_workflow = create_workflow()

def process_query(query: str, thread_id: str = "default") -> Dict[str, Any]:
    """
    Verwerk een zoekopdracht door de workflow.
    
    Args:
        query: De zoekopdracht
        thread_id: Unieke identifier voor het gesprek
    
    Returns:
        Dictionary met de eindstatus van de workflow
    """
    # Initialiseer de state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "research_results": None,
        "pdf_path": None
    }
    
    # Voer de workflow uit
    final_state = agent_workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}}
    )
    
    return final_state

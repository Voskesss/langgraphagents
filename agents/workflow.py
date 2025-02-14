from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph.message import add_messages
from dataclasses import dataclass
import logging

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definieer de state structuur
class State(TypedDict):
    """State voor de workflow met uitgebreide functionaliteit."""
    # Berichten geschiedenis met add_messages reducer
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Web research resultaten
    research_results: Optional[str]
    research_status: Optional[str]  # 'pending', 'completed', 'failed'
    
    # PDF gerelateerde velden
    pdf_path: Optional[str]
    pdf_status: Optional[str]  # 'pending', 'completed', 'failed'
    
    # Human review velden
    human_approved: Optional[bool]
    review_comments: Optional[str]
    review_status: Optional[str]  # 'pending', 'approved', 'rejected'
    
    # Error handling
    error_message: Optional[str]
    retry_count: Optional[int]

def get_next_step(state: Dict[str, Any]) -> str:
    """Bepaal de volgende stap in de workflow."""
    logger.info("Bepalen volgende stap...")
    
    # Check voor errors
    if state.get("error_message"):
        logger.error(f"Error gevonden: {state['error_message']}")
        return END
    
    # Als er nog geen research_results zijn, begin met web research
    if not state.get("research_results"):
        logger.info("Volgende stap: web_research")
        return "web_research"
    
    # Als research klaar is maar nog niet gereviewd, ga naar human review
    if state.get("research_status") == "completed" and state.get("review_status") != "approved":
        logger.info("Volgende stap: human_review")
        return "human_review"
    
    # Als research is goedgekeurd maar geen pdf_path, ga naar format_pdf
    if state.get("review_status") == "approved" and not state.get("pdf_path"):
        logger.info("Volgende stap: format_pdf")
        return "format_pdf"
    
    # Als pdf is gemaakt, klaar
    if state.get("pdf_path"):
        logger.info("Workflow compleet")
        return END
    
    # Fallback
    logger.warning("Onverwachte state, workflow wordt beëindigd")
    return END

def create_workflow() -> StateGraph:
    """Maak en configureer de workflow."""
    # Maak de graph
    workflow = StateGraph(State)
    
    # Importeer de nodige functies
    from agents.web_research_agent import web_research
    from agents.pdf_formatting_agent import format_pdf
    from agents.tools.human_review_tool import human_review
    
    # Voeg nodes toe
    workflow.add_node("web_research", web_research)
    workflow.add_node("human_review", human_review)
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
        "human_review",
        get_next_step
    )
    workflow.add_conditional_edges(
        "format_pdf",
        get_next_step
    )
    
    return workflow

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
        "pdf_path": None,
        "research_status": None,
        "pdf_status": None,
        "human_approved": None,
        "review_comments": None,
        "review_status": None,
        "error_message": None,
        "retry_count": None
    }
    
    # Voer de workflow uit
    final_state = agent_workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}}
    )
    
    return final_state

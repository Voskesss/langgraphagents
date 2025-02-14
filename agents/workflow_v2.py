from typing import Annotated, TypedDict, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
import logging

# Absolute imports met correcte module paden
from agents.tools.web_tools import search_web, fetch_webpage_content
from agents.tools.pdf_tools import generate_pdf
from agents.tools.human_review_tool import human_review

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Laad environment variables
load_dotenv()

class State(TypedDict):
    """State voor de V2 workflow met uitgebreide functionaliteit."""
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

# Initialiseer de agents
web_research_agent = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
).bind_tools([search_web, fetch_webpage_content])

def web_research(state: State) -> Dict[str, Any]:
    """Web research agent functie."""
    try:
        # Reset error state
        state["error_message"] = None
        state["research_status"] = "pending"
        
        # Voer research uit
        response = web_research_agent.invoke(state["messages"])
        
        return {
            "messages": [response],
            "research_results": response.content,
            "research_status": "completed"
        }
    except Exception as e:
        logger.error(f"Error in web research: {str(e)}")
        return {
            "error_message": str(e),
            "research_status": "failed",
            "retry_count": (state.get("retry_count") or 0) + 1
        }

def review_research(state: State) -> Dict[str, Any]:
    """Human review functie voor research resultaten."""
    try:
        state["review_status"] = "pending"
        
        # Vraag om human review
        review_result = human_review(
            content=state["research_results"],
            review_type="research"
        )
        
        # Update state met review resultaat
        return {
            "human_approved": review_result["human_approved"],
            "review_comments": review_result["review_comments"],
            "review_status": review_result["review_status"]
        }
    except Exception as e:
        logger.error(f"Error in review: {str(e)}")
        return {
            "error_message": str(e),
            "review_status": "failed"
        }

def format_pdf(state: State) -> Dict[str, Any]:
    """PDF formatting functie."""
    try:
        state["pdf_status"] = "pending"
        
        # Genereer PDF
        pdf_path = generate_pdf(state["research_results"])
        
        return {
            "pdf_path": pdf_path,
            "pdf_status": "completed"
        }
    except Exception as e:
        logger.error(f"Error in PDF formatting: {str(e)}")
        return {
            "error_message": str(e),
            "pdf_status": "failed"
        }

def get_next_step(state: State) -> str:
    """Bepaal de volgende stap in de workflow."""
    logger.info("Bepalen volgende stap...")
    
    # Check voor errors
    if state.get("error_message"):
        if (state.get("retry_count") or 0) >= 3:
            logger.error(f"Max retries bereikt. Error: {state['error_message']}")
            return END
        logger.warning(f"Error gevonden: {state['error_message']}, opnieuw proberen...")
        return "web_research"
    
    # Normale flow
    if not state.get("research_results") or state.get("research_status") != "completed":
        return "web_research"
    
    if state.get("review_status") != "approved":
        return "review_research"
    
    if not state.get("pdf_path"):
        return "format_pdf"
    
    return END

def create_workflow() -> StateGraph:
    """Maak en configureer de V2 workflow."""
    workflow = StateGraph(State)
    
    # Voeg nodes toe
    workflow.add_node("web_research", web_research)
    workflow.add_node("review_research", review_research)
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
        "review_research",
        get_next_step
    )
    workflow.add_conditional_edges(
        "format_pdf",
        get_next_step
    )
    
    return workflow

def process_query_v2(query: str, thread_id: str = "default") -> Dict[str, Any]:
    """
    Verwerk een zoekopdracht met de V2 workflow.
    
    Args:
        query: De zoekopdracht
        thread_id: Unieke identifier voor het gesprek
    
    Returns:
        Dictionary met de eindstatus van de workflow
    """
    # Maak initiele state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "research_results": None,
        "research_status": None,
        "pdf_path": None,
        "pdf_status": None,
        "human_approved": None,
        "review_comments": None,
        "review_status": None,
        "error_message": None,
        "retry_count": 0
    }
    
    # Maak en configureer de workflow
    workflow = create_workflow()
    
    # Voer de workflow uit
    final_state = workflow.invoke(initial_state)
    
    return final_state

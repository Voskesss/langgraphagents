from typing import Dict, Any, Optional
from langchain_core.tools import tool
from langgraph.types import Command, interrupt

@tool
def human_review(content: str, review_type: str) -> Dict[str, Any]:
    """
    Vraag een mens om review van content.
    
    Args:
        content: De content die gereviewd moet worden
        review_type: Type review ('research' of 'pdf')
    """
    # Toon informatie aan de reviewer
    human_response = interrupt({
        "review_type": review_type,
        "content": content,
        "message": "Wilt u deze content reviewen? (ja/nee)",
        "instructions": "Geef eventueel commentaar mee in het 'comments' veld"
    })
    
    # Verwerk de response
    is_approved = human_response.get("approved", "").lower().startswith("j")
    comments = human_response.get("comments", "")
    
    # Update de state via een Command
    state_update = {
        "human_approved": is_approved,
        "review_comments": comments,
        "review_status": "approved" if is_approved else "rejected"
    }
    
    return Command(update=state_update)

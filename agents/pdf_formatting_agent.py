from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv
import json
from tools import generate_pdf

# Laad environment variables
load_dotenv()

def format_pdf(state: Dict[str, Any]) -> Dict[str, Any]:
    """PDF formatting agent functie."""
    research_results = state.get("research_results", "")
    
    # Initialiseer de agent
    agent = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        temperature=0,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    ).bind_tools([generate_pdf])
    
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
    
    ai_message = agent.invoke([format_message])
    
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

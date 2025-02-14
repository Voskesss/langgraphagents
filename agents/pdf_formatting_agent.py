from typing import Dict, Any
from langchain_core.messages import AIMessage
import os
import json
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import tempfile

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_pdf(state: Dict[str, Any]) -> Dict[str, Any]:
    """PDF formatting functie."""
    messages = state["messages"]
    research_results = state.get("research_results", "")
    
    if not research_results:
        return {
            "messages": messages + [AIMessage(content="Geen onderzoeksresultaten om te formatteren")]
        }
    
    try:
        # Parse de research results
        if isinstance(research_results, str):
            content = research_results
        else:
            content = json.dumps(research_results)
            
        # Valideer dat alle secties aanwezig zijn
        parsed = json.loads(content)
        required_sections = ["title", "sections"]
        for section in required_sections:
            if section not in parsed:
                raise ValueError(f"Content mist verplichte sectie: {section}")
                
        required_subsections = ["Samenvatting", "Belangrijkste Resultaten", "Context en Details", "Bronnen"]
        for subsection in required_subsections:
            if subsection not in parsed["sections"]:
                raise ValueError(f"Content mist verplichte subsectie: {subsection}")
        
        # Check dat bronnen een array is met de juiste structuur
        bronnen = parsed["sections"]["Bronnen"]
        if not isinstance(bronnen, list):
            raise ValueError("Bronnen moet een array zijn")
            
        for bron in bronnen:
            if not isinstance(bron, dict):
                raise ValueError("Elke bron moet een object zijn")
            if "url" not in bron or "titel" not in bron or "relevantie" not in bron:
                raise ValueError("Elke bron moet url, titel en relevantie hebben")
        
        # Genereer de PDF
        pdf_path = generate_pdf(content)
        
        return {
            "messages": messages + [AIMessage(content=f"PDF succesvol gegenereerd: {pdf_path}")],
            "pdf_path": pdf_path
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"Error bij JSON parsen: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }
    except Exception as e:
        error_msg = f"Error bij PDF generatie: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

def generate_pdf(content: str) -> str:
    """
    Genereer een PDF bestand van de JSON content.
    
    Args:
        content: JSON string met de PDF inhoud
        
    Returns:
        Path naar het gegenereerde PDF bestand
    """
    # Parse de JSON content
    data = json.loads(content)
    
    # Maak een tijdelijk bestand voor de PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        pdf_path = temp_pdf.name
    
    # Maak het PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Maak de stijlen
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2C3E50')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#34495E')
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=6,
        spaceAfter=6,
        textColor=colors.HexColor('#2C3E50')
    )
    source_style = ParagraphStyle(
        'CustomSource',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7F8C8D'),
        leftIndent=20
    )
    
    # Maak de content
    story = []
    
    # Titel
    story.append(Paragraph(data['title'], title_style))
    story.append(Spacer(1, 12))
    
    # Secties
    sections = data['sections']
    for section_title in ["Samenvatting", "Belangrijkste Resultaten", "Context en Details"]:
        if section_title in sections:
            story.append(Paragraph(section_title, heading_style))
            story.append(Paragraph(sections[section_title], body_style))
            story.append(Spacer(1, 12))
    
    # Bronnen sectie
    if "Bronnen" in sections:
        story.append(Paragraph("Bronnen", heading_style))
        bronnen = sections["Bronnen"]
        
        # Maak een lijst van bronnen met links
        for bron in bronnen:
            bron_text = f'<link href="{bron["url"]}">{bron["titel"]}</link>'
            if bron.get("relevantie"):
                bron_text += f' - {bron["relevantie"]}'
            story.append(Paragraph(bron_text, source_style))
            story.append(Spacer(1, 6))
    
    # Genereer de PDF
    doc.build(story)
    logger.info(f"PDF gegenereerd: {pdf_path}")
    
    return pdf_path

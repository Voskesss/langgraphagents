from langchain_core.tools import tool
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import json
import logging

# Configureer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def _generate_pdf(content: str) -> str:
    """Maak een PDF met mooie opmaak. Verwacht een JSON string met title en sections.
    
    Args:
        content: Een JSON string met de volgende structuur:
                {
                    "title": "Titel van het rapport",
                    "sections": {
                        "Sectie 1 titel": "Sectie 1 content",
                        "Sectie 2 titel": "Sectie 2 content"
                    }
                }
    """
    try:
        logger.info("Start PDF generatie")
        logger.info(f"Ontvangen content: {content}")
        
        # Parse JSON
        data = json.loads(content)
        logger.info(f"JSON succesvol geparsed: {data}")
        
        title = data.get("title", "Onderzoeksrapport")
        sections = data.get("sections", {})
        
        output_path = "output.pdf"
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Maak custom stijlen
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Bouw het document op
        elements = []
        
        # Titel
        logger.info(f"Toevoegen titel: {title}")
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        # Content secties
        for section_title, section_content in sections.items():
            logger.info(f"Toevoegen sectie: {section_title}")
            elements.append(Paragraph(section_title, heading_style))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(section_content, body_style))
            elements.append(Spacer(1, 12))
        
        # Genereer PDF
        logger.info("Start PDF build")
        doc.build(elements)
        logger.info("PDF build voltooid")
        
        return f"PDF succesvol gegenereerd: {output_path}"
    except json.JSONDecodeError as e:
        error_msg = f"Error bij parsen van JSON: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error bij genereren van PDF: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

# Exporteer het tool object
generate_pdf = _generate_pdf

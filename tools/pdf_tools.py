from langchain_core.tools import tool
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import json

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
        data = json.loads(content)
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
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        # Content secties
        for section_title, section_content in sections.items():
            elements.append(Paragraph(section_title, heading_style))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(section_content, body_style))
            elements.append(Spacer(1, 12))
        
        # Genereer PDF
        doc.build(elements)
        return f"PDF succesvol gegenereerd: {output_path}"
    except Exception as e:
        return f"Error generating PDF: {str(e)}"

# Exporteer het tool object
generate_pdf = _generate_pdf

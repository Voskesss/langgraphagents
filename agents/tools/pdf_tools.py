from langchain_core.tools import tool
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import logging
import os
from datetime import datetime
import traceback

# Configureer logging met meer details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Maak output directory als die niet bestaat
OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    logger.info(f"Output directory aangemaakt: {OUTPUT_DIR}")

@tool
def _generate_pdf(content: str) -> str:
    """Maak een PDF met mooie opmaak. Verwacht een JSON string met title en sections."""
    try:
        logger.info("Start PDF generatie")
        logger.info(f"Ontvangen content type: {type(content)}")
        logger.info(f"Ontvangen content: {content}")
        
        # Parse JSON
        try:
            data = json.loads(content)
            logger.info(f"JSON succesvol geparsed: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            logger.error(f"Problematische content: {content}")
            raise
        
        title = data.get("title", "Onderzoeksrapport")
        sections = data.get("sections", {})
        
        logger.info(f"Titel: {title}")
        logger.info(f"Aantal secties: {len(sections)}")
        logger.info(f"Sectie namen: {list(sections.keys())}")
        
        # Maak unieke bestandsnaam met timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"rapport_{timestamp}.pdf")
        logger.info(f"Output pad: {output_path}")
        
        # Maak het PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Maak custom stijlen
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Centreer de titel
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e'),
            borderPadding=(10, 0, 10, 0),
            borderWidth=0,
            borderColor=colors.HexColor('#bdc3c7'),
            borderRadius=5
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        source_style = ParagraphStyle(
            'SourceStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            leftIndent=20
        )
        
        # Bouw het document op
        elements = []
        
        try:
            # Titel
            logger.info(f"Toevoegen titel: {title}")
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 30))
            
            # Content secties
            for section_title, section_content in sections.items():
                logger.info(f"Verwerken sectie: {section_title}")
                logger.info(f"Sectie content type: {type(section_content)}")
                
                # Sectie titel
                elements.append(Paragraph(section_title, heading_style))
                elements.append(Spacer(1, 6))
                
                # Speciale behandeling voor bronnen sectie
                if section_title == "Bronnen":
                    if isinstance(section_content, str):
                        # Split bronnen op newlines als het een string is
                        sources = section_content.split('\n')
                        for source in sources:
                            if source.strip():
                                elements.append(Paragraph(f"• {source.strip()}", source_style))
                    elif isinstance(section_content, list):
                        # Als het een lijst is, voeg elke bron toe
                        for source in section_content:
                            elements.append(Paragraph(f"• {source}", source_style))
                else:
                    # Normale sectie content
                    if not isinstance(section_content, str):
                        section_content = str(section_content)
                    elements.append(Paragraph(section_content, body_style))
                
                elements.append(Spacer(1, 12))
            
            # Voeg footer toe met timestamp
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#95a5a6'),
                alignment=1
            )
            footer_text = f"Gegenereerd op {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(footer_text, footer_style))
            
        except Exception as e:
            logger.error(f"Error bij opbouwen PDF elementen: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
        # Genereer PDF
        logger.info("Start PDF build")
        try:
            doc.build(elements)
            logger.info("PDF build voltooid")
        except Exception as e:
            logger.error(f"Error bij PDF build: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
        return output_path
        
    except Exception as e:
        error_msg = f"Error bij genereren van PDF: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Exporteer het tool object
generate_pdf = _generate_pdf

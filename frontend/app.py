import streamlit as st
import sys
import os
import uuid
import glob
from datetime import datetime
import re

# Voeg de root directory toe aan de Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from agents.research_agents import process_query_external
from agents.workflow_v2 import process_query_v2

# Helper functies
def sanitize_filename(text):
    """Maak een veilige bestandsnaam van de tekst."""
    # Verwijder speciale tekens en maak lowercase
    safe_text = re.sub(r'[^\w\s-]', '', text.lower())
    # Vervang spaties door underscores
    safe_text = re.sub(r'[-\s]+', '_', safe_text)
    # Beperk de lengte
    return safe_text[:50]

def get_pdf_path(query):
    """Genereer een uniek PDF pad met timestamp en query."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = sanitize_filename(query)
    return os.path.join("output", f"{safe_query}_{timestamp}.pdf")

def list_pdf_files():
    """Lijst alle PDF bestanden in de output directory."""
    if not os.path.exists("output"):
        os.makedirs("output")
    return glob.glob("output/*.pdf")

def delete_pdf(pdf_path):
    """Verwijder een PDF bestand."""
    try:
        os.remove(pdf_path)
        return True
    except Exception as e:
        st.error(f"Fout bij verwijderen: {str(e)}")
        return False

# Pagina configuratie
st.set_page_config(
    page_title="Web Research Assistant",
    page_icon="🔍",
    layout="centered"
)

# Titel en uitleg
st.title("🔍 Web Research Assistant")
st.markdown("""
Deze assistant kan het web doorzoeken en de resultaten verwerken in een mooie PDF.
Geef een onderwerp of vraag op, en de assistant zal:
1. Het web doorzoeken voor relevante informatie
2. De informatie analyseren en structureren
3. Een professioneel opgemaakte PDF genereren
""")

# Initialiseer session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "version" not in st.session_state:
    st.session_state.version = "v1"

# Sidebar met opties en PDF lijst
with st.sidebar:
    st.header("Opties")
    
    # Versie selectie
    version = st.radio(
        "Kies versie:",
        ["Standaard (V1)", "Nieuw met review (V2)"],
        index=0 if st.session_state.version == "v1" else 1,
        help="V2 heeft menselijke review en betere error handling"
    )
    st.session_state.version = "v1" if version == "Standaard (V1)" else "v2"
    
    # Knop om chat te resetten
    if st.button("Begin nieuw onderzoek"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()
    
    # Toon lijst van PDFs
    st.header("PDF Rapporten")
    pdf_files = list_pdf_files()
    
    if not pdf_files:
        st.info("Nog geen PDF rapporten gegenereerd")
    else:
        for pdf_path in pdf_files:
            col1, col2 = st.columns([3, 1])
            
            # Bestandsnaam zonder pad
            filename = os.path.basename(pdf_path)
            
            # Open PDF knop
            with col1:
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label=filename,
                        data=pdf_file,
                        file_name=filename,
                        mime="application/pdf"
                    )
            
            # Delete knop
            with col2:
                if st.button("🗑️", key=f"delete_{filename}"):
                    if delete_pdf(pdf_path):
                        st.success("PDF verwijderd!")
                        st.rerun()

# Chat input
vraag = st.chat_input("Waar wil je meer over weten?")

# Toon chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Verwerk nieuwe vraag
if vraag:
    # Toon gebruikersvraag
    with st.chat_message("user"):
        st.write(vraag)
    
    # Voeg vraag toe aan history
    st.session_state.messages.append({"role": "user", "content": vraag})
    
    # Maak output directory als die niet bestaat
    if not os.path.exists("output"):
        os.makedirs("output")
    
    # Genereer PDF pad
    pdf_path = get_pdf_path(vraag)
    
    # Toon "aan het werk" indicator
    with st.chat_message("assistant"):
        with st.spinner("Even zoeken en verwerken..."):
            # Kies de juiste workflow op basis van versie
            if st.session_state.version == "v1":
                result = process_query_external(vraag, thread_id=st.session_state.thread_id)
                status_message = "Onderzoek voltooid!"
            else:
                result = process_query_v2(vraag, thread_id=st.session_state.thread_id)
                
                # Toon extra informatie voor V2
                if result.get("review_status") == "approved":
                    status_message = "Onderzoek voltooid en goedgekeurd! ✅"
                elif result.get("error_message"):
                    status_message = f"Er is een fout opgetreden: {result['error_message']}"
                else:
                    status_message = "Onderzoek voltooid, wachtend op review..."
            
            # Toon resultaat en PDF link
            if "pdf_path" in result and result["pdf_path"]:
                # Hernoem de gegenereerde PDF
                if os.path.exists(result["pdf_path"]):
                    os.rename(result["pdf_path"], pdf_path)
                    st.success(f"{status_message} De resultaten zijn opgeslagen in: {os.path.basename(pdf_path)}")
                    
                    # Toon download knop
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF Rapport",
                            data=pdf_file,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf"
                        )
            else:
                if st.session_state.version == "v2" and result.get("error_message"):
                    st.error(f"Fout: {result['error_message']}")
                else:
                    st.error("Er is iets misgegaan bij het genereren van de PDF.")
    
    # Voeg antwoord toe aan history
    st.session_state.messages.append({
        "role": "assistant",
        "content": status_message
    })

# Toon extra informatie over de actieve versie
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Actieve versie: {'V1' if st.session_state.version == 'v1' else 'V2'}**")
if st.session_state.version == "v2":
    st.sidebar.markdown("""
    **V2 Features:**
    - Menselijke review van resultaten
    - Verbeterde error handling
    - Status tracking
    - Retry mechanisme
    """)

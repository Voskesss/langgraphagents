import streamlit as st
import sys
import os
import uuid

# Voeg de root directory toe aan de Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.research_agents import process_query_external

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

# Initialiseer session state voor chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

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
    
    # Toon "aan het werk" indicator
    with st.chat_message("assistant"):
        with st.spinner("Even zoeken en verwerken..."):
            # Verwerk de vraag door de multi-agent workflow
            result = process_query_external(vraag, thread_id=st.session_state.thread_id)
            
            # Toon resultaat en PDF link
            if "pdf_path" in result:
                pdf_path = result["pdf_path"]
                st.success(f"Onderzoek voltooid! De resultaten zijn opgeslagen in: {pdf_path}")
                
                # Als de PDF bestaat, toon een download knop
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF Rapport",
                            data=pdf_file,
                            file_name="research_report.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("Er is iets misgegaan bij het genereren van de PDF.")
    
    # Voeg antwoord toe aan history
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Onderzoek voltooid en PDF rapport gegenereerd!"
    })

# Sidebar met extra opties
with st.sidebar:
    st.header("Opties")
    
    # Knop om chat te resetten
    if st.button("Begin nieuw onderzoek"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        # Verwijder oude PDF bestanden
        if os.path.exists("output.pdf"):
            os.remove("output.pdf")
        st.rerun()

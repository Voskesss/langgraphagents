import streamlit as st
import sys
import os

# Voeg de root directory toe aan de Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.basic_agent import stel_vraag
import uuid

# Pagina configuratie
st.set_page_config(
    page_title="LangChain Agent Chat",
    page_icon="🤖",
    layout="centered"
)

# Titel en uitleg
st.title("🤖 LangChain Agent Chat")
st.markdown("""
Deze chatbot kan vragen beantwoorden en informatie opzoeken. 
Stel een vraag en de agent zal zijn best doen om te helpen!
""")

# Initialiseer session state voor chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Chat input
vraag = st.chat_input("Stel je vraag hier...")

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
    
    # Toon "aan het denken" indicator
    with st.chat_message("assistant"):
        with st.spinner("Even denken..."):
            # Haal antwoord op van de agent
            antwoord = stel_vraag(vraag, thread_id=st.session_state.thread_id)
            st.write(antwoord)
    
    # Voeg antwoord toe aan history
    st.session_state.messages.append({"role": "assistant", "content": antwoord})

# Sidebar met extra opties
with st.sidebar:
    st.header("Chat Opties")
    
    # Knop om chat te resetten
    if st.button("Begin nieuwe chat"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

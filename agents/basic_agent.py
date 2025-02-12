from typing import Annotated, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

# Laad environment variables
load_dotenv()

# Definieer de state structuur
class State(TypedDict):
    # Messages hebben het type "list". De add_messages functie in de annotatie
    # definieert hoe deze state key moet worden geüpdatet (in dit geval: berichten toevoegen)
    messages: Annotated[list, add_messages]

# Definieer een eenvoudige tool
@tool
def zoek_informatie(query: str) -> str:
    """Zoek informatie op basis van een query."""
    # Dit is een placeholder - later kunnen we dit vervangen door echte zoekfunctionaliteit
    return f"Dit is een voorbeeld antwoord voor de zoekopdracht: {query}"

# Lijst van beschikbare tools
tools = [zoek_informatie]

# Initialiseer de LLM (Anthropic's Claude)
llm = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Bind tools aan de LLM
llm_with_tools = llm.bind_tools(tools)

# Creëer de graph
graph_builder = StateGraph(State)

# Definieer de chatbot node
def chatbot(state: State) -> Dict[str, Any]:
    # Haal de laatste message op
    messages = state["messages"]
    
    # Laat de LLM reageren
    ai_message = llm_with_tools.invoke(messages)
    
    # Return de nieuwe state met het AI antwoord
    return {"messages": [ai_message]}

# Voeg de chatbot node toe aan de graph
graph_builder.add_node("chatbot", chatbot)

# Definieer de edges: START -> chatbot -> END
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compileer de graph
agent = graph_builder.compile()

def stel_vraag(vraag: str, thread_id: str = "default") -> str:
    """
    Stel een vraag aan de agent.
    
    Args:
        vraag: De vraag voor de agent
        thread_id: Unieke identifier voor het gesprek (voor het behouden van context)
    
    Returns:
        Het antwoord van de agent
    """
    # Maak een HumanMessage van de vraag
    human_message = HumanMessage(content=vraag)
    
    # Roep de agent aan met de message
    final_state = agent.invoke(
        {"messages": [human_message]},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # Haal het laatste bericht op en return de content
    last_message = final_state["messages"][-1]
    return last_message.content

if __name__ == "__main__":
    # Test de agent
    vraag = "Wat kun je me vertellen over Amsterdam?"
    antwoord = stel_vraag(vraag)
    print(f"\nVraag: {vraag}")
    print(f"Antwoord: {antwoord}")

from typing import Annotated, Sequence, TypedDict, Union, List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from langchain_core.tools import BaseTool, tool
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import operator
import os

# Laad environment variables
load_dotenv()

# Definieer een eenvoudige tool
@tool
def zoek_informatie(query: str) -> str:
    """Zoek informatie op basis van een query."""
    # Dit is een placeholder - later kunnen we dit vervangen door echte zoekfunctionaliteit
    return f"Dit is een voorbeeld antwoord voor de zoekopdracht: {query}"

# Lijst van beschikbare tools
tools = [zoek_informatie]

def get_llm(provider: str = "anthropic"):
    """
    Krijg een LLM instance gebaseerd op de gekozen provider.
    
    Args:
        provider: 'anthropic' of 'openai'
    """
    if provider.lower() == "anthropic":
        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    elif provider.lower() == "openai":
        return ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        raise ValueError("Provider moet 'anthropic' of 'openai' zijn")

class AgentState(TypedDict):
    """Type definitie voor de agent state."""
    messages: List[BaseMessage]
    current_step: str

def create_agent(provider: str = "anthropic") -> Graph:
    """
    Maak een nieuwe agent met de gespecificeerde LLM provider.
    
    Args:
        provider: 'anthropic' of 'openai'
        
    Returns:
        Een gecompileerde agent graph
    """
    # Initialiseer de LLM
    llm = get_llm(provider)
    
    # Maak het prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Je bent een behulpzame AI assistent die vragen beantwoordt en taken uitvoert."),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Maak de agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # Maak een tool executor
    tool_executor = ToolExecutor(tools)
    
    # Definieer de agent workflow
    workflow = StateGraph(AgentState)
    
    # Voeg nodes toe voor de agent en tool execution
    workflow.add_node("agent", agent)
    workflow.add_node("tools", tool_executor)
    
    # Definieer wanneer we stoppen
    def should_continue(state: AgentState) -> bool:
        """Bepaal of we door moeten gaan met de agent loop."""
        return state["current_step"] != "end"
    
    # Voeg edges toe
    workflow.add_edge("agent", "tools")
    workflow.add_edge("tools", "agent")
    
    # Stel de entry point in
    workflow.set_entry_point("agent")
    
    # Compileer de graph
    app = workflow.compile()
    
    return app

def run_agent(agent: Graph, vraag: str) -> str:
    """
    Voer de agent uit met een vraag.
    
    Args:
        agent: De gecompileerde agent graph
        vraag: De vraag voor de agent
        
    Returns:
        Het antwoord van de agent
    """
    # Initiële state
    state = {
        "messages": [HumanMessage(content=vraag)],
        "current_step": "agent"
    }
    
    # Voer de agent uit
    result = agent.invoke(state)
    
    # Haal het laatste bericht op
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "Sorry, er is iets misgegaan bij het genereren van een antwoord."

if __name__ == "__main__":
    # Test beide LLMs
    vraag = "Wat is het verschil tussen Python en JavaScript?"
    
    print("\nTesten met Claude (Anthropic):")
    claude_agent = create_agent(provider="anthropic")
    antwoord_claude = run_agent(claude_agent, vraag)
    print(f"Claude's antwoord: {antwoord_claude}\n")
    
    print("\nTesten met GPT-4 (OpenAI):")
    gpt_agent = create_agent(provider="openai")
    antwoord_gpt = run_agent(gpt_agent, vraag)
    print(f"GPT-4's antwoord: {antwoord_gpt}\n")

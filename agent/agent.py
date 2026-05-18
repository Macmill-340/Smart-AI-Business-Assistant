import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from agent.rag import retrieve_context
from backend.database import engine, Lead
from sqlmodel import Session

load_dotenv()

#state
class AgentState(TypedDict):
    user_input:str
    history:str
    intent:str
    context:str
    final_answer:str

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", api_key=os.getenv("GEMINI_API_KEY"))

#node1
def planner_node(state: AgentState):
    """decides what the user wants to do"""
    query = state["user_input"]
    prompt = f"""
    You are a routing AI. 
    Recent Chat History: {state['history']}
    
    Analyze the user's latest input: '{query}'
    1. If the user is asking a factual question, inquiring about services, policies, prices, or seeking information, output exactly: RAG
    2. If the user wants to buy something, place an order, or leaves their contact info, output exactly: LEAD
    3. If they ask to sync data, export leads, or update the CRM, output exactly: CRM
    4. If the user is just saying hello, making small talk, or general chit-chat, output exactly: CHAT
    """

    response = llm.invoke(prompt)
    intent = str(response.text).strip().upper()
    if "RAG"in intent:
        intent = "RAG"
    elif "LEAD" in intent:
        intent = "LEAD"
    elif "CRM" in intent:
        intent = "CRM"
    else:
        intent = "CHAT"

    return {"intent": intent}

#node2
def executor_node(state: AgentState):
    """executes tool based on intent"""
    intent = state["intent"]
    query = state["user_input"]

    if intent =="RAG":
        context = retrieve_context(query)
        return {"context": context}

    elif intent == "CRM":
        #mock integration
        with open("local_crm_sync.csv", "a") as f:
            f.write(f"Synced Lead: {query}\n")
        return {"context": "Successfully synced lead data to local CSV CRM."}

    elif intent == "LEAD":
        prompt = f"""Extract the lead details from the conversation.
                Recent Chat History: {state['history']}
                Latest Input: '{query}'

                You must reply with exactly 3 lines of text in this exact format:
                Name: [their name or 'Unknown']
                Intent: [hot, warm, or cold]
                Notes: [what they want to buy or do]"""

        extracted = str(llm.invoke(prompt).text).strip()

        #parse
        lead_name = "Unknown"
        lead_intent = "warm"
        lead_notes = extracted

        for line in extracted.split('\n'):
            if line.startswith("Name:"):
                lead_name = line.replace("Name:", "").strip()
            elif line.startswith("Intent:"):
                lead_intent = line.replace("Intent:", "").strip().lower()
            elif line.startswith("Notes:"):
                lead_notes = line.replace("Notes:", "").strip()

        #save
        with Session(engine) as session:
            new_lead = Lead(name=lead_name, intent=lead_intent, notes=lead_notes)
            session.add(new_lead)
            session.commit()

        return {"context": f"Lead safely captured. Name: {lead_name}, Intent: {lead_intent}."}
    return {"context": "No specific tools needed"}

#node3
def critic_node(state: AgentState):
    f"""generates final response and ensures its accurate"""
    query = state["user_input"]
    context = state.get("context", "")
    intent = state["intent"]
    if intent == "RAG":
        prompt = f"Answer the user's question based ONLY on this context. If the context doesn't answer it, say you don't know.\nContext: {context}\nQuestion: {query}"
    elif intent == "LEAD":
        prompt = f"The user wanted to become a lead. Here is what our system did: {context}. Write a polite, 1-sentence confirmation message to the user thanking them."
    elif intent == "CRM":
        prompt = f"The user asked to sync the CRM. Here is what the system did: {context}. Write a polite, 1-sentence confirmation message to the user letting them know the sync was successful."
    else:
        prompt = prompt = f"""You are a helpful business assistant. 
        Recent Chat History: {state['history']}
        User's Latest Input: {query}
        Reply naturally to the user."""

    response = llm.invoke(prompt)
    return {"final_answer": response.text}

#graph
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("critic", critic_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "critic")
workflow.add_edge("critic", END)

graph = workflow.compile()

def run_agent(user_input: str, history: str) -> str:
    result = graph.invoke({
        "user_input": user_input,
        "history": history,
        "intent": "",
        "context": "",
        "final_answer": ""
    })

    ans = result["final_answer"]
    if isinstance(ans, list):
        ans = " ".join([block.get("text", "") for block in ans if isinstance(block, dict)])
    elif isinstance(ans, dict):
        ans = ans.get("text", str(ans))

    return str(ans)
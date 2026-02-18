import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

load_dotenv()

# Load LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    api_key=os.getenv("GEMINI_API_KEY")
)


# ---- Conversation State Model ---- #
class ChatState(BaseModel):
    messages: list[str] = Field(default_factory=list)


# ---- Node: Main Conversational Handler ---- #
def llm_node(state: ChatState) -> ChatState:
    user_message = state.messages[-1]  # latest user message

    # Structured system prompt for Phase 2
    system_prompt = (
        "You are TIA-Sales, an NBFC conversational assistant.\n"
        "Answer professionally, politely, and keep responses short for now."
    )

    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ])

    reply_text = response.content

    return ChatState(messages=state.messages + [reply_text])


# ---- Build Graph ---- #
graph_builder = StateGraph(ChatState)
graph_builder.add_node("llm_node", llm_node)
graph_builder.set_entry_point("llm_node")
master_graph = graph_builder.compile()
 
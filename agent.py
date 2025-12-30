from typing import TypedDict, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage
)
from langgraph.graph import StateGraph, END

from agentic_ai import (
    flight_search,
    hotel_recommendation,
    places_discovery,
    budget_estimation
)
from langchain_core.tools import StructuredTool
# ---------------------------
# STATE
# ---------------------------
class AgentState(TypedDict):
    messages: List[BaseMessage]

# ---------------------------
# LLM
# ---------------------------
llm = ChatOpenAI(model="gpt-4o-mini")



tools = {
    "flight_search": flight_search,
    "hotel_recommendation": hotel_recommendation,
    "places_discovery": places_discovery,
    "budget_estimation": budget_estimation,
}

llm_with_tools = llm.bind_tools(list(tools.values()))

# ---------------------------
# AGENT NODE
# ---------------------------
def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

# ---------------------------
# TOOL EXECUTOR NODE
# ---------------------------
from langchain_core.messages import ToolMessage

def tool_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_messages = []

    for call in last_message.tool_calls:
        tool_fn = tools[call["name"]]

        # ✅ Pass the FULL argument dictionary
        tool_result = tool_fn.invoke(call["args"])

        tool_messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=call["id"]
            )
        )

    return {"messages": state["messages"] + tool_messages}



# ---------------------------
# ROUTER
# ---------------------------
def should_continue(state: AgentState):
    last = state["messages"][-1]
    return "tools" if last.tool_calls else END

# ---------------------------
# GRAPH
# ---------------------------
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")

agent = graph.compile()

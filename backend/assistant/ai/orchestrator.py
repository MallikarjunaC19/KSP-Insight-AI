"""
KSP Insight AI (KAVACH AI) — Assistant AI Orchestrator
App: assistant / ai

REWRITTEN for LangChain 1.x. The old `create_tool_calling_agent` +
`AgentExecutor` pattern is gone in 1.x — `langchain.agents.create_agent`
is now the entry point, built on LangGraph under the hood.

Deliberately NOT using LangGraph's checkpointer for conversation memory
— Django's ChatMessage table is already the source of truth and the
RBAC boundary, so history is loaded from there and passed in fresh on
every call rather than maintaining a second, parallel persistence layer
inside LangGraph. This keeps "Django as the RBAC/security boundary"
literally true — there's nowhere else conversation state lives.

Usage unchanged from before:

    from assistant.ai.orchestrator import KavachAssistant
    from assistant.models import Conversation

    conversation = Conversation.objects.get(id=..., officer=officer)
    assistant = KavachAssistant(officer)
    ai_message = assistant.handle_message(conversation, "How many open FIRs at my station?")

Requires: pip install langchain langgraph langchain-openai
Requires env var: OPENAI_API_KEY
"""

import time

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from assistant.models import ChatMessage, AuditLog
from assistant.ai.tools import (
    make_sql_lookup_tool, make_graph_lookup_tool,
    make_quickml_tool, make_bhashini_tool, make_general_answer_tool,
)


SYSTEM_PROMPT_TEMPLATE = """You are the KAVACH AI assistant for Karnataka State Police officers.

You have five tools available:
  - sql_lookup: crimes, FIRs, arrests, chargesheets, court cases, officers
  - graph_lookup: relationship/network questions between people, vehicles, and cases
  - quickml: predictive/analytical questions — hotspots, trends, risk scores
  - bhashini: Kannada <-> English translation/transcription
  - general_answer: definitional or conversational questions that don't need the database

Rules:
  - Any question asking to assess/predict/estimate crime severity, case
    solvability, investigation priority, or hotspot/area risk MUST go
    through the quickml tool. Do NOT answer these from general
    knowledge, "typical factors," or your own reasoning about what
    might make a crime severe — even if you feel confident you could
    write a plausible-sounding answer. A plausible-sounding answer that
    didn't come from the real trained model is a fabrication, not a
    shortcut, and it skips the audit trail entirely.
  - Only answer using information returned by your tools, or genuinely
    general legal/procedural knowledge that has nothing to do with the
    four quickml prediction categories above (e.g. "what does IPC 392
    cover" is fine to answer directly; "how severe is this incident" is
    NOT — that's quickml's job even though you could improvise an
    answer).
  - Never invent case numbers, names, or statistics that a tool didn't
    return.
  - If a tool returns a "not implemented yet" stub message, tell the
    officer plainly that this capability isn't available yet — do not
    pretend to have looked something up.
  - Keep answers concise and operational; officers are using this on
    duty, not reading a report.
  - You are speaking with {officer_name}, badge {badge_number}, at
    {police_station_name}. Every tool call is already scoped to what
    this officer is allowed to see, so you don't need to add your own
    restrictions on top.
"""


class KavachAssistant:
    def __init__(self, officer, model: str = "openai/gpt-oss-120b"):        # Groq-hosted open-weight model (not OpenAI-hosted, despite the
        # name) — current recommended pick for tool-calling agents since
        # Groq deprecated llama-3.3-70b-versatile / llama-3.1-8b-instant
        # on 2026-06-17. Swap to "openai/gpt-oss-20b" for faster/cheaper.
        self.officer = officer
        self.model_name = model
        self.trace_sink = []
        self.tools = [
            make_sql_lookup_tool(officer, self.trace_sink),
            make_graph_lookup_tool(officer),
            make_quickml_tool(officer),
            make_bhashini_tool(officer),
            make_general_answer_tool(officer, model=model),
        ]
        self.llm = ChatGroq(model=model, temperature=0.2)
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            officer_name=f"{officer.first_name} {officer.last_name}",
            badge_number=officer.badge_number,
            police_station_name=officer.police_station.name,
        )
        # create_agent (LangChain 1.x) builds a LangGraph agent under the
        # hood: model + tools + system_prompt, no checkpointer — we manage
        # persistence ourselves via Django, see handle_message() below.
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def _load_history(self, conversation, limit: int = 20):
        """Pulls recent turns from this conversation and converts them
        to LangChain message objects, so the agent has context without
        needing a LangGraph checkpointer — Django stays the single
        source of truth for conversation state."""
        history = []
        recent = conversation.messages.order_by("-created_at")[:limit]
        for msg in reversed(recent):
            if msg.sender == ChatMessage.Sender.USER:
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))
        return history

    def handle_message(self, conversation, user_text: str) -> ChatMessage:
        """
        Persists the officer's message, runs the agent, persists the
        AI's response (with an execution trace in metadata), logs an
        AuditLog entry, and returns the AI's ChatMessage row.
        """
        if conversation.officer_id != self.officer.id:
            raise ValueError("Conversation does not belong to this officer.")

        self.trace_sink.clear()  # don't leak SQL from a prior call on this instance

        ChatMessage.objects.create(
            conversation=conversation, sender=ChatMessage.Sender.USER, content=user_text,
        )

        chat_history = self._load_history(conversation)
        input_messages = chat_history + [HumanMessage(content=user_text)]

        started = time.monotonic()
        result = self.agent.invoke(
            {"messages": input_messages},
            config={"recursion_limit": 10},  # bounds the tool-call loop, ~5 tool round trips
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)

        result_messages = result["messages"]
        answer = result_messages[-1].content

        tools_used = [
            m.name for m in result_messages
            if isinstance(m, ToolMessage) and m.name
        ]

        ai_message = ChatMessage.objects.create(
            conversation=conversation,
            sender=ChatMessage.Sender.AI,
            content=answer,
            metadata={
                "tools_used": tools_used,
                "elapsed_ms": elapsed_ms,
                "model": self.model_name,
                "sql_trace": list(self.trace_sink),
            },
        )

        conversation.save(update_fields=["updated_at"])

        AuditLog.objects.create(
            officer=self.officer,
            action_type=AuditLog.ActionType.QUERY,
            description=f"AI query: {user_text[:200]}",
            related_conversation=conversation,
        )

        return ai_message

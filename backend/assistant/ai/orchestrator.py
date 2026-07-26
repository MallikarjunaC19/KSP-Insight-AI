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

Reverted from Gemini back to Groq. The InvalidArgument retry wrapper
from the Gemini version is intentionally NOT carried over — that's a
Gemini-specific exception type with no direct Groq equivalent, and the
original Groq-based orchestrator (already confirmed working end-to-end)
never needed it. GraphRecursionError handling is kept — that's
LangGraph's own exception, unrelated to LLM provider.

Usage unchanged from before:

    from assistant.ai.orchestrator import KavachAssistant
    from assistant.models import Conversation

    conversation = Conversation.objects.get(id=..., officer=officer)
    assistant = KavachAssistant(officer)
    ai_message = assistant.handle_message(conversation, "How many open FIRs at my station?")

Requires: pip install langchain langgraph langchain-groq
Requires env var: GROQ_API_KEY
"""

import re
import time
from pathlib import Path

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.errors import GraphRecursionError

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from assistant.models import ChatMessage, AuditLog
from assistant.ai.tools import (
    make_sql_lookup_tool, make_graph_lookup_tool,
    make_quickml_tool, make_bhashini_tool, make_general_answer_tool,
)


# Matches the exact string bhashini's synthesize path returns:
#   f"Kannada audio response generated: {audio_url}"
# Kept as a module-level constant so the fallback regex and the tool's
# own format string can't silently drift apart without someone noticing.
BHASHINI_AUDIO_URL_RE = re.compile(r"Kannada audio response generated:\s*(\S+)")


SYSTEM_PROMPT_TEMPLATE = """You are the KAVACH AI assistant for Karnataka State Police officers.

You have five tools available:
  - sql_lookup: crimes, FIRs, arrests, chargesheets, court cases, officers
  - graph_lookup: relationship/network questions between people, vehicles, and cases
  - quickml: predictive/analytical questions — hotspots, trends, risk scores
  - bhashini: Kannada <-> English translation and Kannada speech generation
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
  - When responding to an officer in Kannada, use the bhashini tool:
      - To speak your response aloud in Kannada (default), call
        bhashini with the plain English text of your answer — e.g.
        bhashini("Your FIR has been registered under section 392.")
      - To return your response as Kannada TEXT instead of audio (the
        officer explicitly asked for a written Kannada reply, or audio
        isn't appropriate here), prefix the input with "text:" — e.g.
        bhashini("text:Your FIR has been registered under section 392.")
      - If the officer writes to you in Kannada script, pass that text
        straight to bhashini to get it translated to English before you
        act on it. (Spoken Kannada audio is already transcribed to
        English before it reaches you — you'll only ever see it as
        English text, so you don't need to call bhashini for that case.)
  - You are speaking with {officer_name}, badge {badge_number}, at
    {police_station_name}. Every tool call is already scoped to what
    this officer is allowed to see, so you don't need to add your own
    restrictions on top.
    - When bhashini generates spoken Kannada audio, your final answer to
    the officer MUST include the exact audio URL bhashini returned —
    do not paraphrase it away. Include both the URL and a brief
    English summary of the answer.
  - If the officer's own message was written in Kannada script, your
    visible answer text MUST itself be in Kannada — call bhashini with
    the "text:" prefix (e.g. bhashini("text:<your English answer
    here>")) and use ITS returned Kannada text as your final answer,
    not an English summary with an audio link attached. Optionally you
    may also call bhashini a second time without the prefix to attach
    spoken audio alongside the Kannada text, but the primary visible
    response must be Kannada text either way.
"""


class KavachAssistant:
    def __init__(self, officer, model: str = "openai/gpt-oss-120b"):
        # Groq-hosted open-weight model (not OpenAI-hosted, despite the
        # name) — current recommended pick for tool-calling agents.
        # Swap to "openai/gpt-oss-20b" for faster/cheaper if needed.
        self.officer = officer
        self.model_name = model
        self.trace_sink = []
        self.ml_trace_sink = []    # quickml's structured trace
        self.tools = [
            make_sql_lookup_tool(officer, self.trace_sink),
            make_graph_lookup_tool(officer),
            make_quickml_tool(officer, self.ml_trace_sink),
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

    @staticmethod
    def _find_bhashini_audio_url(result_messages):
        """Scans the tool-call trace for a bhashini audio-synthesis
        result and pulls out the audio URL, most recent call last.

        This exists as a safety net, not the primary mechanism — the
        system prompt already instructs the agent to include the URL
        verbatim. Prompt-only enforcement of "preserve this substring
        exactly" is exactly the kind of instruction LLMs quietly drop
        under paraphrasing pressure, so this guarantees the officer
        gets a working link even if the agent summarizes it away.
        """
        found_url = None
        for m in result_messages:
            if not (isinstance(m, ToolMessage) and m.name == "bhashini"):
                continue
            content = m.content if isinstance(m.content, str) else str(m.content)
            match = BHASHINI_AUDIO_URL_RE.search(content)
            if match:
                found_url = match.group(1)  # keep the last match, in case bhashini fires more than once
        return found_url

    def handle_message(self, conversation, user_text: str) -> ChatMessage:
        """
        Persists the officer's message, runs the agent, persists the
        AI's response (with an execution trace in metadata), logs an
        AuditLog entry, and returns the AI's ChatMessage row.
        """
        if conversation.officer_id != self.officer.id:
            raise ValueError("Conversation does not belong to this officer.")

        self.trace_sink.clear()
        self.ml_trace_sink.clear()

        user_message = ChatMessage.objects.create(
            conversation=conversation, sender=ChatMessage.Sender.USER, content=user_text,
        )

        chat_history = self._load_history(conversation)
        input_messages = chat_history + [HumanMessage(content=user_text)]

        started = time.monotonic()
        try:
            result = self.agent.invoke(
                {"messages": input_messages},
                config={"recursion_limit": 15},
            )
        except GraphRecursionError:
            user_message.delete()
            return ChatMessage.objects.create(
                conversation=conversation,
                sender=ChatMessage.Sender.AI,
                content="I wasn't able to resolve that question after several attempts — try rephrasing it more specifically (e.g. naming the exact station).",
                metadata={"tools_used": [], "elapsed_ms": 0, "model": self.model_name,
                        "sql_trace": [], "ml_trace": [], "audio_url": None},
            )
        except Exception:
            user_message.delete()
            raise
        elapsed_ms = int((time.monotonic() - started) * 1000)

        result_messages = result["messages"]
        answer = result_messages[-1].content

        tools_used = [
            m.name for m in result_messages
            if isinstance(m, ToolMessage) and m.name
        ]

        # Belt-and-suspenders: if bhashini generated spoken audio but the
        # agent's final answer dropped the URL (paraphrased it away
        # instead of following the system prompt), append it here so the
        # officer/frontend always has a working link to the audio.
        audio_url = None
        if "bhashini" in tools_used:
            audio_url = self._find_bhashini_audio_url(result_messages)
            if audio_url and audio_url not in answer:
                answer = f"{answer}\n\nAudio: {audio_url}"

        ai_message = ChatMessage.objects.create(
            conversation=conversation,
            sender=ChatMessage.Sender.AI,
            content=answer,
            metadata={
                "tools_used": tools_used,
                "elapsed_ms": elapsed_ms,
                "model": self.model_name,
                "sql_trace": list(self.trace_sink),
                "ml_trace": list(self.ml_trace_sink),
                "audio_url": audio_url,
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
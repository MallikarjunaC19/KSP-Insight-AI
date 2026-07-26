"""
KSP Insight AI (KAVACH AI) — Vanna Client

Uses Vanna's legacy (<2.0) mixin API with Groq as the LLM provider.
Only generate_sql() is used. All generated SQL is validated and scoped
(see assistant/ai/sql_scope.py) before execution — Vanna's output is
never trusted or run directly.

Reverted from a Gemini-based version back to Groq — Groq's message
format (list of {"role", "content"} dicts) maps directly onto its
chat.completions.create(messages=...) call, so submit_prompt() here is
simpler than the Gemini version's flatten-to-string approach.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from vanna.chromadb import ChromaDB_VectorStore
from vanna.base import VannaBase
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _create_groq_client(api_key: str):
    return Groq(api_key=api_key)


class _GroqLLM(VannaBase):
    """
    Groq implementation for Vanna — legacy mixin "bring your own LLM"
    pattern (implement system_message/user_message/assistant_message/
    submit_prompt, matching Vanna's own reference implementations).
    """

    def __init__(self, config=None):
        super().__init__(config=config)

        config = config or {}

        api_key = config.get("api_key") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. Set it in backend/.env."
            )

        self.client = _create_groq_client(api_key)
        self.model_name = config.get(
            "model",
            os.getenv("VANNA_GROQ_MODEL", "openai/gpt-oss-120b"),
        )

    def system_message(self, message: str):
        return {"role": "system", "content": message}

    def user_message(self, message: str):
        return {"role": "user", "content": message}

    def assistant_message(self, message: str):
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=prompt,  # already [{"role": ..., "content": ...}, ...] — Groq takes this directly
            temperature=0.0,  # SQL generation should be deterministic, not creative
        )
        return response.choices[0].message.content.strip()


class KavachVanna(ChromaDB_VectorStore, _GroqLLM):

    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        _GroqLLM.__init__(self, config=config)


_instance = None


def get_vanna() -> KavachVanna:
    global _instance

    if _instance is None:
        _instance = KavachVanna(
            config={
                "path": os.getenv(
                    "VANNA_CHROMA_PATH",
                    "./vanna_chroma_store",
                ),
                "model": os.getenv(
                    "VANNA_GROQ_MODEL",
                    "openai/gpt-oss-120b",
                ),
            }
        )

    return _instance
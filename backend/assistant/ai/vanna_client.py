"""
KSP Insight AI (KAVACH AI) — Vanna Client
App: assistant / ai

Uses Vanna's LEGACY (pre-2.0) mixin API deliberately — see the note in
chat about why: Vanna 2.0 is its own full agent framework, and we
already have one (the LangChain orchestrator). We only want Vanna's
text-to-SQL generation, nothing else, so this wraps just that.

We NEVER call vn.ask() or vn.run_sql() here — only vn.generate_sql().
The generated SQL is untrusted output; it gets passed to
assistant/ai/sql_scope.py's validate_and_scope() before anything
touches the real database. See tools.py's security contract.

pip install "vanna<2.0" chromadb groq
"""

import os

from vanna.chromadb import ChromaDB_VectorStore
from vanna.base import VannaBase
from groq import Groq


class _GroqLLM(VannaBase):
    """Legacy Vanna's documented pattern for plugging in a custom LLM —
    implement system_message/user_message/assistant_message/submit_prompt,
    same shape as their own mistral.py reference implementation."""

    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)
        self.client = Groq(api_key=(config or {}).get("api_key") or os.environ["GROQ_API_KEY"])
        self.model = (config or {}).get("model", "openai/gpt-oss-120b")

    def system_message(self, message: str) -> dict:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> dict:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            temperature=0.0,  # SQL generation should be deterministic, not creative
        )
        return response.choices[0].message.content


class KavachVanna(ChromaDB_VectorStore, _GroqLLM):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        _GroqLLM.__init__(self, config=config)


_instance = None


def get_vanna() -> KavachVanna:
    """Singleton — avoids reloading the ChromaDB collection on every
    call. persist_directory should be a real path on disk that survives
    restarts; train_vanna.py (management command) writes to the same
    path so training persists across server restarts."""
    global _instance
    if _instance is None:
        _instance = KavachVanna(config={
            "path": os.environ.get("VANNA_CHROMA_PATH", "./vanna_chroma_store"),
            "model": os.environ.get("VANNA_GROQ_MODEL", "openai/gpt-oss-120b"),
        })
    return _instance
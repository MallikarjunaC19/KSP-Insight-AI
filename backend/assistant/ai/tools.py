"""
KSP Insight AI (KAVACH AI) — Assistant AI Tools
App: assistant / ai

CONSOLIDATED VERSION — reverted from Gemini back to Groq across every
tool. bhashini (Sarvam AI) is untouched by this — Sarvam is a separate
translation/TTS provider, unrelated to which LLM does reasoning.

Status:
  sql_lookup     — REAL (Vanna + sql_scope.py RBAC injection, Groq via vanna_client.py)
  graph_lookup   — REAL (intent classification + pre-written Cypher templates, never LLM-written Cypher) — Groq
  quickml        — REAL (Zoho Catalyst QuickML, 4 models, Production environment, retry-with-backoff) — Groq for intent classification
  bhashini       — REAL (Sarvam AI: Mayura text translate + Bulbul v3 TTS) — unchanged, not LLM-provider-dependent
  general_answer — REAL (plain Groq call, no DB access)
"""

import json
import os
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from django.db import connection

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from assistant.ai.vanna_client import get_vanna
from assistant.ai.sql_scope import validate_and_scope, UnsafeQueryError
from assistant.ai.graph_templates import TEMPLATES
from assistant.ai.quickml_client import predict as quickml_predict
from assistant.models import PredictionHistory
from accounts.permissions import filter_by_station_field
from persons.models import Person
from investigations.models import InvestigationCase
from django.conf import settings
from assistant.ai.sarvam_client import (
    translate_kannada_text_to_english,
    translate_english_to_kannada_text,
    synthesize_kannada_speech,
)

@dataclass
class ToolResult:
    """Every tool returns this shape so the orchestrator can log a
    consistent execution trace into ChatMessage.metadata regardless of
    which tool ran."""
    answer: str
    tool_name: str
    raw_query: Optional[str] = None
    source: Optional[str] = None
    row_count: Optional[int] = None


# ---------------------------------------------------------------------
# sql_lookup — REAL
# ---------------------------------------------------------------------

MAX_ROWS_RETURNED = 20
MAX_INTERMEDIATE_STEPS = 3


_SQL_START_RE = re.compile(r'^\s*(--.*\n\s*)?(SELECT|WITH)\b', re.IGNORECASE)

def _format_results(columns, rows) -> str:
    if not rows:
        return "No matching records found."
    if len(rows) == 1 and len(columns) == 1:
        return f"{columns[0]}: {rows[0][0]}"
    lines = [" | ".join(columns)]
    for row in rows[:MAX_ROWS_RETURNED]:
        lines.append(" | ".join(str(v) for v in row))
    if len(rows) > MAX_ROWS_RETURNED:
        lines.append(f"... and {len(rows) - MAX_ROWS_RETURNED} more row(s)")
    return "\n".join(lines)


def _looks_like_sql(text: str) -> bool:
    return bool(text) and bool(_SQL_START_RE.match(text))


def _run_scoped(sql: str, officer):
    """Runs any SELECT through the same RBAC scoping + read-only path.
    Raises UnsafeQueryError (RBAC rejection) or lets DB exceptions propagate."""
    scoped_sql = validate_and_scope(sql, officer)
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute(scoped_sql)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall() if cursor.description else []
    return scoped_sql, columns, rows



def make_sql_lookup_tool(officer, trace_sink: list):
    vn = get_vanna()

    @tool
    def sql_lookup(question: str) -> str:
        """Answer questions about structured crime-database records:
        crimes, FIRs, officers, arrests, chargesheets, court cases —
        anything that's a row in a Postgres table. Use this for
        questions like 'how many FIRs were filed this month at my
        station' or 'list open cases assigned to me'."""
        try:
            generated_sql = vn.generate_sql(question, allow_llm_to_see_data=False)
        except Exception as exc:
            return f"Couldn't generate a query for that question: {exc}"

        current_question = question
        for _ in range(MAX_INTERMEDIATE_STEPS):
            if not _looks_like_sql(generated_sql):
                return generated_sql or "I couldn't generate a query for that question."

            if 'intermediate_sql' not in generated_sql.lower():
                break

            intermediate_query = re.sub(
                r'^\s*--.*intermediate_sql.*\n', '', generated_sql, flags=re.IGNORECASE
            ).strip()
            try:
                _, _, intermediate_rows = _run_scoped(intermediate_query, officer)
            except UnsafeQueryError as exc:
                return f"That question couldn't be safely scoped to your access level ({exc}). Try rephrasing it."
            except Exception as exc:
                return f"Couldn't resolve the values needed for that question: {exc}"

            distinct_values = ", ".join(str(row[0]) for row in intermediate_rows[:50])
            current_question = f"{current_question}\n\n(Known column values: {distinct_values})"
            try:
                generated_sql = vn.generate_sql(current_question, allow_llm_to_see_data=False)
            except Exception as exc:
                return f"Couldn't generate a query for that question: {exc}"
        else:
            return "Couldn't resolve that question after checking the relevant column values. Try rephrasing it more specifically."

        try:
            scoped_sql, columns, rows = _run_scoped(generated_sql, officer)
        except UnsafeQueryError as exc:
            return f"That question couldn't be safely scoped to your access level ({exc}). Try rephrasing it."
        except Exception as exc:
            return f"That query failed to run: {exc}"

        summary = _format_results(columns, rows)
        trace_sink.append({
            "tool": "sql_lookup",
            "executed_sql": scoped_sql,
            "row_count": len(rows),
        })
        return summary

    return sql_lookup

# ---------------------------------------------------------------------
# graph_lookup — REAL
# ---------------------------------------------------------------------

_INTENT_SYSTEM_PROMPT = """You classify a police officer's question into ONE of these intents
and extract the entity it's asking about. Respond with ONLY valid JSON, no other text.

Intents:
- "associates_of_person": who is X connected/associated with
- "vehicles_of_person": what vehicles does X own
- "people_in_case": who are the suspects/victims/witnesses in case X
- "other_cases_for_person": is X linked to any other cases
- "case_network": full picture / network around case X
- "unknown": doesn't match any of the above, or missing a clear entity name/case number

JSON shape:
{"intent": "<one of the above>", "person_name": "<name or null>", "case_number": "<case number or null>"}

Examples:
Q: "Who is Rajesh Kumar connected to?"
A: {"intent": "associates_of_person", "person_name": "Rajesh Kumar", "case_number": null}

Q: "Show me the network around case CR-2026-00104"
A: {"intent": "case_network", "person_name": null, "case_number": "CR-2026-00104"}

Q: "What's the weather today?"
A: {"intent": "unknown", "person_name": null, "case_number": null}
"""


def _format_graph_results(intent: str, results: list) -> str:
    if intent == "associates_of_person":
        names = sorted({r["associate_name"] for r in results})
        return "Associated with: " + ", ".join(names)
    if intent == "vehicles_of_person":
        regs = [r["registration_number"] for r in results]
        return "Vehicles owned: " + ", ".join(regs) if regs else "No vehicles found."
    if intent == "people_in_case":
        lines = [f"{r['person_name']} ({r['role'].replace('_', ' ').title()})" for r in results]
        return "People in this case: " + "; ".join(lines)
    if intent == "other_cases_for_person":
        lines = [f"{r['case_number']} ({r['role'].replace('_', ' ').title()}, {r['status']})" for r in results]
        return "Other cases linked to this person: " + "; ".join(lines)
    if intent == "case_network":
        lines = []
        for r in results:
            vehicles = ", ".join(v for v in r["vehicles"] if v) or "no known vehicles"
            lines.append(f"{r['person_name']} ({r['role'].replace('_', ' ').title()}) — {vehicles}")
        return "Case network: " + "; ".join(lines)
    return str(results)


def make_graph_lookup_tool(officer):
    groq_client = Groq()

    @tool
    def graph_lookup(question: str) -> str:
        """Answer questions about relationships/connections between
        people, vehicles, and cases — e.g. 'who is connected to this
        suspect', 'what other cases involve this vehicle'. Use this for
        network/association questions, not simple record lookups."""

        try:
            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0,
            )
            parsed = json.loads(completion.choices[0].message.content)
        except Exception as exc:
            return f"Couldn't understand that as a network/relationship question: {exc}"

        intent = parsed.get("intent")
        if intent not in TEMPLATES:
            return (
                "That doesn't look like a network/relationship question I can answer "
                "from the graph database. Try asking about a person's connections or "
                "a case's network."
            )

        person_pg_id = None
        case_pg_id = None

        if parsed.get("person_name"):
            name_parts = parsed["person_name"].split()
            people_qs = Person.objects.all()
            for part in name_parts:
                people_qs = people_qs.filter(first_name__icontains=part) | people_qs.filter(last_name__icontains=part)
            person = people_qs.first()
            if person is None:
                return f"I couldn't find a person matching '{parsed['person_name']}' in the records."
            person_pg_id = str(person.id)

        if parsed.get("case_number"):
            cases_qs = filter_by_station_field(
                InvestigationCase.objects.filter(case_number=parsed["case_number"]),
                officer, station_field="fir__police_station",
            )
            case = cases_qs.first()
            if case is None:
                return f"I couldn't find case {parsed['case_number']} in your accessible records."
            case_pg_id = str(case.id)

        template_fn = TEMPLATES[intent]
        try:
            if intent in ("associates_of_person", "vehicles_of_person", "other_cases_for_person"):
                results = template_fn(officer, person_pg_id)
            else:
                results = template_fn(officer, case_pg_id)
        except Exception as exc:
            return f"That graph query failed to run: {exc}"

        if not results:
            summary = "No connections found in the graph database for that query, within your access scope."
        else:
            summary = _format_graph_results(intent, results)

        return f"{summary}\n\n[graph intent: {intent}]"

    return graph_lookup


# ---------------------------------------------------------------------
# quickml — REAL
# ---------------------------------------------------------------------

_QUICKML_INTENT_PROMPT = """You classify a police officer's question into ONE of these 4 prediction models
and extract whatever feature values are mentioned in the question. Respond with ONLY valid JSON.

Models and their features:
- "severity": crime_type, weapon_used (true/false), victim_count, property_damage, hour (0-23), district
- "solvability": evidence_count, witness_count, suspect_identified (true/false), cctv_available (true/false), crime_type, response_time (minutes)
- "priority": severity (Low/Medium/High/Critical), victim_count, investigation_days, crime_type, evidence_count
- "hotspot": latitude, longitude, police_station, district, crime_category, day_of_week, month, hour

If a feature isn't mentioned, use null for it in the "features" dict — do not guess.
If the question doesn't match any of these 4 models, use "model_key": "unknown".

JSON shape:
{"model_key": "<severity|solvability|priority|hotspot|unknown>", "features": {...}}

Example:
Q: "How severe is a robbery with a weapon and 2 victims around 11pm in Bengaluru Urban?"
A: {"model_key": "severity", "features": {"crime_type": "Robbery", "weapon_used": true, "victim_count": 2, "property_damage": null, "hour": 23, "district": "Bengaluru Urban"}}
"""

_DEFAULTS = {
    "weapon_used": False, "victim_count": 1, "property_damage": 0, "hour": 12,
    "evidence_count": 1, "witness_count": 0, "suspect_identified": False,
    "cctv_available": False, "response_time": 20, "investigation_days": 5,
    "crime_type": "Robbery",
    "district": "Bengaluru Urban",
    "severity": "Medium",
    "police_station": "Cubbon Park PS",
    "crime_category": "Robbery",
    "day_of_week": "Monday",
    "month": 7,
    "latitude": 12.9716,
    "longitude": 77.5946,
}


def make_quickml_tool(officer, trace_sink: list):
    groq_client = Groq()

    @tool
    def quickml(question: str) -> str:
        """Answer predictive/analytical questions — crime severity,
        case solvability, investigation priority, or crime hotspot
        risk. Use this for questions like 'how severe would this
        incident be' or 'is this area becoming a hotspot'. Does not
        answer simple record lookups — use sql_lookup for those."""

        try:
            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": _QUICKML_INTENT_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0,
            )
            parsed = json.loads(completion.choices[0].message.content)
        except Exception as exc:
            return f"Couldn't understand that as a prediction question: {exc}"

        model_key = parsed.get("model_key")
        if model_key not in ("severity", "solvability", "priority", "hotspot"):
            return (
                "That doesn't look like a question I can run through the prediction models. "
                "Try asking about crime severity, case solvability, investigation priority, "
                "or hotspot risk."
            )

        features = {k: (v if v is not None else _DEFAULTS.get(k)) for k, v in parsed.get("features", {}).items()}
        used_defaults = [k for k, v in parsed.get("features", {}).items() if v is None and k in _DEFAULTS]

        result = None
        last_exc = None
        for attempt in range(5):  # widened — Zoho can stay flaky for several seconds
            try:
                result = quickml_predict(model_key, features)
                break
            except Exception as exc:
                last_exc = exc
                if attempt < 4:
                    time.sleep(2 * (attempt + 1))  # 2s, 4s, 6s, 8s

        if result is None:
            return (
                f"The prediction service is temporarily unavailable after "
                f"5 attempts ({last_exc}). Please try again in a moment."
            )

        classification = result.get("result")
        likelihood = result.get("likelihood_score")
        if isinstance(classification, list):
            classification = classification[0] if classification else "unknown"
        if isinstance(likelihood, list):
            likelihood = round(likelihood[0] * 100, 1) if likelihood else "?"

        explanation_summary = ""
        top_factors = []
        explanation_rows = result.get("explanation", {}).get("data", [])
        if explanation_rows:
            top_rows = sorted(explanation_rows, key=lambda row: abs(row[2]), reverse=True)[:3]
            factor_lines = []
            encoded_feature_seen = False
            for name, value, impact in top_rows:
                direction = "supports" if impact > 0 else "against"
                is_encoded = any(name.endswith(f"_{i}") for i in range(1, 20)) and name.split("_")[-1].isdigit()
                if is_encoded:
                    encoded_feature_seen = True
                factor_lines.append(f"{name}={value} ({direction} {classification}, impact {impact:+.3f})")
                top_factors.append({
                    "feature": name, "value": value, "impact": impact, "encoded": is_encoded,
                })
            explanation_summary = "\nTop contributing factors: " + "; ".join(factor_lines)
            if encoded_feature_seen:
                explanation_summary += (
                    "\n(Some factor names are internal encoded categories, not directly "
                    "human-readable without the model's category mapping.)"
                )

        prediction_type_map = {
            "hotspot": PredictionHistory.PredictionType.CRIME_HOTSPOT,
            "severity": PredictionHistory.PredictionType.RISK_SCORE,
            "solvability": PredictionHistory.PredictionType.RISK_SCORE,
            "priority": PredictionHistory.PredictionType.RISK_SCORE,
        }
        prediction_record = PredictionHistory.objects.create(
            officer=officer,
            prediction_type=prediction_type_map[model_key],
            input_parameters=features,
            output_result=result,
            confidence_score=(likelihood / 100 if isinstance(likelihood, (int, float)) else None),
        )

        trace_sink.append({
            "tool": "quickml",
            "model": model_key,
            "prediction": classification,
            "confidence": likelihood,
            "top_factors": top_factors,
            "used_defaults": used_defaults,
            "prediction_history_id": str(prediction_record.id),
        })

        caveat = f" (defaults used for: {', '.join(used_defaults)})" if used_defaults else ""
        return (
            f"Predicted {model_key}: {classification} ({likelihood}% confidence){caveat}"
            f"{explanation_summary}\n\n"
            f"[quickml model: {model_key}, features: {features}]"
        )

    return quickml

# ---------------------------------------------------------------------
# bhashini — REAL (Sarvam AI)
# ---------------------------------------------------------------------

def make_bhashini_tool(officer):
    """Kannada <-> English via Sarvam AI (Mayura text translate,
    Bulbul v3 TTS). Named bhashini for backward compatibility with the
    orchestrator's tool list. NOTE: speech-to-text is NOT handled here —
    audio is transcribed to English before the agent runs (see
    transcribe_speech_to_english() called from views.py's send-message
    action), so this tool only ever receives text."""

    @tool
    def bhashini(text_or_audio_ref: str) -> str:
        """Translate between Kannada and English, or speak a response in
        Kannada. Input routing:
        - Text containing Kannada script is translated to English.
        - Text prefixed with "text:" is translated to Kannada TEXT.
        - Plain English text (no prefix) is converted to spoken Kannada
        audio by default.
        """
        is_kannada_script = any(
            '\u0C80' <= ch <= '\u0CFF' for ch in text_or_audio_ref
        )

        if is_kannada_script:
            try:
                english_text = translate_kannada_text_to_english(text_or_audio_ref)
            except Exception as exc:
                return f"Couldn't translate that text: {exc}"
            return f"Translated (Kannada -> English): {english_text}"

        if text_or_audio_ref.startswith("text:"):
            english_source = text_or_audio_ref[len("text:"):].strip()
            try:
                kannada_text = translate_english_to_kannada_text(english_source)
            except Exception as exc:
                return f"Couldn't translate that text: {exc}"
            return f"Kannada text: {kannada_text}"

        try:
            audio_relpath = synthesize_kannada_speech(text_or_audio_ref, settings.MEDIA_ROOT)
        except Exception as exc:
            return f"Couldn't generate Kannada speech: {exc}"
        audio_url = settings.MEDIA_URL + audio_relpath
        return f"Kannada audio response generated: {audio_url}"

    return bhashini

# ---------------------------------------------------------------------
# general_answer — REAL
# ---------------------------------------------------------------------

def make_general_answer_tool(officer, model: str = "openai/gpt-oss-120b"):
    """Real, working tool — plain LLM call for definitional/
    conversational questions that don't need the database."""
    llm = ChatGroq(model=model, temperature=0.2)

    @tool
    def general_answer(question: str) -> str:
        """Answer general/conversational/definitional questions that
        don't require looking anything up in the crime database or
        graph — legal section meanings, how-to questions about using
        the system, general explanations."""
        response = llm.invoke(question)
        return response.content

    return general_answer
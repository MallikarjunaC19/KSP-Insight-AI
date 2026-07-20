"""
KSP Insight AI (KAVACH AI) — Assistant AI Tools
App: assistant / ai

CONSOLIDATED VERSION — all four real tool implementations in one file,
to eliminate the splice-drift that caused quickml's stub to stay active
even after quickml_client.py was updated. This is now the single
authoritative version of tools.py.

Status:
  sql_lookup     — REAL (Vanna + sql_scope.py RBAC injection)
  graph_lookup   — REAL (intent classification + pre-written Cypher templates, never LLM-written Cypher)
  quickml        — REAL (Zoho Catalyst QuickML, 4 models, confirmed working with {"data": {...}} payload wrapper)
  bhashini       — STUB (Kannada STT/TTS, not yet implemented)
  general_answer — REAL (plain Groq call, no DB access)
"""

import json
from dataclasses import dataclass
from typing import Optional

from django.db import connection

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from groq import Groq

from assistant.ai.vanna_client import get_vanna
from assistant.ai.sql_scope import validate_and_scope, UnsafeQueryError
from assistant.ai.graph_templates import TEMPLATES
from assistant.ai.quickml_client import predict as quickml_predict
from assistant.models import PredictionHistory
from accounts.permissions import filter_by_station_field
from persons.models import Person
from investigations.models import InvestigationCase


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

        try:
            scoped_sql = validate_and_scope(generated_sql, officer)
        except UnsafeQueryError as exc:
            return f"That question couldn't be safely scoped to your access level ({exc}). Try rephrasing it."

        try:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(scoped_sql)
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = cursor.fetchall() if cursor.description else []
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
}


def make_quickml_tool(officer):
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

        try:
            result = quickml_predict(model_key, features)
        except Exception as exc:
            return f"Prediction request failed: {exc}"

        classification = result.get("result")
        likelihood = result.get("likelihood_score")
        if isinstance(classification, list):
            classification = classification[0] if classification else "unknown"
        if isinstance(likelihood, list):
            likelihood = round(likelihood[0] * 100, 1) if likelihood else "?"

        # Explainability: Catalyst returns a SHAP-style per-feature impact
        # score in explanation.data — [feature_name, feature_value, impact].
        # Positive impact pushed toward the predicted label, negative
        # pushed away. This was being silently discarded before; now
        # surfaced as the top 3 contributing factors so the officer sees
        # WHY the model said what it said, not just the label.
        #
        # Caveat, stated plainly rather than hidden: one-hot-encoded
        # categorical features (e.g. "crime_type_6") don't map back to a
        # human-readable category name without the model's original
        # encoding table, which isn't available here — those show up
        # as-is rather than translated, and that's flagged in the output
        # itself when it happens, not silently presented as if it were
        # a clean answer.
        explanation_summary = ""
        explanation_rows = result.get("explanation", {}).get("data", [])
        if explanation_rows:
            top_factors = sorted(explanation_rows, key=lambda row: abs(row[2]), reverse=True)[:3]
            factor_lines = []
            encoded_feature_seen = False
            for name, value, impact in top_factors:
                direction = "supports" if impact > 0 else "against"
                if any(name.endswith(f"_{i}") for i in range(1, 20)) and name.split("_")[-1].isdigit():
                    encoded_feature_seen = True
                factor_lines.append(f"{name}={value} ({direction} {classification}, impact {impact:+.3f})")
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
        PredictionHistory.objects.create(
            officer=officer,
            prediction_type=prediction_type_map[model_key],
            input_parameters=features,
            output_result=result,
            confidence_score=(likelihood / 100 if isinstance(likelihood, (int, float)) else None),
        )

        caveat = f" (defaults used for: {', '.join(used_defaults)})" if used_defaults else ""
        return (
            f"Predicted {model_key}: {classification} ({likelihood}% confidence){caveat}"
            f"{explanation_summary}\n\n"
            f"[quickml model: {model_key}, features: {features}]"
        )

    return quickml


# ---------------------------------------------------------------------
# bhashini — STUB
# ---------------------------------------------------------------------

def make_bhashini_tool(officer):
    """STUB — Kannada STT/TTS via Bhashini API."""
    @tool
    def bhashini(text_or_audio_ref: str) -> str:
        """Translate or transcribe between Kannada and English — use
        this when the officer is speaking/writing in Kannada and needs
        it converted before another tool can act on it, or when a
        response needs to go back to them in Kannada."""
        return (
            "[bhashini_tool is not implemented yet — this is a stub. "
            "Wire this up to the Bhashini API for Kannada STT/TTS.]"
        )

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
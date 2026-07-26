"""
assistant/ai/sarvam_client.py
Sarvam AI STT-translate (Kannada/English/code-mixed speech -> English text)
+ text translate (Kannada text -> English) + TTS (English -> Kannada speech).

Required in .env:
    SARVAM_API_KEY=...
"""
import os
import uuid
import base64
from pathlib import Path

from sarvamai import SarvamAI

_client = None


def get_sarvam() -> SarvamAI:
    global _client
    if _client is None:
        _client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
    return _client


def transcribe_speech_to_english(audio_path: str) -> str:
    """Any supported spoken language (Kannada, English, or code-mixed)
    -> English text, one REST call. Auto-detects source language.
    NOTE: this is client.speech_to_text.translate(), NOT
    client.speech_to_text_translate — that attribute is job/batch-only."""
    client = get_sarvam()
    with open(audio_path, "rb") as f:
        response = client.speech_to_text.translate(file=f)
    # Confirm field name against a real response — likely .transcript
    return response.transcript


def translate_kannada_text_to_english(text: str) -> str:
    """Kannada script text -> English text."""
    client = get_sarvam()
    response = client.text.translate(
        input=text,
        source_language_code="kn-IN",
        target_language_code="en-IN",
        model="mayura:v1",
    )
    return response.translated_text


def synthesize_kannada_speech(text: str, media_root: str) -> str:
    """English text -> Kannada speech audio file. Returns a path under media_root."""
    client = get_sarvam()
    response = client.text_to_speech.convert(
        text=text,
        target_language_code="kn-IN",
        model="bulbul:v3",
    )
    audio_bytes = base64.b64decode(response.audios[0])

    filename = f"kavach_tts_{uuid.uuid4().hex}.wav"
    out_path = Path(media_root) / "tts" / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio_bytes)
    return f"tts/{filename}"


def translate_english_to_kannada_text(text: str) -> str:
    """English text -> Kannada script text (no audio)."""
    client = get_sarvam()
    response = client.text.translate(
        input=text,
        source_language_code="en-IN",
        target_language_code="kn-IN",
        model="mayura:v1",
    )
    return response.translated_text
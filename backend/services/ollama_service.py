import ollama
import json
import re

OLLAMA_MODEL = "llama3"   # Change to "mistral" or "gemma" if preferred


def _chat(prompt: str, system: str = "") -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"].strip()


def translate_to_english(text: str, source_language: str = "auto") -> dict:
    """
    Translate complaint text to English.
    Returns: { translated_text, source_language_name }
    """
    system = (
        "You are a professional multilingual translator specializing in government complaints. "
        "Translate the input text accurately to English. "
        "Preserve all factual details, names, locations, and dates. "
        "Respond ONLY with a JSON object: {\"translated\": \"...\", \"source_lang_name\": \"...\"}"
    )
    prompt = f"Translate this text to English:\n\n{text}"
    raw = _chat(prompt, system)

    try:
        clean = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(clean)
        return {
            "translated_text": data.get("translated", text),
            "source_language_name": data.get("source_lang_name", source_language),
        }
    except Exception:
        return {"translated_text": raw, "source_language_name": source_language}


def generate_summary(translated_text: str, category: str, department: str) -> str:
    """
    Generate a concise structured summary for the complaint report.
    """
    system = (
        "You are a government complaint officer. "
        "Write a formal, concise structured summary for an official complaint record. "
        "Include: issue description, location if mentioned, urgency indicators, and recommended action. "
        "Keep it under 200 words. Plain text only."
    )
    prompt = (
        f"Category: {category}\n"
        f"Department: {department}\n\n"
        f"Complaint text:\n{translated_text}\n\n"
        "Write the official summary:"
    )
    return _chat(prompt, system)


def assess_priority(translated_text: str) -> str:
    """
    Use LLM to assess complaint urgency: low | medium | high | urgent
    """
    system = (
        "You assess the urgency of government complaints. "
        "Reply ONLY with one word: low, medium, high, or urgent. "
        "urgent = threat to life/safety. high = significant public impact. "
        "medium = service disruption. low = general feedback."
    )
    result = _chat(translated_text, system).lower().strip()
    valid = {"low", "medium", "high", "urgent"}
    return result if result in valid else "medium"

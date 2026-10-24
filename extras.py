"""Extra AI helpers for the LabelLens app: nutrition facts and the chat assistant.

Does NOT change analyze_label or the contract. Uses the same GEMINI_API_KEY and core.MODEL_NAME.
Every function returns a dict and never raises.
"""
import json
import os
import re

import core

KEYS = ["calories", "sugar_g", "added_sugar_g", "sodium_mg", "sat_fat_g", "fat_g", "carbs_g", "protein_g", "fiber_g"]
MEALS = ["Breakfast", "Lunch", "Snack", "Dinner"]

FACTS_PROMPT = (
    "You read a product label photo. Return ONLY JSON, no other text: "
    '{"product_name": str or null, "serving_size": str or null, '
    '"per_serving": {"calories": n, "sugar_g": n, "added_sugar_g": n, "sodium_mg": n, "sat_fat_g": n, '
    '"fat_g": n, "carbs_g": n, "protein_g": n, "fiber_g": n}, '
    '"claim_checks": [{"claim": str, "finding": str, "level": "ok" or "note" or "warn"}], '
    '"concerning": [{"name": str, "why": str}]}. '
    "Rules: use ONLY what is printed on the label. If a number is not printed, use null. Never estimate. "
    "If the table is per 100 g/ml and a serving size is printed, convert exactly; otherwise use null. "
    "claim_checks: take each front-of-pack claim (for example '100% juice', 'no added sugar', 'natural', 'healthy') "
    "and compare it with the printed ingredient list and nutrition table. In finding, say what the printed text shows "
    "and quote the words. Never invent percentages or hidden ingredients. If nothing printed contradicts the claim, level is ok. "
    "concerning: only items actually printed (added sugars, sweeteners, colours, preservatives, E-numbers, palm oil, high sodium). "
    "why = one short, hedged sentence of general knowledge. Write in English."
)

CHAT_PROMPT = (
    "You are LabelLens Assistant, a warm helper for everyone, from children to elders, with any level of education. "
    "Reply in the language the user writes in, in short plain sentences. "
    "For questions about today's intake or the last scan, use the numbers in CONTEXT and never invent numbers that are not there. "
    "You can explain labels, nutrition and healthy swaps. Never diagnose, never give a medicine or pesticide dose; "
    "for symptoms or medical conditions tell the user to ask a doctor or pharmacist. "
    "If the user says they ate or drank something, or asks to log it, estimate typical values for one normal serving, "
    "put them in 'log', and say in the reply that these are estimates. Otherwise log is null. "
    'Return ONLY JSON: {"reply": str, "log": null or {"name": str, "meal": "Breakfast" or "Lunch" or "Snack" or "Dinner", '
    '"kcal": number, "sugar": number, "sodium": number, "sat": number}} '
    "where sugar and sat are grams and sodium is milligrams."
)


def _num(x, hi=100000):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v or v < 0 or v > hi:
        return None
    return round(v, 1)


def _s(x, n):
    return None if x is None else str(x)[:n]


def _scrub(msg):
    key = os.environ.get("GEMINI_API_KEY", "")
    msg = str(msg)
    return (msg.replace(key, "***") if key else msg)[:200]


def _call_json(parts):
    from google import genai

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    last = None
    for _ in range(2):
        try:
            text = client.models.generate_content(model=core.MODEL_NAME, contents=parts).text or ""
            text = re.sub(r"```(?:json)?", "", text).strip()
            return json.loads(text[text.find("{"): text.rfind("}") + 1])
        except Exception as exc:
            last = exc
    raise RuntimeError(_scrub(last))


def facts(raw, mime, profile):
    try:
        from google.genai import types

        d = _call_json([types.Part.from_bytes(data=raw, mime_type=mime),
                        FACTS_PROMPT + "\nProfile: " + str(profile)[:200]])
        ps = d.get("per_serving") if isinstance(d.get("per_serving"), dict) else {}
        checks = []
        for x in list(d.get("claim_checks") or [])[:6]:
            if isinstance(x, dict) and x.get("claim"):
                lv = x.get("level") if x.get("level") in ("ok", "note", "warn") else "note"
                checks.append({"claim": _s(x.get("claim"), 120), "finding": _s(x.get("finding"), 300), "level": lv})
        conc = []
        for x in list(d.get("concerning") or [])[:8]:
            if isinstance(x, dict) and x.get("name"):
                conc.append({"name": _s(x.get("name"), 80), "why": _s(x.get("why"), 200)})
        return {"product_name": _s(d.get("product_name"), 80), "serving_size": _s(d.get("serving_size"), 40),
                "per_serving": {k: _num(ps.get(k)) for k in KEYS}, "claim_checks": checks, "concerning": conc}
    except Exception as exc:
        return {"error": _scrub(exc)}


def chat(messages, context):
    try:
        lines = []
        for m in (messages if isinstance(messages, list) else [])[-8:]:
            if isinstance(m, dict):
                who = "User" if m.get("role") == "user" else "Assistant"
                lines.append(f"{who}: {str(m.get('content', ''))[:800]}")
        ctx = json.dumps(context if isinstance(context, dict) else {}, ensure_ascii=False)[:6000]
        d = _call_json([CHAT_PROMPT + "\nCONTEXT: " + ctx + "\n\nCONVERSATION:\n" + "\n".join(lines) + "\nAssistant (JSON only):"])
        lg, log = d.get("log"), None
        if isinstance(lg, dict) and lg.get("name"):
            log = {"name": str(lg["name"])[:80], "meal": lg.get("meal") if lg.get("meal") in MEALS else "Snack",
                   "kcal": round(_num(lg.get("kcal")) or 0), "sugar": _num(lg.get("sugar")) or 0,
                   "sodium": round(_num(lg.get("sodium")) or 0), "sat": _num(lg.get("sat")) or 0}
        return {"reply": str(d.get("reply") or "")[:1500], "log": log}
    except Exception as exc:
        return {"reply": "", "log": None, "error": _scrub(exc)}

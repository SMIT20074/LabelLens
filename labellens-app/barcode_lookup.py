"""Fast path: barcode -> Open Food Facts -> rule-based verdict. No AI call, no key.

Typical time: well under 2 seconds (cached repeats are instant).
Verdict rules live here in plain code, so they are easy to explain to judges.
"""
import json
import time
import urllib.request

UA = "LabelLens/1.0 (hackathon project; github.com/SMIT20074/LabelLens)"
FIELDS = ("product_name,brands,quantity,nutriscore_grade,nova_group,ingredients_text,"
          "allergens_tags,traces_tags,additives_tags,nutriments,image_front_small_url")
CACHE = {}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _valid(code):
    if not code.isdigit() or len(code) not in (8, 12, 13):
        return False
    d = [int(c) for c in code]
    check = d.pop()
    total = sum(x * (3 if i % 2 == 0 else 1) for i, x in enumerate(reversed(d)))
    return (10 - total % 10) % 10 == check


def _fetch(code):
    url = f"https://world.openfoodfacts.org/api/v2/product/{code}.json?fields={FIELDS}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("product") if data.get("status") == 1 else None


def judge(p, profile):
    prof = (profile or "adult").lower()
    n = p.get("nutriments") or {}
    sugar, salt, sat = _f(n.get("sugars_100g")), _f(n.get("salt_100g")), _f(n.get("saturated-fat_100g"))
    ing = (p.get("ingredients_text") or "").lower()
    allergens = {t.split(":")[-1] for t in (p.get("allergens_tags") or [])}
    traces = {t.split(":")[-1] for t in (p.get("traces_tags") or [])}
    level, reasons, tips = 0, [], []

    def bump(lv, msg):
        nonlocal level
        level = max(level, lv)
        reasons.append(msg)

    if "peanut" in prof or "nut" in prof:
        if allergens & {"peanuts", "nuts"} or "peanut" in ing:
            bump(2, "The database lists peanuts or nuts in this product.")
        elif traces & {"peanuts", "nuts"}:
            bump(1, "It may contain traces of peanuts or nuts.")
    for word, tags in (("gluten", {"gluten"}), ("milk", {"milk"}), ("dairy", {"milk"}),
                       ("lactose", {"milk"}), ("egg", {"eggs"}), ("soy", {"soybeans"})):
        if word in prof:
            if allergens & tags:
                bump(2, f"The database lists {word} in this product.")
            elif traces & tags:
                bump(1, f"It may contain traces of {word}.")
    if "diabet" in prof and sugar is not None:
        if sugar >= 15:
            bump(2, f"Very high sugar: {sugar:g} g per 100 g.")
        elif sugar >= 5:
            bump(1, f"Moderate sugar: {sugar:g} g per 100 g.")
    if ("pregnan" in prof or "lactat" in prof or "nursing" in prof) and "caffeine" in ing:
        bump(1, "Contains caffeine. Ask your doctor what is right for you.")
    if ("child" in prof or "kid" in prof) and "caffeine" in ing:
        bump(1, "Contains caffeine, which is not suited to young children.")
    if "elder" in prof and salt is not None and salt >= 1.5:
        bump(1, f"High salt: {salt:g} g per 100 g.")
    if sugar is not None and sugar >= 22.5:
        bump(1, f"High sugar: {sugar:g} g per 100 g.")
    if salt is not None and salt >= 1.5:
        bump(1, f"High salt: {salt:g} g per 100 g.")
    if sat is not None and sat >= 5:
        bump(1, f"High saturated fat: {sat:g} g per 100 g.")
    if (p.get("nutriscore_grade") or "").lower() in ("d", "e"):
        bump(1, f"Nutri-Score {p['nutriscore_grade'].upper()} (a weaker nutrition grade).")
    if not n:
        bump(1, "The database has no nutrition numbers for this product.")
    if not reasons:
        reasons.append("Nothing in the database entry conflicts with this profile. Not a guarantee of safety.")

    if sugar is not None and sugar >= 10:
        tips.append("Look for a version with less sugar, or share one serving.")
    if "caffeine" in ing:
        tips.append("Keep caffeine away from bedtime.")
    if salt is not None and salt >= 1.5:
        tips.append("Compare brands and pick the lower-salt one.")
    if p.get("nova_group") == 4:
        tips.append("Heavily processed food: scan the ingredient list for additives you want to skip.")
    tips.append("Databases can be out of date. Check the real label too.")
    return ["OK", "CAREFUL", "AVOID"][level], reasons, tips


def build(p, profile, code):
    n = p.get("nutriments") or {}
    per = {}
    for label, key, unit in (("calories", "energy-kcal_100g", "kcal"), ("sugar", "sugars_100g", "g"),
                             ("fat", "fat_100g", "g"), ("saturated fat", "saturated-fat_100g", "g"),
                             ("salt", "salt_100g", "g"), ("protein", "proteins_100g", "g")):
        v = _f(n.get(key))
        if v is not None:
            per[label] = f"{v:g} {unit}"
    verdict, reasons, tips = judge(p, profile)
    adds = [t.split(":")[-1].upper() for t in (p.get("additives_tags") or [])][:8]
    name = p.get("product_name") or f"Barcode {code}"
    return {"product": {"brand": (p.get("brands") or "").split(",")[0], "name": name, "per_100g": per,
                        "nutriscore": (p.get("nutriscore_grade") or "").upper(), "additives": adds,
                        "ingredients_text": p.get("ingredients_text") or "",
                        "image": p.get("image_front_small_url") or ""},
            "verdict": verdict, "reasons": reasons, "suggestions": tips,
            "source": "Open Food Facts (barcode)", "guess": name}


def lookup(body):
    t0 = time.time()
    code = "".join(c for c in str((body or {}).get("code", "")) if c.isdigit())
    profile = str((body or {}).get("profile") or "adult")
    if not _valid(code):
        return {"error": "That barcode is not valid."}
    try:
        if code in CACHE:
            p, cached = CACHE[code], True
        else:
            p, cached = _fetch(code), False
            if p:
                CACHE[code] = p
        if not p:
            return {"error": "Barcode not in the database."}
        out = build(p, profile, code)
        out["cached"], out["ms"] = cached, round((time.time() - t0) * 1000)
        return out
    except Exception:
        return {"error": "Online lookup failed. Try again in a moment."}

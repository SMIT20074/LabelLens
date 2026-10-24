"""LabelLens lookup: name the product (AI), fetch facts online (Open Food Facts), cache, judge.
Used when a photo is blurry or the user types a product name. Never raises."""
import base64, json, os, re, threading, time, urllib.parse, urllib.request
import core

_DIR = os.path.dirname(os.path.abspath(__file__))
_FILE = os.path.join(_DIR, "product_cache.json")
_LOCK = threading.Lock()
try:
    _CACHE = json.load(open(_FILE))
except Exception:
    _CACHE = {}


def _key(t):
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()


def _ask(parts):
    from google import genai
    c = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    r = c.models.generate_content(model=core.MODEL_NAME, contents=parts)
    return (r.text or "").strip()


def identify(raw, mime):
    from google.genai import types
    t = _ask([types.Part.from_bytes(data=raw, mime_type=mime),
              "Name the product in this photo: brand and product, max 6 words. "
              "If you cannot tell, answer exactly UNKNOWN. Reply with the name only."])
    t = t.splitlines()[0].strip(" .\"'") if t else ""
    return "" if (not t or t.upper().startswith("UNKNOWN")) else t[:60]


def _off(name):
    q = urllib.parse.urlencode({
        "search_terms": name, "search_simple": 1, "action": "process", "json": 1,
        "page_size": 6,
        "fields": "product_name,brands,ingredients_text,nutriments,nutriscore_grade,additives_tags"})
    req = urllib.request.Request("https://world.openfoodfacts.org/cgi/search.pl?" + q,
                                 headers={"User-Agent": "LabelLens/1.0 (hackathon project)"})
    with urllib.request.urlopen(req, timeout=8) as r:
        d = json.loads(r.read().decode("utf-8"))
    toks = _key(name).split()
    best, bs = None, -1
    for p in d.get("products", []):
        hay = _key((p.get("brands") or "") + " " + (p.get("product_name") or ""))
        m = sum(1 for t in toks if t in hay)
        if m < max(1, len(toks) // 2):
            continue
        s = m * 2 + (1 if p.get("ingredients_text") else 0)
        if s > bs:
            best, bs = p, s
    if not best:
        return None
    n = best.get("nutriments") or {}
    per = {}
    for label, k, unit in (("energy", "energy-kcal_100g", "kcal"), ("sugar", "sugars_100g", "g"),
                           ("salt", "salt_100g", "g"), ("saturated fat", "saturated-fat_100g", "g"),
                           ("fat", "fat_100g", "g"), ("protein", "proteins_100g", "g"),
                           ("caffeine", "caffeine_100g", "g")):
        if n.get(k) is not None:
            try:
                per[label] = "%s %s" % (round(float(n[k]), 1), unit)
            except Exception:
                pass
    return {"name": best.get("product_name") or name, "brand": best.get("brands") or "",
            "ingredients_text": (best.get("ingredients_text") or "")[:900],
            "per_100g": per, "nutriscore": str(best.get("nutriscore_grade") or "").upper(),
            "additives": [a.split(":")[-1].upper() for a in (best.get("additives_tags") or [])][:8]}


def _verdict(info, profile):
    try:
        t = _ask(["Person: %s. Product: %s %s. Ingredients: %s. Per 100g: %s. "
                  "Judge only from this data. Never give a medicine dose. Reply ONLY JSON: "
                  '{"verdict":"OK or CAREFUL or AVOID","reasons":["max 3 short reasons"]}'
                  % (profile, info["brand"], info["name"], info["ingredients_text"] or "unknown",
                     json.dumps(info["per_100g"]))])
        j = json.loads(re.search(r"\{.*\}", t, re.S).group(0))
        v = j.get("verdict") if j.get("verdict") in ("OK", "CAREFUL", "AVOID") else "CAREFUL"
        rs = [str(x)[:160] for x in (j.get("reasons") or [])][:3]
    except Exception:
        v, rs = "CAREFUL", ["Could not judge this online match. Read the label."]
    if v == "OK":
        v = "CAREFUL"
        rs.append("Matched online by name, not read from your pack, so never a plain OK.")
    return v, rs


def lookup(body):
    try:
        t0 = time.time()
        profile = str(body.get("profile") or "adult")[:80]
        name = str(body.get("name") or "").strip()[:60]
        if not name:
            raw = base64.b64decode(str(body.get("image") or ""))
            if not raw:
                return {"error": "Send a photo or type a product name."}
            name = identify(raw, str(body.get("mime") or "image/jpeg"))
            if not name:
                return {"error": "Could not tell what this product is. Type its name instead."}
        ck = _key(name) + "|" + _key(profile)
        with _LOCK:
            hit = _CACHE.get(ck)
        if hit:
            out = dict(hit)
            out.update(cached=True, ms=int((time.time() - t0) * 1000))
            return out
        info = _off(name)
        if not info:
            return {"error": "No online match for “%s”. Try a clear label photo." % name, "guess": name}
        v, rs = _verdict(info, profile)
        out = {"guess": name, "product": info, "verdict": v, "reasons": rs,
               "source": "Open Food Facts", "cached": False, "ms": int((time.time() - t0) * 1000)}
        with _LOCK:
            _CACHE[ck] = out
            try:
                json.dump(_CACHE, open(_FILE, "w"))
            except Exception:
                pass
        return out
    except Exception:
        return {"error": "Online lookup failed. Try again in a moment."}

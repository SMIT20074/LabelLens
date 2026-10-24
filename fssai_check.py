import re

SOURCE = "FSS (Labelling and Display) Regulations, 2020 - verify on fssai.gov.in"

def check_fssai(text_read, ingredients, confidence):
    findings = []
    if confidence is None or confidence < 0.6 or not (text_read or "").strip():
        return [{"rule": "ALL", "status": "unable_to_determine",
                 "note": "Label not read clearly. Retake the photo.", "source": SOURCE}]
    t = text_read.lower()
    if re.search(r"(?<!\d)(\d[\s-]?){14}(?!\d)", t):
        findings.append({"rule": "FSSAI licence number (14 digits)", "status": "no_issue_in_checked_fields",
                         "note": "A 14-digit number is printed. This does not prove it is a real licence.", "source": SOURCE})
    else:
        findings.append({"rule": "FSSAI licence number (14 digits)", "status": "potential_issue",
                         "note": "No 14-digit licence number found in the text read.", "source": SOURCE})
    if "fssai" in t:
        findings.append({"rule": "FSSAI logo or name", "status": "no_issue_in_checked_fields",
                         "note": "FSSAI text found. A logo picture cannot be confirmed from text.", "source": SOURCE})
    else:
        findings.append({"rule": "FSSAI logo or name", "status": "potential_issue",
                         "note": "No FSSAI text found.", "source": SOURCE})
    if ingredients:
        findings.append({"rule": "Ingredient list", "status": "no_issue_in_checked_fields",
                         "note": "Ingredients were read.", "source": SOURCE})
    else:
        findings.append({"rule": "Ingredient list", "status": "potential_issue",
                         "note": "No ingredient list found.", "source": SOURCE})
    return findings

# LABELLENS_PATCH_FSSAI_CATEGORY
_orig_check_fssai = check_fssai
def check_fssai(text_read, ingredients, confidence):
    out = _orig_check_fssai(text_read, ingredients, confidence)
    try:
        if out and out[0].get("rule") == "ALL":
            return out
        from fssai_categories import guess_category, looks_like_medicine
        blob = (text_read or "") + " " + " ".join(str(i) for i in (ingredients or []))
        if looks_like_medicine(blob):
            note = "This looks like a medicine, not a food. FSSAI food categories and limits do not apply."
        else:
            g = guess_category(blob)
            cat = ("Category guess: %s %s (keyword guess, not official). " % g) if g else "Food category unclear. "
            note = cat + "Labels rarely print additive amounts and FSSAI limits per category are not loaded, so 'in range' cannot be confirmed."
        out.append({"rule": "Ingredient amounts vs FSSAI limits", "status": "unable_to_determine", "note": note,
                    "source": "Limits are in FSS (Food Products Standards and Food Additives) Regulations, 2011, Appendix A"})
    except Exception:
        pass
    return out

# LABELLENS_PATCH_FSSAI_LICENCE
import json as _json, os as _os, re as _re
def get_fssai_rules():
    try:
        p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fssai_rules.json")
        return _json.load(open(p))
    except Exception:
        return {"rules": []}

_prev_check_fssai = check_fssai
def check_fssai(text_read, ingredients, confidence):
    out = _prev_check_fssai(text_read, ingredients, confidence)
    try:
        if out and out[0].get("rule") == "ALL":
            return out
        t = (text_read or "").lower()
        if _re.search(r"(?<!\d)(\d[\s-]?){14}(?!\d)", t):
            out.append({"rule": "FSSAI licence validity", "status": "unable_to_determine",
                "note": "A licence is valid for 1 to 5 years from its issue date. A printed number does not show whether it is still valid. Check it on the official FSSAI licence search (FoSCoS).",
                "source": "FSS (Licensing and Registration) Regulations, 2011, reg 2.1.7(1) - needs legal review"})
    except Exception:
        pass
    return out

# LABELLENS_PATCH_FSSAI_MEDICINE
_prev_med_check = check_fssai
def check_fssai(text_read, ingredients, confidence):
    out = _prev_med_check(text_read, ingredients, confidence)
    try:
        from fssai_categories import looks_like_medicine
        blob = (text_read or "") + " " + " ".join(str(i) for i in (ingredients or []))
        if out and out[0].get("rule") != "ALL" and looks_like_medicine(blob):
            return [x for x in out if x["rule"] == "Ingredient amounts vs FSSAI limits"]
    except Exception:
        pass
    return out

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

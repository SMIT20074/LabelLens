# LabelLens shared contract (fixed, nobody changes it)

Function in core.py:
analyze_label(image_bytes: bytes, mime_type: str, profile: str) -> dict

Returned dict keys:
- label_type (str)
- language_detected (str)
- text_read (str)
- ingredients (list of str)
- warnings (list of str)
- verdict ("OK" or "CAREFUL" or "AVOID")
- reasons (list of str)
- confidence (float, 0 to 1)
- retake_photo (bool)
- error (str or None)

profile is plain text like "adult", "child age 5", "pregnant", "allergic to peanuts".

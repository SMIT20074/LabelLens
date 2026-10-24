# LabelLens

Hacktoberfest Hack Day, NST ADYPU, 24–25 October 2026.

## What LabelLens is

LabelLens is a web app that helps people read food, medicine, household, and pesticide labels.  
It aims to explain labels in any language, with a profile-based verdict, warnings, ingredients, and the text the model read.

**Why:** small print, hard words, and unfamiliar languages make labels hard to understand.

## Current status

This README follows the team's brief. The repo and running app were not independently verified for this update.

| Status | Details |
| --- | --- |
| Team-reported working | Laptop web app, live camera, profiles, nutrition card, daily tracker, assistant, and rate limits. |
| Current code branch | `smit-core` in [SMIT20074/LabelLens](https://github.com/SMIT20074/LabelLens). |
| Not yet confirmed | A real label scan using real Gemma 4, a public Render link, and measured accuracy. |
| Known bug | Auto-scan can fire when no label is in view. Use manual **Scan now** for the demo. |
| Evaluation target | Aman plans to check 15 real label photos. This is a target, not a completed test count. |
| Planned if time allows | Open Food Facts barcode lookup, faster photo upload, a new dark look, and an installable PWA. |

An offline demo uses saved sample scans. It must be labeled as a sample demo, not a live model result.

**Why:** judges need to know what is ready, what needs checking, and what is planned.

## How it works

1. Take or upload a label photo and choose a profile. **Why:** warnings can depend on who will use the product.
2. The web page sends it to the Python server and `core.py`, which calls Gemma 4 through the Gemini API. **Why:** the model reads the image.
3. Code checks the result before showing a verdict. **Why:** a poor reading must not produce an OK verdict.
4. Show ingredients, reasons, warnings, and the text read beside the verdict. **Why:** the user can compare the reading with the photo.

Flow: photo → web page → Python server → `core.py` → Gemma 4 through Gemini API → safety checks → screen.

## Features in the team brief

- **Profile-based results:** the app uses the person's profile when it explains a label. An OK result is not a safety guarantee.
- **Text read:** users can check the model's reading against the photo.
- **Retake check:** a blurry or empty photo, or confidence below **0.6**, requires a retake or CAREFUL result. Code must block OK.
- **Nutrition card:** shows a share of daily limits for sugar, calories, sodium, and saturated fat.
- **Claim check:** compares front-of-pack claims with printed pack text. It does not uncover hidden recipes.
- **Today tab:** food log, limits, alerts, an adult calorie target estimate, and estimates for food without a label.
- **Assistant tab:** chat and voice input/output in English, Hindi, and Marathi.
- **Capture and history:** live camera, photo upload, device-saved scan history, and saved offline samples.
- **Rate limits:** 60 requests per person per 10 minutes and 800 per day, as specified in the brief.

The reported laptop features still need an end-to-end check with a real label and the real model.

**Why:** these features support the main job of reading and checking a label.

## Models and tools used

| Tool | Job |
| --- | --- |
| Gemma 4 through the Gemini API | Read label images and help explain them. |
| Python 3.11+ | Run the backend. |
| Python standard library web server | Serve the page and handle requests. |
| HTML, CSS, JavaScript | Build the web interface. |
| `core.py` | Run the label analysis and checks. |
| `extras.py` | Support nutrition and chat. |
| `app.py` | Run the server and page. |
| Render free plan | Intended public hosting; the public link is not yet confirmed. |
| GitHub | Hold the team's public code. |

This build uses a Python web server, not Streamlit. Gemma 4 has open weights, but this build calls Google's hosted API.

**Why:** each part has a clear job that every team member should be able to explain.

## Fixed contract

The function in `core.py` stays:

```python
analyze_label(image_bytes, mime_type, profile) -> dict
```

The returned keys stay:

`label_type`, `language_detected`, `text_read`, `ingredients`, `warnings`, `verdict`, `reasons`, `confidence`, `retake_photo`, `error`.

Verdict is OK, CAREFUL, or AVOID. Confidence ranges from 0 to 1. A model confidence value is not a measured accuracy score.

**Why:** a fixed contract lets the team work on separate files.

## Licenses and tracks

**Gemma 4:** Apache License, Version 2.0, January 2004.

Checked against the [official model card](https://ai.google.dev/gemma/docs/core/model_card_4) and its linked [full license](https://ai.google.dev/gemma/apache_2) on 24 October 2026. The license allows use, changes, and sharing, including commercial use, under its terms. Redistribution requires a license copy, notices on changed files, retention of applicable notices in source, and applicable NOTICE attributions when supplied. Section 3 covers limited patent rights and when they end. It does not give general trademark permission and provides the work without a warranty, subject to the text's exceptions.

**Project code:** MIT, as stated in the team brief. The repo's license file was not independently checked for this update.

Hosted access also follows the [Gemini API terms](https://ai.google.dev/gemini-api/terms).

The team is targeting Best Open-Source AI Project and Best Use of Gemma 4 through the Gemini API. Organizers have not yet confirmed whether hosted API use meets the open-weight track's rules.

**Why:** model licensing, project licensing, and event eligibility are separate questions.

## How to run

You need Git, Python 3.11+, and a Gemini API key. These steps follow the file layout and branch in the brief; Smit should confirm them against the running build.

Use **Bash** on macOS or Linux.

1. **Get the current build.**

   ```bash
   git clone --branch smit-core https://github.com/SMIT20074/LabelLens.git labellens
   cd labellens
   ```

   **Why:** this checks out the branch reported to hold the laptop build.

2. **Install the declared dependencies.** If the repo provides `requirements.txt`, run:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

   If that file is absent, Smit must confirm the package list; do not guess dependencies.

   **Why:** the app needs the packages used by its code.

3. **Set the key for this terminal session.** Enter it only at the hidden local prompt.

   ```bash
   read -r -s -p "Gemini API key (hidden): " GEMINI_API_KEY
   printf '\n'
   export GEMINI_API_KEY
   ```

   **Why:** the key stays in the environment instead of code, files, or command history.

4. **Start the Python server.**

   ```bash
   python3 app.py
   ```

   Open the address printed by the server. Use manual **Scan now** for the demo.

   **Why:** `app.py` serves the page and handles web requests.

Never put a key in code, files, commits, screenshots, or chat. Never create or commit a `.env` file.

## Privacy

Photos and profile text go to the Python server and Google's Gemini API for reading. Google handles submitted data under its [API data terms](https://ai.google.dev/gemini-api/terms).

The team brief says scan history is saved on the user's device. Before making a privacy claim, confirm whether history includes images or only results, and confirm the server's storage and logging behavior.

Do not claim that nothing is stored or that processing is fully offline.

**Why:** users need to know where their photo goes and where history stays.

## Safety

LabelLens is **informational only**. It is a reading and checking helper, not a doctor.

- It **never gives a medicine or pesticide dose**.
- Users must check the printed label because AI can be wrong.
- A blurry or empty photo, or confidence below **0.6**, must block OK and lead to CAREFUL or a retake request.
- The 0.6 threshold is a code rule, not proof of accuracy.
- Daily nutrition limits use general guidance; they may not fit every person.
- Calorie targets and unlabelled-food entries are estimates for adults, not medical advice.
- A claim check uses visible pack text; it cannot detect an undisclosed recipe.

The retake and verdict guards need real tests. This README does not prove they work.

**Why:** a wrong OK can cause harm, while a retake gives the user another chance to check.

## Honest limits and evaluation

- Small print, glare, blur, cropped labels, and unfamiliar wording can cause errors.
- The model may invent words, miss warnings, or give a wrong verdict.
- "Any country, any language" is the goal, not tested worldwide coverage.
- Auto-scan has a known empty-view bug; manual **Scan now** is the safer demo path.
- Scan time is expected to be a few seconds but has not been measured here. Do not claim "instant" or "1 second".
- Completed label count (N): **TBD**.
- Accuracy: **TBD**.
- A real scan with Gemma 4 and the public Render deployment remain unconfirmed.
- Use only real counts and scores from [eval/results.md](eval/results.md). Aman owns the evaluation, including planned label photos, `answers.csv`, and `run_eval.py`.
- Closest-tool names and comparisons must come from [research/competitors.md](research/competitors.md). Those contents were not available for this update.

**Why:** clear limits help users and judges see what the project has actually shown.

## Team

| Person | Name | Repo files owned | Work |
| --- | --- | --- | --- |
| Person 1 | Smit | `core.py`, `app.py`, `extras.py` | Core analysis, server, extras, deploy, and merges. |
| Person 2 | Aman | `research/`, `eval/` | Source checks, competitor research, and real-label evaluation. |
| Person 3 | Ajay | `README.md`, `slides/` | Write this guide and prepare **all presentation slides 1–8**, including the shared deck outside the repo. |
| Person 4 | Narmit | `pitch/` | Prepare the pitch and speaking notes. |

Everyone must explain the full photo-to-verdict flow. Work on your own branch and edit only your assigned files. Keep commits small. Pull before pushing, and push only after the team says the base is ready. Never commit a key or a `.env` file.

**Why:** clear roles reduce conflicts and help every member answer judges' questions.


"""LabelLens web app v3: label-paper UI + handbook features. AI work stays in core.py.

Run:  python3 app.py   (then open http://localhost:8501)
Team tools: http://localhost:8501/?team=1
"""
import base64
import json
import os
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import core
import extras
from concurrent.futures import ThreadPoolExecutor

PORT = int(os.environ.get("PORT", "8501"))
SAMPLES_DIR = Path(__file__).parent / "samples"
MAX_BODY = 25 * 1024 * 1024
MAX_SAMPLES = 50

PAGE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>LabelLens</title>
<style>
:root{--ink:#101418;--paper:#eef2ef;--card:#fff;--mut:#5d6660;--ok:#0f9d58;--care:#e08a00;--bad:#d62839;--hi:#ffe14d}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0}
body{font:16px/1.5 "Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink);background:var(--paper);padding-bottom:70px}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes pop{0%{transform:scale(.5);opacity:0}70%{transform:scale(1.08)}100%{transform:scale(1);opacity:1}}
@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-9px)}40%{transform:translateX(8px)}60%{transform:translateX(-5px)}80%{transform:translateX(4px)}}
@keyframes scan{0%{top:3%}50%{top:95%}100%{top:3%}}
@keyframes stamp{0%{transform:scale(2.2) rotate(-8deg);opacity:0}60%{transform:scale(.94) rotate(-3deg);opacity:1}100%{transform:scale(1) rotate(-3deg)}}
.wrap{max-width:1080px;margin:0 auto;padding:14px 16px}
header{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:6px 0 12px;border-bottom:6px solid var(--ink)}
.brand{font-size:2.1rem;font-weight:900;letter-spacing:-.04em;line-height:1;display:flex;align-items:center;gap:10px}
.brand svg{width:40px;height:40px}
.tag{margin:0;color:var(--mut);font-size:.95rem;flex:1;min-width:200px}
nav{display:flex;gap:6px;flex-wrap:wrap;padding:12px 0}
nav button{border:2px solid var(--ink);background:var(--card);border-radius:6px;padding:6px 12px;font:inherit;font-weight:700;font-size:.9rem;cursor:pointer}
nav button.on{background:var(--ink);color:#fff}
button:focus-visible,input:focus-visible{outline:3px solid #2b6df0;outline-offset:2px}
.grid{display:grid;gap:16px;grid-template-columns:1fr}
@media(min-width:900px){.grid{grid-template-columns:400px 1fr;align-items:start}.left{position:sticky;top:12px}}
.box{background:var(--card);border:2px solid var(--ink);border-radius:6px;padding:14px;margin-bottom:14px}
.box h2{margin:0 0 10px;font-size:1.15rem;font-weight:900;padding-bottom:6px;border-bottom:4px solid var(--ink)}
.box h3{margin:14px 0 4px;font-size:1rem}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:2px solid var(--ink);background:#fff;border-radius:999px;padding:6px 12px;font:inherit;font-weight:700;font-size:.9rem;cursor:pointer;transition:transform .15s}
.chip:active{transform:scale(.94)}
.chip.on{background:var(--ink);color:#fff}
.chips.off .chip.on{background:#fff;color:var(--ink)}
#custom{width:100%;margin-top:10px;border:2px solid var(--ink);border-radius:6px;padding:10px 12px;font:inherit}
.vf{position:relative;display:block;aspect-ratio:16/10;border:2px solid var(--ink);border-radius:6px;overflow:hidden;cursor:pointer;
  background:repeating-linear-gradient(0deg,#fff 0 22px,#f1f4f2 22px 23px)}
.vf input{display:none}
.vf img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:none;background:#fff}
.vf.has img{display:block}
.vf-empty{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;text-align:center;padding:12px}
.vf.has .vf-empty{display:none}
.vf-empty svg{width:44px;height:44px}
.vf-empty b{font-size:1.1rem}.vf-empty span{color:var(--mut);font-size:.88rem}
.cn{position:absolute;width:26px;height:26px;border:4px solid var(--ink);pointer-events:none}
.c1{top:8px;left:8px;border-right:0;border-bottom:0}.c2{top:8px;right:8px;border-left:0;border-bottom:0}
.c3{bottom:8px;left:8px;border-right:0;border-top:0}.c4{bottom:8px;right:8px;border-left:0;border-top:0}
.laser{position:absolute;left:0;right:0;top:3%;height:4px;background:var(--bad);box-shadow:0 0 16px 4px rgba(214,40,57,.6);opacity:0;pointer-events:none}
.vf.scanning .laser{opacity:1;animation:scan 1.5s ease-in-out infinite}
.vf.drag{outline:4px dashed var(--bad);outline-offset:-8px}
.cta{width:100%;margin-top:10px;border:2px solid var(--ink);border-radius:6px;padding:15px;font:inherit;font-size:1.1rem;font-weight:900;color:#fff;background:var(--ink);cursor:pointer}
.cta:disabled{opacity:.35;cursor:not-allowed}
.cta:not(:disabled):active{transform:translateY(2px)}
.ghost{border:2px solid var(--ink);background:#fff;color:var(--ink);border-radius:6px;padding:9px 14px;font:inherit;font-weight:700;cursor:pointer;margin:8px 6px 0 0}
.status{min-height:1.3em;margin:8px 0 0;font-weight:700}.status.bad{color:var(--bad)}
.banner{border:2px solid var(--ink);border-radius:6px;padding:10px 12px;font-weight:600;margin-bottom:10px}
.warn{background:#fff3cd}.err{background:#ffd9de}.info{background:#dfe9ff}
.verdict{border:3px solid var(--ink);border-radius:6px;background:var(--vc);color:#fff;padding:16px;display:grid;grid-template-columns:130px 1fr;gap:14px;align-items:center;margin-bottom:12px;animation:rise .4s both}
.verdict.v-avoid{animation:rise .4s both,shake .5s .3s both}
.ringwrap{position:relative;width:130px;height:130px}
.ring{width:130px;height:130px;transform:rotate(-90deg)}
.ring .t{fill:none;stroke:rgba(255,255,255,.3);stroke-width:10}
.ring .p{fill:none;stroke:#fff;stroke-width:10;stroke-linecap:butt;transition:stroke-dashoffset 1.2s cubic-bezier(.2,.8,.2,1)}
.ringmid{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.5rem}
.vword{font-size:3.2rem;font-weight:900;letter-spacing:-.02em;line-height:1;display:inline-block;border:4px solid #fff;padding:2px 12px;animation:stamp .5s .2s both}
.vsub{margin-top:8px;font-weight:600}
.vmeta{margin-top:4px;font-size:.85rem;opacity:.9}
@media(max-width:520px){.verdict{grid-template-columns:1fr;text-align:center;justify-items:center}}
ul.plain{margin:0;padding:0;list-style:none}
ul.plain li{padding:6px 0 6px 18px;border-top:1px solid #d9dfdb;position:relative}
ul.plain li:first-child{border-top:0}
ul.plain li::before{content:"";position:absolute;left:0;top:14px;width:8px;height:8px;background:var(--ink)}
.ing b{font-weight:800}.ing span{color:var(--mut)}
.raw{white-space:pre-wrap;word-break:break-word;background:#f6f8f6;border:1px solid #cfd6d1;padding:10px;margin:8px 0;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;max-height:240px;overflow:auto}
mark{background:var(--hi);color:var(--ink);padding:0 2px}
.note{color:var(--mut);font-size:.85rem}
.row{padding:8px 0;border-top:1px solid #d9dfdb}.row:first-child{border-top:0}
.row b{display:block}.row span{color:#333}
label.ck{display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-top:1px solid #d9dfdb;cursor:pointer}
label.ck:first-of-type{border-top:0}
label.ck input{margin-top:5px;width:18px;height:18px;accent-color:var(--ink)}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;background:var(--bad)}.dot.y{background:var(--ok)}
.hist{display:flex;flex-wrap:wrap;gap:6px}
.bar{position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--ink);color:#fff;text-align:center;padding:8px 12px calc(8px + env(safe-area-inset-bottom));font-size:.85rem;font-weight:600}
.vf{cursor:default}
.vf video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none}
.vf.live video{display:block}.vf.live .vf-empty{display:none}
.vf.locked,.vf.locked .cn{border-color:var(--ok)}
.meter{position:absolute;left:12px;right:12px;bottom:10px;height:6px;background:rgba(0,0,0,.4);border-radius:3px;overflow:hidden;display:none}
.vf.live .meter{display:block}.vf.has .meter{display:none}
.meter i{display:block;height:100%;width:0;background:#fff;transition:width .2s}
.vf.locked .meter i{background:var(--ok)}
.btnrow{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.btnrow .ghost{margin:0;flex:1;white-space:nowrap;text-align:center}
.hint{font-weight:700;margin-top:6px;min-height:1.3em}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px}
.tile{border:2px solid var(--ink);border-radius:6px;padding:8px}
.tile b{display:block;font-size:1.3rem;line-height:1.1}.tile span{font-size:.8rem;color:var(--mut)}
.pbar{height:8px;background:#dfe5e1;border-radius:4px;overflow:hidden;margin-top:6px}
.pbar i{display:block;height:100%;background:var(--ok)}.pbar i.m{background:var(--care)}.pbar i.h{background:var(--bad)}
.lv{padding:7px 0;border-top:1px solid #d9dfdb}.lv:first-of-type{border-top:0}
.lv.lw b{color:var(--bad)}.lv.ln b{color:#b36b00}.lv.lo b{color:var(--ok)}
.toast{position:fixed;left:12px;right:12px;top:12px;z-index:90;background:var(--bad);color:#fff;border:3px solid var(--ink);border-radius:6px;padding:12px 14px;font-weight:700;animation:rise .3s both;max-width:640px;margin:0 auto;cursor:pointer}
.chat{display:flex;flex-direction:column;gap:8px;max-height:52vh;overflow:auto;padding:4px 2px}
.msg{padding:9px 12px;border:2px solid var(--ink);border-radius:6px;max-width:88%;white-space:pre-wrap}
.msg.u{align-self:flex-end;background:var(--ink);color:#fff}.msg.a{align-self:flex-start;background:#fff}
.chatrow{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.chatrow input,.chatrow select{border:2px solid var(--ink);border-radius:6px;padding:10px;font:inherit}
.chatrow input{flex:1;min-width:140px}.chatrow .ghost{margin:0}
.frm{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}
.frm label{font-size:.85rem;font-weight:700}
.frm input,.frm select,.qin{width:100%;border:2px solid var(--ink);border-radius:6px;padding:9px;font:inherit}
.logrow{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:7px 0;border-top:1px solid #d9dfdb}
.logrow:first-of-type{border-top:0}.logrow .ghost{margin:0;padding:4px 10px}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head>
<body>
<div class="wrap">
<header>
  <div class="brand"><svg viewBox="0 0 64 64" aria-hidden="true"><rect x="4" y="4" width="56" height="56" rx="6" fill="#101418"/><circle cx="29" cy="29" r="13" fill="none" stroke="#fff" stroke-width="5"/><path d="M39 39 L52 52" stroke="#ffe14d" stroke-width="7" stroke-linecap="round"/><path d="M22 27h14M22 33h8" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>LabelLens</div>
  <p class="tag">Photograph a label. See what it says, and whether it fits the person using it.</p>
</header>
<nav id="nav"></nav>
<div id="setup"></div><div id="alerts"></div>

<div id="tab-scan" class="grid">
  <div class="left">
    <section class="box">
      <h2>Who is this for?</h2>
      <div class="chips" id="chips"></div>
      <input id="custom" maxlength="200" placeholder='Or type: "diabetic, allergic to nuts"' autocomplete="off">
    </section>
    <div class="vf" id="vf">
      <video id="cam" autoplay playsinline muted></video>
      <div class="vf-empty">
        <svg viewBox="0 0 64 64" fill="none" stroke="#101418" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 22h10l4-7h16l4 7h10a3 3 0 0 1 3 3v24a3 3 0 0 1-3 3H10a3 3 0 0 1-3-3V25a3 3 0 0 1 3-3z"/><circle cx="32" cy="36" r="10"/></svg>
        <b id="emptyT">Starting the camera\u2026</b><span id="emptyS">Allow camera access. Or use Upload photo.</span>
      </div>
      <img id="preview" alt="Your label photo">
      <i class="cn c1"></i><i class="cn c2"></i><i class="cn c3"></i><i class="cn c4"></i><div class="laser"></div><div class="meter"><i id="meterFill"></i></div>
    </div>
    <div class="btnrow"><button class="ghost" id="flip" type="button">Flip camera</button><button class="ghost" id="auto" type="button">Auto-scan: on</button><label class="ghost" style="cursor:pointer">Upload photo<input type="file" id="file" accept="image/*" hidden></label></div><div class="hint" id="hint"></div>
    <button class="cta" id="go" type="button" disabled>Check this label</button>
    <div class="status" id="status" role="status"></div>
    <section class="box" id="histBox" hidden style="margin-top:12px"><h2>Recent scans</h2><div class="hist" id="hist"></div><button class="ghost" id="clearHist" type="button">Clear history</button></section>
    <section class="box" style="margin-top:12px"><button class="ghost" id="demoBtn" type="button" style="margin:0">No internet? Offline demo</button><div class="hist" id="demoList" style="margin-top:8px"></div></section>
  </div>
  <div id="result"><section class="box"><h2>Result appears here</h2><p class="note" style="margin:0">Pick who the label is for, add a photo, then press Check. You will see the verdict, the reasons, and the exact text the model read.</p></section></div>
</div>
<div id="tab-today" hidden></div><div id="tab-ai" hidden></div><div id="tab-info" hidden></div>
</div>
<div class="bar">Informational only. Check the label and ask a doctor or pharmacist.</div>

<script>
"use strict";
var PROFILES=["adult","child age 5","pregnant","allergic to peanuts","diabetic","elderly"];
var VERDICTS={OK:{c:"#0f9d58",sub:"Nothing readable on the label conflicts with this profile. This is not a guarantee of safety."},
  CAREFUL:{c:"#e08a00",sub:"A concern exists or the evidence is incomplete. Read the label closely."},
  AVOID:{c:"#d62839",sub:"The label shows a specific problem for this profile. Do not proceed without resolving it."}};
var MSGS=["Reading the label\u2026","Checking the ingredients\u2026","Matching it to the profile\u2026"];
var CATS=[["food","Food: explains nutrition and known concerns. An unfamiliar or artificial ingredient is not called harmful on that basis alone."],
  ["medic","Medicine: explains what the label prints. No dose, treatment or prescription advice is ever invented. Ask a doctor or pharmacist."],
  ["pestic","Pesticide: label text only. No dose or application instruction is invented. Follow the product label and local rules."],
  ["agri","Pesticide: label text only. No dose or application instruction is invented. Follow the product label and local rules."],
  ["clean","Household chemical: explains label hazards. No safe-use instruction is invented."],
  ["household","Household chemical: explains label hazards. No safe-use instruction is invented."]];
var TABS=[["scan","Scan"],["today","Today"],["ai","Assistant"],["how","How it works"],["rules","Verdicts and safety"],["tests","Tests"],["rivals","Rivals"],["next","Roadmap"]];
var TEAM=new URLSearchParams(location.search).has("team");
var chosen=PROFILES[0],img=null,msgTimer=null,current=null,HEALTH={};
var INFO={
how:[["#","The idea"],["Label first","LabelLens reads the actual photo. No product database match is needed, so unfamiliar products work."],
 ["#","The six stages"],["1 Upload","A photo plus a plain-text profile such as \"pregnant\" or \"allergic to peanuts\"."],
 ["2 Read","A vision model (Gemma 4 through the Gemini API) pulls out the visible text, the language and the product type."],
 ["3 Explain","Ingredients and known concerns, in simple words."],["4 Check","Profile and product rules check warnings and uncertainty."],
 ["5 Validate","Python checks the reply has the right keys and types. Code blocks an OK verdict on a blurry, empty or low-confidence read."],
 ["6 Display","Exact text, ingredients, warnings, verdict, reasons, confidence and retake status."],
 ["#","Four promises"],["Read any visible label","No database match required to start."],["Explain ingredients","Plain language and profile checks."],
 ["Show evidence","The exact text is shown, with profile words highlighted."],["Admit uncertainty","Blurry photos get a retake request. Nothing is invented."],
 ["#","Contract"],["analyze_label","analyze_label(image_bytes, mime_type, profile) returns label_type, language_detected, text_read, ingredients, warnings, verdict, reasons, confidence, retake_photo, error."]],
rules:[["#","What each verdict means"],["OK","No relevant concern found in the available label text. Never a promise of safety."],
 ["CAREFUL","A concern exists, or evidence is incomplete: unclear text, uncertain ingredient, or a warning that needs checking."],
 ["AVOID","A specific, well-supported concern, such as a declared allergen that matches a stated allergy."],
 ["Confidence","How well the label was read. It is not the chance that the product is safe."],
 ["#","Rules by category"],["Food","Explain nutrition and known concerns. Do not call something harmful only because it is unfamiliar."],
 ["Medicine","Explain label content and warnings. Never invent doses, treatment advice or prescriptions."],
 ["Household chemicals","Explain label hazards. Never invent safe-use instructions."],["Pesticides","Use label text only. Never invent doses or application steps."],
 ["All categories","If key text is unreadable, ask for a retake. If still unsure, say a reliable verdict cannot be reached."],
 ["#","Trust rule"],["No sponsorship","A safety verdict is never sold to a brand and a warning is never changed for money."]],
rivals:[["#","Closest tools (public pages; validate before presenting)"],
 ["Yuka","Food and cosmetics scoring from a product database."],["ReadLabel","Label-photo analysis without a product database."],
 ["Factsy","Database-free ingredient analysis with profile warnings."],["KnowFood","Food additive analysis with named safety references."],
 ["FactsScan","India-focused food scanning with health scores."],["Open Food Facts","Open food database with barcode lookup."],
 ["Fooducate","Food grading, barcode scanning, tracking."],["Spoonful","Dietary restrictions and allergies with a product catalog."],
 ["Scroov","India-focused label and barcode scanning."],["Aahar IQ","India-focused AI food label reading, multilingual claims."],
 ["#","Our honest position"],["Not unique alone","Database-free label reading already exists (ReadLabel, Factsy)."],
 ["Our edge","Exact-text evidence, profile-aware checks, multilingual reading, category rules and visible uncertainty, together."]],
next:[["#","After the hackathon"],["History and reports","Saved scans, downloadable reports, privacy controls to delete them."],
 ["Evidence links","Tie each warning to the exact label text."],["Official sources","Look up safety rules and alerts."],
 ["More reach","More languages, translated summaries, text-to-speech, accessibility."],["Food extras","Product comparison and alternatives."],
 ["Quality","A verified ingredient library and a larger human-reviewed test set."],
 ["#","Business options"],["Freemium","Basic scans free, detailed reports paid."],["Family plan","Several profiles and saved history. Needs strong data protection."],
 ["Business API","Label reading for retailers and other apps."],["Partnerships","Consumer education and research."],
 ["#","Risks and answers"],["Wrong reading","Show exact text, ask for a retake, test known labels."],["Missed allergen","Never promise perfect detection. Check the package."],
 ["Unsafe advice","Never invent doses. Use label text only."],["API outage","Clear retry message and an offline demo."],["Key leak","Environment variable only. Never logged or committed."],
 ["#","60-second pitch"],["Pitch","People struggle with tiny text and unfamiliar ingredients, and databases miss products. LabelLens reads the real label photo, shows the text it read, explains ingredients, checks them against the user's profile and gives OK, CAREFUL or AVOID with reasons. It asks for a clearer photo when needed. It is informational only, and it never claims to guarantee safety."]]};
var TESTS=["Clear food label: extracted text and ingredients match the real label","Unfamiliar brand: works without any database","Peanut label with a peanut-allergy profile: a warning appears","Same label, different profile: verdict changes only where the label supports it","Blurry ingredient list: a retake is requested","Non-English label: text and language match a known example","Medicine label: no invented dose or treatment","Pesticide label: no invented dose or application step","Missing key or bad model reply: a helpful message, no crash, no key shown",
 "Demo day: one clear scan works end to end","Demo day: exact text is visible","Demo day: backup samples are saved","Demo day: team can explain the contract and its limits"];

function $(s){return document.querySelector(s)}
function el(t,c,x){var n=document.createElement(t);if(c)n.className=c;if(x!=null)n.textContent=x;return n}
function svgEl(t,a){var n=document.createElementNS("http://www.w3.org/2000/svg",t);for(var k in a)n.setAttribute(k,a[k]);return n}
function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}
function arr(x){return Array.isArray(x)?x.map(String):[]}
function getProfile(){return $("#custom").value.trim()||chosen}
function say(m,c){var s=$("#status");s.textContent=m||"";s.className="status "+(c||"")}
function store(k,v){try{if(v===undefined)return JSON.parse(localStorage.getItem(k)||"null");localStorage.setItem(k,JSON.stringify(v))}catch(e){return null}}

function buildNav(){var n=$("#nav");n.textContent="";TABS.forEach(function(t){var b=el("button",t[0]==="scan"?"on":"",t[1]);b.type="button";b.onclick=function(){openTab(t[0])};b.dataset.t=t[0];n.appendChild(b)})}
function openTab(t){
  document.querySelectorAll("#nav button").forEach(function(b){b.classList.toggle("on",b.dataset.t===t)});
  $("#tab-scan").hidden=t!=="scan";$("#tab-today").hidden=t!=="today";$("#tab-ai").hidden=t!=="ai";var info=$("#tab-info");info.hidden=["scan","today","ai"].indexOf(t)>=0;
  if(t==="scan"){if(!img)startCam()}else stopCam();
  if(t==="today")renderToday();
  if(["scan","today","ai"].indexOf(t)>=0)return;
  info.textContent="";
  if(t==="tests"){renderTests(info);return}
  var box=el("section","box");
  INFO[t].forEach(function(r){
    if(r[0]==="#"){var h=el("h2",null,r[1]);h.style.marginTop=box.children.length?"18px":"0";box.appendChild(h)}
    else{var d=el("div","row");d.appendChild(el("b",null,r[0]));d.appendChild(el("span",null,r[1]));box.appendChild(d)}});
  info.appendChild(box);window.scrollTo(0,0)}
function renderTests(info){
  var box=el("section","box");box.appendChild(el("h2",null,"Live status"));
  [["API key is set",HEALTH.key],["Model name is set in core.py",HEALTH.model],["Saved offline samples: "+(HEALTH.samples||0)+" (need 3)",(HEALTH.samples||0)>=3]].forEach(function(s){
    var d=el("div","row");var dot=el("i","dot"+(s[1]?" y":""));d.appendChild(dot);d.appendChild(document.createTextNode(s[0]));box.appendChild(d)});
  box.appendChild(el("h2",null,"Test checklist"));box.lastChild.style.marginTop="18px";
  var done=store("ll_tests")||{};
  TESTS.forEach(function(t,i){var l=el("label","ck");var c=el("input");c.type="checkbox";c.checked=!!done[i];
    c.onchange=function(){done[i]=c.checked;store("ll_tests",done)};l.appendChild(c);l.appendChild(el("span",null,t));box.appendChild(l)});
  box.appendChild(el("p","note","Only claim an accuracy number when you have a defined test set and a calculated result. Ticks are saved on this device."));
  info.appendChild(box)}

function buildChips(){var b=$("#chips");b.textContent="";PROFILES.forEach(function(p){
  var c=el("button","chip"+(p===chosen?" on":""),cap(p));c.type="button";
  c.onclick=function(){chosen=p;$("#custom").value="";b.classList.remove("off");buildChips()};b.appendChild(c)})}

function loadFile(f){
  if(!f)return;var url=URL.createObjectURL(f),im=new Image();
  im.onload=function(){var k=Math.min(1,1600/Math.max(im.naturalWidth,im.naturalHeight));
    var w=Math.max(1,Math.round(im.naturalWidth*k)),h=Math.max(1,Math.round(im.naturalHeight*k));
    var c=document.createElement("canvas");c.width=w;c.height=h;c.getContext("2d").drawImage(im,0,0,w,h);
    var u=c.toDataURL("image/jpeg",.9);img={b64:u.split(",")[1],mime:"image/jpeg"};
    $("#preview").src=u;$("#vf").classList.add("has");$("#go").disabled=false;say("");URL.revokeObjectURL(url)};
  im.onerror=function(){URL.revokeObjectURL(url);say("That file is not a readable image. Use a JPG, PNG or WEBP photo.","bad")};
  im.src=url}

function setBusy(b){$("#go").disabled=b||!img;$("#go").textContent=b?"Scanning\u2026":"Check this label";
  $("#vf").classList.toggle("scanning",b);clearInterval(msgTimer);
  if(b){var i=0;say(MSGS[0]);msgTimer=setInterval(function(){i=(i+1)%MSGS.length;say(MSGS[i])},1400)}else say("")}

function errorResult(m){return{label_type:"unknown",language_detected:"unknown",text_read:"",ingredients:[],warnings:[],verdict:"CAREFUL",
  reasons:["Could not analyze this photo. Please try again."],confidence:0,retake_photo:true,error:String(m)}}

async function analyze(profile){
  if(!img)return;profile=profile||getProfile();setBusy(true);var data;
  try{var r=await fetch("/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image:img.b64,mime:img.mime,profile:profile})});
    data=await r.json();if(!data||typeof data!=="object"||!data.verdict)data=errorResult(data&&data.error?data.error:"Unexpected reply from the server.")}
  catch(e){data=errorResult("Network problem: "+e.message)}
  setBusy(false);showResult(data,profile,"live");
  if(!data.error){var h=store("ll_hist")||[];h.unshift({t:Date.now(),profile:profile,r:data});store("ll_hist",h.slice(0,8));buildHist()}}

function listBox(title,items,ing){
  var b=el("section","box");b.appendChild(el("h2",null,title));var u=el("ul","plain");
  items.forEach(function(t){var li=el("li",ing?"ing":null);
    if(ing){var m=t.split(/\s[-\u2013\u2014]\s|:\s/);if(m.length>1){li.appendChild(el("b",null,m[0]));li.appendChild(el("span",null," \u2013 "+m.slice(1).join(": ")))}else li.appendChild(el("b",null,t))}
    else li.textContent=t;u.appendChild(li)});
  b.appendChild(u);return b}

function highlight(node,text,words){
  if(!words.length){node.textContent=text;return}
  var re=new RegExp("("+words.map(function(w){return w.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}).join("|")+")","gi");
  text.split(re).forEach(function(p,i){if(i%2){var m=el("mark",null,p);node.appendChild(m)}else node.appendChild(document.createTextNode(p))})}
var STOP="adult child age pregnant allergic allergy diabetic elderly with and the for who from have has not only about".split(" ");
function profileWords(p){return p.toLowerCase().split(/[^a-z\u00C0-\u024F]+/).filter(function(w){return w.length>=4&&STOP.indexOf(w)<0})}

function limits(r,conf){
  var l=[];if(r.retake_photo||conf<.6)l.push("Some key text may be unreadable. Retake the photo before relying on this.");
  else if(conf<.85)l.push("The read is only partly certain. Compare the text below with the real label.");
  if(r.error)l.push("The analysis failed: "+r.error);
  l.push("It cannot confirm doses, drug interactions or ingredients that are not printed.");
  l.push("It reads this one label. It is not a medical, pharmacy or pesticide authority.");return l}

function showResult(r,profile,source){
  current={r:r,profile:profile,source:source};
  var box=$("#result");box.textContent="";
  var conf=Math.max(0,Math.min(1,Number(r.confidence)||0)),v=VERDICTS[r.verdict]?r.verdict:"CAREFUL",meta=VERDICTS[v];
  if(source==="sample")box.appendChild(el("div","banner info","Showing a saved sample (offline demo)."));
  if(r.error)box.appendChild(el("div","banner err","Could not analyze: "+r.error+". You can use the offline demo."));
  if(r.retake_photo||conf<.6)box.appendChild(el("div","banner warn","Please retake the photo. Hold the phone steady, fill the frame with the label, use good light, avoid glare."));

  var card=el("div","verdict v-"+v.toLowerCase());card.style.setProperty("--vc",meta.c);
  var wrap=el("div","ringwrap"),C=2*Math.PI*54,s=svgEl("svg",{viewBox:"0 0 120 120","class":"ring"});
  s.appendChild(svgEl("circle",{"class":"t",cx:60,cy:60,r:54}));
  var pr=svgEl("circle",{"class":"p",cx:60,cy:60,r:54});pr.style.strokeDasharray=C;pr.style.strokeDashoffset=C;s.appendChild(pr);
  wrap.appendChild(s);var pct=el("div","ringmid","0%");wrap.appendChild(pct);card.appendChild(wrap);
  var side=el("div");side.appendChild(el("div","vword",v));side.appendChild(el("div","vsub",meta.sub));
  side.appendChild(el("div","vmeta","For "+profile+". Ring = how well the label was read."));
  var tl=(r.label_type||"unknown")+" label, "+(r.language_detected||"unknown");side.appendChild(el("div","vmeta",tl));
  card.appendChild(side);box.appendChild(card);

  var lt=String(r.label_type||"").toLowerCase(),note="";CATS.forEach(function(c){if(!note&&lt.indexOf(c[0])>=0)note=c[1]});
  if(note)box.appendChild(el("div","banner info",note));
  var re=arr(r.reasons),wa=arr(r.warnings),ig=arr(r.ingredients);
  if(re.length)box.appendChild(listBox("Why this verdict",re));
  if(wa.length)box.appendChild(listBox("Warnings on the label",wa));
  if(ig.length)box.appendChild(listBox("Ingredients found",ig,true));
  if(r.facts)addFacts(box,r.facts,profile);
  box.appendChild(listBox("What this scan cannot confirm",limits(r,conf)));

  var tb=el("section","box");tb.appendChild(el("h2",null,"Exact text the model read"));
  var pre=el("pre","raw");var words=profileWords(profile);
  if(r.text_read)highlight(pre,String(r.text_read),words);else pre.textContent="(nothing was read)";
  tb.appendChild(pre);tb.appendChild(el("div","note",(words.length?"Words from the profile are highlighted. ":"")+"Compare with the real label. If it differs, do not trust the verdict."));
  box.appendChild(tb);

  var ab=el("section","box");
  function btn(t,f){var b=el("button","ghost",t);b.type="button";b.onclick=f;ab.appendChild(b);return b}
  btn("Scan another label",resetScan);
  btn("Copy summary",function(){copySummary(this)});
  if(source==="live"&&img){ab.appendChild(el("div","note","Re-check this same photo for someone else:"));
    var cs=el("div","chips");cs.style.marginTop="6px";PROFILES.forEach(function(p){if(p!==profile){var c=el("button","chip",cap(p));c.type="button";c.onclick=function(){analyze(p)};cs.appendChild(c)}});ab.appendChild(cs)}
  if(TEAM&&source==="live"&&!r.error)btn("Save as offline sample",saveSample);
  box.appendChild(ab);

  requestAnimationFrame(function(){pr.style.strokeDashoffset=C*(1-conf);
    var t0=performance.now();(function f(n){var k=Math.min(1,(n-t0)/1100);pct.textContent=Math.round(conf*100*(1-Math.pow(1-k,3)))+"%";if(k<1)requestAnimationFrame(f)})(t0)});
  if(window.innerWidth<900&&box.scrollIntoView)box.scrollIntoView({behavior:"smooth",block:"start"});
  if(navigator.vibrate)navigator.vibrate(v==="AVOID"?[70,40,70]:30)}

function copySummary(b){
  if(!current)return;var r=current.r,t=["LabelLens result: "+(r.verdict||"CAREFUL")+" for "+current.profile,"Type: "+(r.label_type||"unknown")+", language: "+(r.language_detected||"unknown"),
    "Confidence in reading: "+Math.round((Number(r.confidence)||0)*100)+"%","Reasons: "+arr(r.reasons).join("; "),"Warnings: "+arr(r.warnings).join("; "),"Informational only. Check the label and ask a doctor or pharmacist."].join("\n");
  var ok=function(){b.textContent="Copied"};
  if(navigator.clipboard)navigator.clipboard.writeText(t).then(ok,function(){b.textContent="Copy failed"});else b.textContent="Copy not supported"}

function resetScan(){img=null;$("#preview").removeAttribute("src");$("#vf").classList.remove("has");$("#file").value="";$("#go").disabled=true;say("");window.scrollTo({top:0,behavior:"smooth"})}

function buildHist(){var h=store("ll_hist")||[],box=$("#hist");box.textContent="";$("#histBox").hidden=!h.length;
  h.forEach(function(x){var b=el("button","chip",x.r.verdict+" \u00B7 "+x.profile);b.type="button";b.onclick=function(){showResult(x.r,x.profile,"history")};box.appendChild(b)})}

async function saveSample(){
  if(!current)return;var name=window.prompt("Name for this sample?","")||"";
  try{var r=await fetch("/save_sample",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:name,profile:current.profile,result:current.r})});
    var d=await r.json();say(d.saved?"Saved samples/"+d.saved:(d.error||"Could not save."),d.saved?"":"bad");loadHealth()}catch(e){say("Could not save: "+e.message,"bad")}}

async function loadDemo(){
  var l=$("#demoList");l.textContent="Loading\u2026";
  try{var items=await (await fetch("/samples")).json();l.textContent="";if(!items.length){l.textContent="No saved samples yet.";return}
    items.forEach(function(s){var b=el("button","chip",s.name||"sample");b.type="button";b.onclick=function(){showResult(s.result,s.profile||"adult","sample")};l.appendChild(b)})}
  catch(e){l.textContent="Could not load samples."}}

async function loadHealth(){
  try{HEALTH=await (await fetch("/health")).json()}catch(e){HEALTH={}}
  var s=$("#setup");s.textContent="";var miss=[];
  if(!HEALTH.key)miss.push("GEMINI_API_KEY is not set in the Terminal that runs this app");
  if(!HEALTH.model)miss.push("MODEL_NAME is not set in core.py (line 13)");
  if(miss.length)s.appendChild(el("div","banner warn","Live scans are off: "+miss.join("; ")+". The offline demo still works."))}

/* ===== live camera: behaves like a scanner ===== */
var stream=null,camTimer=null,locked=false,busy=false,prevG=null,okTicks=0,autoOn=true,facing="environment";
var sm=document.createElement("canvas");sm.width=160;sm.height=120;
function camMsg(m){$("#emptyT").textContent="Camera is off";$("#emptyS").textContent=m}
function hint(m){$("#hint").textContent=m}
function stopCam(){clearInterval(camTimer);if(stream){stream.getTracks().forEach(function(t){t.stop()});stream=null}$("#cam").srcObject=null;$("#vf").classList.remove("live","locked")}
async function startCam(){
  if(stream||img)return;
  if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){camMsg("Live camera needs localhost or https. Use Upload photo instead.");return}
  try{
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:facing},width:{ideal:1920},height:{ideal:1080}},audio:false});
    var v=$("#cam");v.srcObject=stream;try{await v.play()}catch(e){}
    $("#vf").classList.add("live");$("#go").disabled=false;$("#go").textContent="Scan now";
    hint("Point at the label and hold steady");clearInterval(camTimer);camTimer=setInterval(tick,250)
  }catch(e){stream=null;camMsg("Camera is blocked or missing ("+(e.name||"error")+"). Allow it in the address bar, or use Upload photo.")}}
function tick(){
  var v=$("#cam");if(!stream||locked||busy||!v.videoWidth)return;
  var c=sm.getContext("2d",{willReadFrequently:true});c.drawImage(v,0,0,160,120);
  var d=c.getImageData(0,0,160,120).data,g=new Float32Array(19200),i,x,y,p,L,lap=0,lap2=0,edges=0,n=0,mot=0;
  for(i=0;i<19200;i++)g[i]=.3*d[i*4]+.59*d[i*4+1]+.11*d[i*4+2];
  for(y=1;y<119;y++)for(x=1;x<159;x++){p=y*160+x;L=4*g[p]-g[p-1]-g[p+1]-g[p-160]-g[p+160];lap+=L;lap2+=L*L;n++;
    if(Math.abs(g[p+1]-g[p-1])+Math.abs(g[p+160]-g[p-160])>60)edges++}
  var sharp=lap2/n-(lap/n)*(lap/n),dens=edges/n;
  if(prevG){for(i=0;i<19200;i+=7)mot+=Math.abs(g[i]-prevG[i]);mot/=2743}else mot=99;
  prevG=g;
  var good=sharp>150&&dens>.06&&mot<6;okTicks=good?okTicks+1:0;
  $("#meterFill").style.width=Math.round(Math.min(1,okTicks/4)*100)+"%";
  hint(mot>=6?"Hold steady":sharp<=150?"Move closer or wait for focus":dens<=.06?"Fill the frame with the label text":"Reading\u2026 hold still");
  if(okTicks>=4&&autoOn)lockAndScan()}
function captureFrame(){
  var v=$("#cam");if(!v.videoWidth)return false;
  var k=Math.min(1,1600/Math.max(v.videoWidth,v.videoHeight)),w=Math.round(v.videoWidth*k),h=Math.round(v.videoHeight*k),c=document.createElement("canvas");
  c.width=w;c.height=h;c.getContext("2d").drawImage(v,0,0,w,h);var u=c.toDataURL("image/jpeg",.9);
  img={b64:u.split(",")[1],mime:"image/jpeg"};$("#preview").src=u;$("#vf").classList.add("has");return true}
function lockAndScan(){locked=true;$("#vf").classList.add("locked");if(navigator.vibrate)navigator.vibrate(40);hint("Got it");if(captureFrame())analyze();else{locked=false;$("#vf").classList.remove("locked")}}
function initCam(){
  $("#flip").onclick=function(){facing=facing==="environment"?"user":"environment";stopCam();startCam()};
  $("#auto").onclick=function(){autoOn=!autoOn;this.textContent="Auto-scan: "+(autoOn?"on":"off");okTicks=0};
  $("#file").addEventListener("change",function(){locked=true});
  startCam()}

function setBusy(b){busy=b;$("#go").disabled=b||(!img&&!stream);$("#go").textContent=b?"Scanning\u2026":(stream&&!img?"Scan now":"Check this label");
  $("#vf").classList.toggle("scanning",b);clearInterval(msgTimer);
  if(b){var i=0;say(MSGS[0]);msgTimer=setInterval(function(){i=(i+1)%MSGS.length;say(MSGS[i])},1400)}else say("")}
function resetScan(){img=null;locked=false;okTicks=0;prevG=null;$("#preview").removeAttribute("src");$("#vf").classList.remove("has","locked");
  $("#file").value="";$("#go").disabled=!stream;$("#go").textContent=stream?"Scan now":"Check this label";say("");hint("");window.scrollTo({top:0,behavior:"smooth"});startCam()}
async function analyze(profile){
  if(!img)return;profile=profile||getProfile();setBusy(true);var data;
  try{var r=await fetch("/scan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image:img.b64,mime:img.mime,profile:profile})});
    data=await r.json();if(!data||typeof data!=="object"||!data.verdict)data=errorResult(data&&data.error?data.error:"Unexpected reply from the server.")}
  catch(e){data=errorResult("Network problem: "+e.message)}
  setBusy(false);showResult(data,profile,"live");
  if(!data.error){var h=store("ll_hist")||[];h.unshift({t:Date.now(),profile:profile,r:data});store("ll_hist",h.slice(0,8));buildHist()}}

/* ===== daily tracker ===== */
var MEALS=["Breakfast","Lunch","Snack","Dinner"],SET=store("ll_set")||{kcal:2000};
var ALERT={kcal:["calories","Eating more than you need, again and again, leads to weight gain and over the years raises the risk of type 2 diabetes and heart disease."],
  sugar:["sugar","Too much sugar, day after day, raises the risk of weight gain, type 2 diabetes and tooth decay."],
  sodium:["salt (sodium)","Too much salt, day after day, raises blood pressure and the risk of heart disease."],
  sat:["saturated fat","Too much saturated fat, day after day, raises cholesterol and the risk of heart disease."]};
function LIM(){var k=SET.kcal||2000;return{kcal:k,sugar:Math.round(k*.1/4),sodium:2000,sat:Math.round(k*.1/9)}}
function dayKey(){return new Date().toLocaleDateString("en-CA")}
function today(){return (store("ll_log")||{})[dayKey()]||[]}
function totals(){var t={kcal:0,sugar:0,sodium:0,sat:0};today().forEach(function(e){t.kcal+=e.kcal||0;t.sugar+=e.sugar||0;t.sodium+=e.sodium||0;t.sat+=e.sat||0});return t}
function over(t){var L=LIM();return Object.keys(ALERT).filter(function(k){return t[k]>L[k]})}
function defMeal(){var h=new Date().getHours();return h<11?"Breakfast":h<16?"Lunch":h<19?"Snack":"Dinner"}
function addEntry(e){
  var before=over(totals()),Lg=store("ll_log")||{},k=dayKey();(Lg[k]=Lg[k]||[]).push(e);store("ll_log",Lg);
  var t=totals(),L=LIM();over(t).filter(function(x){return before.indexOf(x)<0}).forEach(function(x){
    toast("Your "+ALERT[x][0]+" limit for today is exceeded ("+Math.round(t[x])+" of "+L[x]+"). "+ALERT[x][1])});
  showAlerts()}
function delEntry(id){var Lg=store("ll_log")||{},k=dayKey();Lg[k]=(Lg[k]||[]).filter(function(e){return e.id!==id});store("ll_log",Lg);showAlerts();renderToday()}
function showAlerts(){var a=$("#alerts");a.textContent="";var o=over(totals());
  if(o.length){var t=totals(),L=LIM();a.appendChild(el("div","banner err","Over today's limit: "+o.map(function(k){return ALERT[k][0]+" ("+Math.round(t[k])+" of "+L[k]+")"}).join(", ")+". Open the Today tab."))}}
function toast(m){var t=el("div","toast",m);document.body.appendChild(t);t.onclick=function(){t.remove()};setTimeout(function(){t.remove()},10000);speak(m);if(navigator.vibrate)navigator.vibrate([120,60,120])}
function bar(v,l){var p=l?v/l:0,d=el("div","pbar"),i=el("i",p>1?"h":p>.8?"m":"");i.style.width=Math.min(100,p*100)+"%";d.appendChild(i);return d}
function fld(fr,lbl,node){var w=el("label",null,lbl);w.appendChild(node);fr.appendChild(w);return node}
function numIn(v){var i=el("input");i.type="number";i.value=v;return i}
function selIn(o,v){var s=el("select");o.forEach(function(t){var x=document.createElement("option");x.value=t;x.textContent=t;s.appendChild(x)});if(v)s.value=v;return s}

function proposeLog(parent,lg){
  var d=el("div","row");d.appendChild(el("b",null,lg.name+" ("+lg.meal+")"));
  d.appendChild(el("span",null,"About "+lg.kcal+" kcal, sugar "+lg.sugar+" g, sodium "+lg.sodium+" mg, saturated fat "+lg.sat+" g. An estimate, not measured."));
  var b=el("button","ghost","Add to today");b.type="button";
  b.onclick=function(){addEntry({id:Date.now(),name:lg.name,meal:lg.meal,qty:1,kcal:lg.kcal,sugar:lg.sugar,sodium:lg.sodium,sat:lg.sat,est:true});b.disabled=true;b.textContent="Added";if(!$("#tab-today").hidden)renderToday()};
  d.appendChild(b);parent.appendChild(d)}

function renderToday(){
  var box=$("#tab-today");box.textContent="";var L=LIM(),T=totals();
  var s=el("section","box");s.appendChild(el("h2",null,"Today, "+dayKey()));
  [["kcal","Calories","kcal"],["sugar","Sugar","g"],["sodium","Sodium","mg"],["sat","Saturated fat","g"]].forEach(function(k){
    var r=el("div","row");r.appendChild(el("b",null,k[1]+": "+Math.round(T[k[0]])+" of "+L[k[0]]+" "+k[2]));r.appendChild(bar(T[k[0]],L[k[0]]));s.appendChild(r)});
  s.appendChild(el("p","note","Sugar limit: under 10% of calories. Salt: under 2000 mg sodium. Saturated fat: under 10% of calories (general WHO-style guidance). Your calorie target is an estimate for adults."));
  box.appendChild(s);

  var qa=el("section","box");qa.appendChild(el("h2",null,"I ate something without a label"));
  var qi=el("input","qin");qi.placeholder='e.g. "pav bhaji and one chai with sugar"';var out=el("div"),go=el("button","cta","Estimate and log");go.type="button";
  go.onclick=async function(){var v=qi.value.trim();if(!v)return;go.disabled=true;go.textContent="Estimating\u2026";out.textContent="";
    try{var r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages:[{role:"user",content:"I just ate this for "+defMeal()+": "+v+". Estimate one normal serving and log it."}],context:ctx()})});
      var d=await r.json();if(d.log)proposeLog(out,d.log);else out.appendChild(el("p","note",d.reply||d.error||"Could not estimate. Try again."))}
    catch(e){out.appendChild(el("p","note","Network problem: "+e.message))}
    go.disabled=false;go.textContent="Estimate and log"};
  qa.appendChild(qi);qa.appendChild(go);qa.appendChild(out);box.appendChild(qa);

  var lb=el("section","box");lb.appendChild(el("h2",null,"Eaten today"));var items=today();
  if(!items.length)lb.appendChild(el("p","note","Nothing logged yet. Scan a label or add food above."));
  items.forEach(function(e){var r=el("div","logrow"),t=el("div");t.appendChild(el("b",null,e.meal+": "+e.name+(e.qty&&e.qty!==1?" x"+e.qty:"")));
    t.appendChild(el("div","note",e.kcal+" kcal, sugar "+e.sugar+" g, sodium "+e.sodium+" mg"+(e.est?" (estimate)":"")));r.appendChild(t);
    var x=el("button","ghost","Remove");x.type="button";x.onclick=function(){delEntry(e.id)};r.appendChild(x);lb.appendChild(r)});
  box.appendChild(lb);

  var st=el("section","box");st.appendChild(el("h2",null,"My daily calories: "+L.kcal+" kcal"));var fr=el("div","frm");
  var age=fld(fr,"Age",numIn(SET.age||25)),sex=fld(fr,"Sex",selIn(["Male","Female"],SET.sex)),wt=fld(fr,"Weight (kg)",numIn(SET.wt||65)),
    ht=fld(fr,"Height (cm)",numIn(SET.ht||170)),ac=fld(fr,"Activity",selIn(["Mostly sitting","Light","Moderate","Very active"],SET.act));
  st.appendChild(fr);var cb=el("button","ghost","Calculate my calories");cb.type="button";
  cb.onclick=function(){var b=10*wt.value+6.25*ht.value-5*age.value+(sex.value==="Male"?5:-161),f=[1.2,1.375,1.55,1.725][ac.selectedIndex];
    var k=Math.max(1200,Math.min(4000,Math.round(b*f/50)*50));SET={kcal:k,age:age.value,sex:sex.value,wt:wt.value,ht:ht.value,act:ac.value};store("ll_set",SET);showAlerts();renderToday()};
  st.appendChild(cb);st.appendChild(el("p","note","Uses the Mifflin-St Jeor estimate. For adults only. Children, pregnancy and medical conditions need a doctor or dietitian."));box.appendChild(st)}

/* ===== nutrition card on the result ===== */
function addFacts(box,f,profile){
  if(f.error){box.appendChild(el("div","banner warn","Nutrition details were not available for this scan. The verdict above still applies."));return}
  var ps=f.per_serving||{},L=LIM(),T=totals(),sug=ps.added_sugar_g!=null?ps.added_sugar_g:ps.sugar_g;
  var has=ps.calories!=null||sug!=null||ps.sodium_mg!=null||ps.sat_fat_g!=null;
  var c=el("section","box");c.appendChild(el("h2",null,(f.product_name||"Nutrition")+" \u2013 per serving"+(f.serving_size?" ("+f.serving_size+")":"")));
  if(has){
    var vals={kcal:ps.calories,sugar:sug,sodium:ps.sodium_mg,sat:ps.sat_fat_g},g=el("div","tiles");
    [["kcal","Calories","kcal"],["sugar",ps.added_sugar_g!=null?"Added sugar":"Sugar","g"],["sodium","Sodium","mg"],["sat","Saturated fat","g"]].forEach(function(t){
      var v=vals[t[0]],d=el("div","tile");d.appendChild(el("b",null,v==null?"not printed":v+" "+t[2]));d.appendChild(el("span",null,t[1]));
      if(v!=null){d.appendChild(el("div","note",Math.round(v/L[t[0]]*100)+"% of daily limit"));d.appendChild(bar(v,L[t[0]]))}g.appendChild(d)});
    c.appendChild(g);
    Object.keys(vals).forEach(function(k){if(vals[k]!=null&&T[k]+vals[k]>L[k]){var d=el("div","lv lw");
      d.appendChild(el("b",null,"Eating this takes today's "+ALERT[k][0]+" to "+Math.round((T[k]+vals[k])/L[k]*100)+"% of your limit."));c.appendChild(d)}});
    var meal=defMeal(),qty=1,mb=el("div","chips"),sel=selIn(["0.5","1","1.5","2","3"],"1");mb.style.margin="12px 0 6px";
    var draw=function(){mb.textContent="";MEALS.forEach(function(m){var b=el("button","chip"+(m===meal?" on":""),m);b.type="button";b.onclick=function(){meal=m;draw()};mb.appendChild(b)})};draw();
    c.appendChild(mb);var row=el("div","chatrow");sel.style.width="90px";sel.onchange=function(){qty=Number(sel.value)};
    var add=el("button","ghost","Add to today's log");add.type="button";
    add.onclick=function(){var q=Number(sel.value)||1;addEntry({id:Date.now(),name:f.product_name||"Scanned item",meal:meal,qty:q,kcal:Math.round((ps.calories||0)*q),sugar:Math.round((sug||0)*q*10)/10,sodium:Math.round((ps.sodium_mg||0)*q),sat:Math.round((ps.sat_fat_g||0)*q*10)/10});add.disabled=true;add.textContent="Added to today"};
    row.appendChild(el("span","note","Servings eaten:"));row.appendChild(sel);row.appendChild(add);c.appendChild(row)}
  else c.appendChild(el("p","note","No nutrition table was readable. Photograph the nutrition panel too."));
  box.appendChild(c);
  if((f.claim_checks||[]).length){var k=el("section","box");k.appendChild(el("h2",null,"Front claims vs the printed label"));
    f.claim_checks.forEach(function(x){var d=el("div","lv l"+(x.level==="warn"?"w":x.level==="ok"?"o":"n"));d.appendChild(el("b",null,"\u201C"+x.claim+"\u201D"));d.appendChild(el("div",null,x.finding||""));k.appendChild(d)});
    k.appendChild(el("p","note","Compared only with the text printed on this pack. It cannot know the real recipe."));box.appendChild(k)}
  if((f.concerning||[]).length){var z=el("section","box");z.appendChild(el("h2",null,"Ingredients worth a second look"));
    f.concerning.forEach(function(x){var d=el("div","lv ln");d.appendChild(el("b",null,x.name));d.appendChild(el("div",null,x.why||""));z.appendChild(d)});
    z.appendChild(el("p","note","General information. Whether it matters depends on how much and how often."));box.appendChild(z)}}

/* ===== assistant with voice ===== */
var chatHist=[],speakOn=false,VL={English:"en-IN",Hindi:"hi-IN",Marathi:"mr-IN"};
function vlang(){var s=$("#vlang");return VL[s?s.value:"English"]}
function speak(t){if(!speakOn||!window.speechSynthesis)return;var u=new SpeechSynthesisUtterance(String(t));u.lang=vlang();speechSynthesis.cancel();speechSynthesis.speak(u)}
function addMsg(role,text){var m=el("div","msg "+role,text),lg=$("#chatlog");lg.appendChild(m);lg.scrollTop=lg.scrollHeight;return m}
function ctx(){var c=current&&current.r?current.r:null,f=c&&c.facts&&!c.facts.error?c.facts:null;
  return{limits:LIM(),today_totals:totals(),today_log:today().map(function(e){return e.meal+": "+e.name+" ("+e.kcal+" kcal)"}),
    last_scan:c?{profile:current.profile,verdict:c.verdict,type:c.label_type,reasons:arr(c.reasons).slice(0,4),warnings:arr(c.warnings).slice(0,4),facts:f}:null}}
async function sendChat(text){
  text=String(text||"").trim();if(!text)return;addMsg("u",text);chatHist.push({role:"user",content:text});var w=addMsg("a","Thinking\u2026");
  try{var r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages:chatHist.slice(-8),context:ctx()})});var d=await r.json();
    w.textContent=d.reply||d.error||"Sorry, I could not answer. Try again.";chatHist.push({role:"assistant",content:w.textContent});speak(w.textContent);
    if(d.log)proposeLog($("#chatlog"),d.log)}
  catch(e){w.textContent="Network problem: "+e.message}
  var lg=$("#chatlog");lg.scrollTop=lg.scrollHeight}
function listen(){var R=window.SpeechRecognition||window.webkitSpeechRecognition;if(!R){addMsg("a","Voice input works in Chrome or Edge. You can type instead.");return}
  var r=new R();r.lang=vlang();r.onresult=function(e){sendChat(e.results[0][0].transcript)};r.onerror=function(){addMsg("a","I could not hear that. Check microphone permission.")};r.start()}
function buildAI(){
  var b=$("#tab-ai");b.textContent="";var s=el("section","box");s.appendChild(el("h2",null,"Ask LabelLens"));var lg=el("div","chat");lg.id="chatlog";s.appendChild(lg);
  var q=el("div","chips");q.style.marginTop="10px";["Is my day on track?","Explain my last scan simply","What can I drink instead of sugary juice?","I ate pav bhaji for breakfast"].forEach(function(t){
    var c=el("button","chip",t);c.type="button";c.onclick=function(){sendChat(t)};q.appendChild(c)});s.appendChild(q);
  var row=el("div","chatrow"),inp=el("input");inp.placeholder="Type or use the mic. Any language.";
  inp.onkeydown=function(e){if(e.key==="Enter"&&inp.value.trim()){sendChat(inp.value);inp.value=""}};
  var mic=el("button","ghost","Mic");mic.type="button";mic.onclick=listen;var vl=selIn(["English","Hindi","Marathi"]);vl.id="vlang";
  var sp=el("button","ghost","Voice reply: off");sp.type="button";sp.onclick=function(){speakOn=!speakOn;sp.textContent="Voice reply: "+(speakOn?"on":"off");if(!speakOn&&window.speechSynthesis)speechSynthesis.cancel()};
  [inp,mic,vl,sp].forEach(function(n){row.appendChild(n)});s.appendChild(row);
  s.appendChild(el("p","note","The assistant explains and estimates. It does not diagnose and never gives medicine or pesticide doses. Ask a doctor or pharmacist about health problems."));
  b.appendChild(s);addMsg("a","Hi! I can explain a label, check how your day is going, and log what you eat. Ask me anything, in any language.")}

buildNav();buildChips();buildHist();loadHealth();buildAI();showAlerts();initCam();
$("#custom").addEventListener("input",function(){$("#chips").classList.toggle("off",!!$("#custom").value.trim())});
$("#file").addEventListener("change",function(e){loadFile(e.target.files&&e.target.files[0])});
$("#go").addEventListener("click",function(){if(!img){if(!stream||!captureFrame())return;locked=true}analyze()});
$("#demoBtn").addEventListener("click",loadDemo);
$("#clearHist").addEventListener("click",function(){store("ll_hist",[]);buildHist()});
["dragenter","dragover"].forEach(function(ev){$("#vf").addEventListener(ev,function(e){e.preventDefault();$("#vf").classList.add("drag")})});
["dragleave","drop"].forEach(function(ev){$("#vf").addEventListener(ev,function(e){e.preventDefault();$("#vf").classList.remove("drag")})});
$("#vf").addEventListener("drop",function(e){loadFile(e.dataTransfer&&e.dataTransfer.files&&e.dataTransfer.files[0])});
</script></body></html>
"""


# ---------------------------------------------------------------- server
def load_samples():
    out = []
    if SAMPLES_DIR.exists():
        for p in sorted(SAMPLES_DIR.glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(d.get("result"), dict):
                    out.append(d)
            except Exception:
                continue
    return out


def save_sample(name, profile, result):
    SAMPLES_DIR.mkdir(exist_ok=True)
    n = len(list(SAMPLES_DIR.glob("*.json"))) + 1
    if n > MAX_SAMPLES:
        raise ValueError("Too many samples saved.")
    path = SAMPLES_DIR / f"{n:02d}.json"
    payload = {"name": (str(name)[:60] or f"sample {n}"), "profile": str(profile)[:200], "result": result}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path.name


class Handler(BaseHTTPRequestHandler):
    server_version = "LabelLens"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/samples":
            self._json(200, load_samples())
        elif path == "/health":
            self._json(200, {
                "ok": True,
                "key": bool(os.environ.get("GEMINI_API_KEY")),
                "model": not str(core.MODEL_NAME).startswith("PASTE_"),
                "samples": len(load_samples()),
            })
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            size = int(self.headers.get("Content-Length") or 0)
            if size <= 0 or size > MAX_BODY:
                raise ValueError("Request size is not allowed.")
            body = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("Bad request.")
        except Exception as exc:
            self._json(400, {"error": str(exc)[:200]})
            return

        if path == "/analyze":
            try:
                raw = base64.b64decode(str(body.get("image") or ""))
            except Exception:
                self._json(200, core._error_result("The photo could not be decoded."))
                return
            self._json(200, core.analyze_label(
                raw, str(body.get("mime") or "image/jpeg"), str(body.get("profile") or "adult")))
        elif path == "/scan":
            try:
                raw = base64.b64decode(str(body.get("image") or ""))
            except Exception:
                self._json(200, core._error_result("The photo could not be decoded."))
                return
            mime = str(body.get("mime") or "image/jpeg")
            prof = str(body.get("profile") or "adult")
            with ThreadPoolExecutor(2) as ex:
                f1 = ex.submit(core.analyze_label, raw, mime, prof)
                f2 = ex.submit(extras.facts, raw, mime, prof)
                res, fx = f1.result(), f2.result()
            if isinstance(res, dict):
                res["facts"] = fx
            self._json(200, res)
        elif path == "/chat":
            self._json(200, extras.chat(body.get("messages"), body.get("context")))
        elif path == "/save_sample":
            try:
                result = body.get("result")
                if not isinstance(result, dict):
                    raise ValueError("No result to save.")
                self._json(200, {"saved": save_sample(body.get("name", ""), body.get("profile", "adult"), result)})
            except Exception as exc:
                self._json(400, {"error": str(exc)[:200]})
        else:
            self._json(404, {"error": "Not found"})


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY is not set. Live scans will not work (offline demo still does).")
    if str(core.MODEL_NAME).startswith("PASTE_"):
        print("WARNING: MODEL_NAME is not set in core.py. Live scans will not work.")
    try:
        server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    except OSError:
        print(f"Port {PORT} is busy. Press Ctrl+C in the Terminal window running the old app, then try again.")
        return
    url = f"http://localhost:{PORT}"
    print(f"\nLabelLens is running:  {url}")
    ip = lan_ip()
    if ip:
        print(f"On your phone (same Wi-Fi):  http://{ip}:{PORT}")
    print(f"Team tools (save samples):  {url}/?team=1\nPress Ctrl+C to stop.\n")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

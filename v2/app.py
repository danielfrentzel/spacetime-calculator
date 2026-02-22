#!/usr/bin/env python3
import logging
import math
import os as _os
import re
import sys as _sys

from flask import Blueprint, Flask, render_template_string, request

# Make the project root importable so HourCalculator can be found whether
# v2/app.py is run standalone or imported from the parent app.
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)
from hour_calculator import HourCalculator

log = logging.getLogger('STC')
log.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setLevel(logging.DEBUG)
_handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%H:%M:%S'))
log.addHandler(_handler)
log.propagate = True

app = Flask(__name__)
v2_bp = Blueprint('v2', __name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Time Tracker</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0e1117;
    --surface: #161b22;
    --surface2: #1c2333;
    --border: #2a3142;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --accent-glow: rgba(88, 166, 255, 0.15);
    --green: #3fb950;
    --green-bg: rgba(63, 185, 80, 0.1);
    --red: #f85149;
    --red-bg: rgba(248, 81, 73, 0.1);
    --yellow: #d29922;
    --yellow-bg: rgba(210, 153, 34, 0.1);
    --purple: #a371f7;
    --purple-bg: rgba(163, 113, 247, 0.1);
    --radius: 10px;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Outfit', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
  }

  .container { width: 100%; max-width: 760px; }

  h1 {
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
    background: linear-gradient(135deg, var(--accent), #a371f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .subtitle {
    color: var(--text-dim);
    font-size: 0.95rem;
    margin-bottom: 6px;
    font-weight: 300;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 24px;
  }

  label {
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--text-dim);
    margin-bottom: 10px;
  }

  textarea {
    width: 100%;
    min-height: 160px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    padding: 14px 16px;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
    line-height: 1.7;
  }

  textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
  textarea::placeholder { color: #6b7585; }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    padding: 11px 28px;
    background: var(--accent);
    color: #fff;
    font-family: 'Outfit', sans-serif;
    font-size: 0.95rem;
    font-weight: 500;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn:hover { filter: brightness(1.15); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(88,166,255,0.3); }
  .btn:active { transform: translateY(0); }
  .btn svg { width: 16px; height: 16px; }

  .results-section { animation: fadeIn 0.35s ease; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .section-title {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-dim);
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }

  .id-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--surface2);
    border-radius: 8px;
    margin-bottom: 8px;
  }

  .id-name { font-family: 'DM Mono', monospace; font-weight: 500; font-size: 0.95rem; }

  .id-hours {
    font-family: 'DM Mono', monospace;
    font-size: 0.95rem;
    color: var(--green);
    background: var(--green-bg);
    padding: 4px 12px;
    border-radius: 6px;
  }

  .total-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    margin-top: 4px;
    border-top: 1px solid var(--border);
  }

  .total-label { font-weight: 600; font-size: 0.95rem; }

  .total-hours {
    font-family: 'DM Mono', monospace;
    font-weight: 600;
    font-size: 1rem;
    color: var(--accent);
  }

  .break-item, .target-item {
    padding: 10px 16px;
    border-radius: 8px;
    margin-bottom: 6px;
    font-family: 'DM Mono', monospace;
    font-size: 0.88rem;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .break-item {
    background: var(--yellow-bg);
    color: var(--yellow);
    border-left: 3px solid var(--yellow);
  }

  .target-item {
    background: var(--purple-bg);
    color: var(--purple);
    border-left: 3px solid var(--purple);
  }

  .icon-sm { width: 15px; height: 15px; flex-shrink: 0; }

  .section-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }

  .section-title-row .section-title {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }

  .copy-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: 'Outfit', sans-serif;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .copy-btn:hover { border-color: var(--accent); color: var(--accent); }
  .copy-btn.copied { border-color: var(--green); color: var(--green); }
  .copy-btn svg { width: 13px; height: 13px; }

  .show-more-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
    padding: 8px 20px;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-dim);
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  .show-more-btn:hover { border-color: var(--accent); color: var(--accent); }

  .report-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: transparent;
    border: 1px solid rgba(248, 81, 73, 0.3);
    border-radius: 8px;
    color: var(--text-dim);
    font-family: 'Outfit', sans-serif;
    font-size: 0.8rem;
    font-weight: 400;
    cursor: pointer;
    transition: all 0.2s;
  }
  .report-btn:hover { border-color: var(--red); color: var(--red); }

  .version-header {
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 24px;
    margin-bottom: 14px;
    padding-bottom: 8px;
  }

  .info-box {
    background: var(--accent-glow);
    border: 1px solid rgba(88, 166, 255, 0.3);
    border-radius: var(--radius);
    padding: 16px 20px;
    color: var(--accent);
    font-size: 0.9rem;
    margin-bottom: 24px;
    animation: fadeIn 0.35s ease;
  }

  .info-box .info-title {
    font-weight: 600;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .info-box .info-detail {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    opacity: 0.85;
    margin-top: 6px;
  }

  .warning-box {
    background: var(--yellow-bg);
    border: 1px solid rgba(210, 153, 34, 0.3);
    border-radius: var(--radius);
    padding: 16px 20px;
    color: var(--yellow);
    font-size: 0.9rem;
    margin-bottom: 24px;
    animation: fadeIn 0.35s ease;
  }

  .warning-box .warning-title {
    font-weight: 600;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .warning-box .warning-detail {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    opacity: 0.85;
    margin-top: 6px;
  }

  .error-box {
    background: var(--red-bg);
    border: 1px solid rgba(248,81,73,0.3);
    border-radius: var(--radius);
    padding: 16px 20px;
    color: var(--red);
    font-size: 0.9rem;
    margin-bottom: 24px;
    animation: fadeIn 0.35s ease;
  }

  .hint {
    margin-top: 12px;
    font-size: 0.78rem;
    color: #6b7585;
    font-family: 'DM Mono', monospace;
    line-height: 1.6;
  }
</style>
</head>
<body>
<div class="container">
  <h1>Time Calculator</h1>
  <p style="font-size:0.85rem;margin-bottom:28px;">
    <a href="/v2/help" style="color:var(--accent);">Help</a>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="/" style="color:var(--accent);">Version 1</a>
  </p>
  <p class="subtitle">Calculate total hours worked per ID.</p>

  <form method="POST" class="card">
    <label for="input">Time Entries</label>
    <textarea id="input" name="input" placeholder="id1 8-8:30, 9-9:30, 11-1&#10;id2 8:30-9, 9:30-11, 1-1:42">{{ input_text }}</textarea>
    <div class="hint">
      Format: &lt;id&gt; &lt;start time&gt;-&lt;end time&gt;, …&nbsp;&nbsp;|&nbsp;&nbsp;Times: 8, 8:30, 8.5&nbsp;&nbsp;|&nbsp;&nbsp;AM/PM: 8a, 8am, 3p, 3pm&nbsp;&nbsp;|&nbsp;&nbsp;In-line comments: # // &lt;…&gt;&nbsp;&nbsp;|&nbsp;&nbsp;Total hour target format: \=8.0
    </div>
    <button type="submit" class="btn" title="Shift+Enter or Ctrl+Enter">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
      Calculate
    </button>
  </form>

  {% if error %}
  <div class="error-box">{{ error }}</div>
  {% endif %}

  {% if order_error %}
  <div class="warning-box">
    <div class="warning-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      Disagreement between calculation methods — unordered mode failed
    </div>
    <div class="warning-detail">{{ order_error }}</div>
    {% if results is not none %}<div class="warning-detail">Showing ordered results below. Please review the results for accuracy.</div>{% endif %}
  </div>
  {% endif %}

  {% if order_warning %}
  <div class="warning-box">
    <div class="warning-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      Disagreement between calculation methods — input order may be ambiguous
    </div>
    <div class="warning-detail">
      Unordered: {% for id, hrs in order_warning.items() %}{{ id }} = {{ "%.1f"|format(hrs) }} hrs{% if not loop.last %},&nbsp;&nbsp;{% endif %}{% endfor %}
    </div>
    <div class="warning-detail">Showing ordered results below. Please review the results for accuracy.</div>
  </div>
  {% endif %}

  {% if detected_ids %}
  <div class="info-box">
    <div class="info-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="8"/><line x1="12" y1="12" x2="12" y2="16"/></svg>
      Multi-word ID{{ 's' if detected_ids|length > 1 else '' }} detected
    </div>
    {% for id in detected_ids %}
    <div class="info-detail">ID detected as: "{{ id }}"</div>
    {% endfor %}
  </div>
  {% endif %}

  {% if results %}
  <div class="results-section">
    <div class="card">
      <div class="section-title-row">
        <span class="section-title">Hours by ID</span>
        <button class="copy-btn" onclick="copyResults(this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span class="copy-label">Copy</span>
        </button>
      </div>
      {% for id, hours in results.items() %}
      <div class="id-row">
        <span class="id-name">{{ id }}</span>
        <span class="id-hours">{{ "%.1f"|format(hours) }} hrs</span>
      </div>
      {% endfor %}
      <div class="total-row">
        <span class="total-label">Total</span>
        <span class="total-hours">{{ "%.1f"|format(total) }} hrs</span>
      </div>
    </div>

    {% if breaks %}
    <div class="card">
      <div class="section-title">Breaks</div>
      {% for b in breaks %}
      <div class="break-item">
        <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {{ b }}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    {% if target_time or target_achieved_at %}
    <div class="card">
      <div class="section-title">Target Time</div>
      {% if target_achieved_at %}
      <div class="target-item" style="background:var(--green-bg);color:var(--green);border-left-color:var(--green);">
        <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        Done since {{ target_achieved_at }}
      </div>
      {% else %}
      <div class="target-item">
        <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        Done by {{ target_time }}
      </div>
      {% endif %}
    </div>
    {% endif %}

  </div>
  {% endif %}

  {% set has_detail = results is not none or v2_unordered is not none or v2_unordered_error or v1_ordered is not none or v1_unordered is not none or v1_ordered_error or v1_unordered_error %}
  {% if has_detail %}
  <div class="results-section">
    <button class="show-more-btn" id="show-more-btn" onclick="toggleMore()">
      {% if methods_differ %}Show less{% else %}Show more{% endif %}
    </button>
    <div id="more-details" style="display:{% if methods_differ %}block{% else %}none{% endif %};">

      {% set all_errored = results is none and v2_unordered is none and v1_ordered is none and v1_unordered is none %}
      <p style="font-size:0.85rem;margin-bottom:16px;margin-top:12px;{% if all_errored %}color:var(--red);{% elif methods_differ %}color:var(--yellow);{% else %}color:var(--green);{% endif %}">
        {% if all_errored %}✕ All calculation methods failed. Please verify the time entries.
        {% elif methods_differ %}⚠ Results differ between calculation methods — review calculations for accuracy.<br>
        <span style="padding-left:1.2em;">Review time entries and order lines by the first start time or specify AM/PM explicitly. See <a href="/v2/help" style="color:var(--accent);">Help</a> for more information.</span>
        {% else %}✓ All calculation methods agree.{% endif %}
      </p>

      <div class="version-header" style="color:var(--accent);border-bottom:1px solid rgba(88,166,255,0.25);">Version 2 Calculations</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:8px;">

        <div class="card">
          {% if results is not none %}
          <div class="section-title-row">
            <span class="section-title">Ordered</span>
            <button class="copy-btn" onclick="copyResults(this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>
            {% for id, hours in results.items() %}
            <div class="id-row">
              <span class="id-name">{{ id }}</span>
              <span class="id-hours">{{ "%.1f"|format(hours) }} hrs</span>
            </div>
            {% endfor %}
            <div class="total-row">
              <span class="total-label">Total</span>
              <span class="total-hours">{{ "%.1f"|format(total) }} hrs</span>
            </div>
            {% if breaks %}
            <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px;">
              <div style="font-size:0.7rem;font-weight:500;text-transform:uppercase;letter-spacing:1.2px;color:var(--text-dim);margin-bottom:8px;">Breaks</div>
              {% for b in breaks %}
              <div class="break-item">
                <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {{ b }}
              </div>
              {% endfor %}
            </div>
            {% endif %}
          {% else %}
          <div class="section-title">Ordered</div>
            <p style="color:var(--red);font-size:0.85rem;margin-top:8px;">{{ error }}</p>
          {% endif %}
        </div>

        <div class="card">
          {% if v2_unordered is not none %}
          <div class="section-title-row">
            <span class="section-title">Unordered</span>
            <button class="copy-btn" onclick="copyResults(this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>
            {% for id, hrs in v2_unordered.items() %}
            <div class="id-row">
              <span class="id-name">{{ id }}</span>
              <span class="id-hours">{{ "%.1f"|format(hrs) }} hrs</span>
            </div>
            {% endfor %}
            <div class="total-row">
              <span class="total-label">Total</span>
              <span class="total-hours">{{ "%.1f"|format(v2_unordered_total) }} hrs</span>
            </div>
            {% if v2_unordered_breaks %}
            <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px;">
              <div style="font-size:0.7rem;font-weight:500;text-transform:uppercase;letter-spacing:1.2px;color:var(--text-dim);margin-bottom:8px;">Breaks</div>
              {% for b in v2_unordered_breaks %}
              <div class="break-item">
                <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {{ b }}
              </div>
              {% endfor %}
            </div>
            {% endif %}
          {% else %}
          <div class="section-title">Unordered</div>
            <p style="color:var(--red);font-size:0.85rem;margin-top:8px;">{{ v2_unordered_error }}</p>
          {% endif %}
        </div>

      </div>

      <div class="version-header" style="color:var(--accent);border-bottom:1px solid rgba(163,113,247,0.25);">Version 1 Calculations</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">

        <div class="card">
          {% if v1_ordered is not none %}
          <div class="section-title-row">
            <span class="section-title">Ordered</span>
            <button class="copy-btn" onclick="copyResults(this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>
            {% for id, hrs in v1_ordered.items() %}
            <div class="id-row">
              <span class="id-name">{{ id }}</span>
              <span class="id-hours">{{ "%.1f"|format(hrs) }} hrs</span>
            </div>
            {% endfor %}
            <div class="total-row">
              <span class="total-label">Total</span>
              <span class="total-hours">{{ "%.1f"|format(v1_ordered_total) }} hrs</span>
            </div>
            {% if v1_ordered_breaks %}
            <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px;">
              <div style="font-size:0.7rem;font-weight:500;text-transform:uppercase;letter-spacing:1.2px;color:var(--text-dim);margin-bottom:8px;">Breaks</div>
              {% for b in v1_ordered_breaks %}
              <div class="break-item">
                <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {{ b }}
              </div>
              {% endfor %}
            </div>
            {% endif %}
          {% else %}
          <div class="section-title">Ordered</div>
            <p style="color:var(--red);font-size:0.85rem;margin-top:8px;">{{ v1_ordered_error }}</p>
          {% endif %}
        </div>

        <div class="card">
          {% if v1_unordered is not none %}
          <div class="section-title-row">
            <span class="section-title">Unordered</span>
            <button class="copy-btn" onclick="copyResults(this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>
            {% for id, hrs in v1_unordered.items() %}
            <div class="id-row">
              <span class="id-name">{{ id }}</span>
              <span class="id-hours">{{ "%.1f"|format(hrs) }} hrs</span>
            </div>
            {% endfor %}
            <div class="total-row">
              <span class="total-label">Total</span>
              <span class="total-hours">{{ "%.1f"|format(v1_unordered_total) }} hrs</span>
            </div>
            {% if v1_unordered_breaks %}
            <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px;">
              <div style="font-size:0.7rem;font-weight:500;text-transform:uppercase;letter-spacing:1.2px;color:var(--text-dim);margin-bottom:8px;">Breaks</div>
              {% for b in v1_unordered_breaks %}
              <div class="break-item">
                <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {{ b }}
              </div>
              {% endfor %}
            </div>
            {% endif %}
          {% else %}
          <div class="section-title">Unordered</div>
            <p style="color:var(--red);font-size:0.85rem;margin-top:8px;">{{ v1_unordered_error }}</p>
          {% endif %}
        </div>

      </div>
    </div>
    {% endif %}
  </div>

  {% if error or v2_unordered_error or v1_ordered_error or v1_unordered_error %}
  <div style="margin-top:8px;text-align:right;">
    <button class="report-btn" onclick="reportBug()">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c4.97 0 9-4.03 9-9s-4.03-9-9-9-9 4.03-9 9 4.03 9 9 9z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
      Report a bug
    </button>
  </div>
  {% endif %}
</div>

<script>
document.getElementById('input').addEventListener('keydown', function(e) {
  if ((e.shiftKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    this.closest('form').submit();
  }
});

function reportBug() {
  const input = document.getElementById('input').value;
  const subject = encodeURIComponent('Time Calculator Error Report');
  const body = encodeURIComponent('An error occured when submitting the following input.\n\n\n' + input);
  window.location.href = 'mailto:7daniel49@gmail.com?subject=' + subject + '&body=' + body;
}

function toggleMore() {
  const btn = document.getElementById('show-more-btn');
  const details = document.getElementById('more-details');
  const expanded = details.style.display !== 'none';
  details.style.display = expanded ? 'none' : 'block';
  btn.textContent = expanded ? 'Show more' : 'Show less';
}

function copyResults(btn) {
  const card = btn.closest('.card');
  const rows = card.querySelectorAll('.id-row');
  const total = card.querySelector('.total-hours');
  let lines = [];
  rows.forEach(row => {
    const id = row.querySelector('.id-name').textContent.trim();
    const hrs = row.querySelector('.id-hours').textContent.trim();
    lines.push(id + ' = ' + hrs);
  });
  lines.push('Total = ' + total.textContent.trim());
  navigator.clipboard.writeText(lines.join(',  ')).then(() => {
    const label = btn.querySelector('.copy-label');
    btn.classList.add('copied');
    label.textContent = 'Copied!';
    setTimeout(() => { btn.classList.remove('copied'); label.textContent = 'Copy'; }, 2000);
  });
}
</script>
</body>
</html>
"""

HELP_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Time Tracker – Help</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0e1117;
    --surface: #161b22;
    --border: #2a3142;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --radius: 10px;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Outfit', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
  }

  .container { width: 100%; max-width: 760px; }

  h1 {
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
    background: linear-gradient(135deg, var(--accent), #a371f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .nav {
    margin-bottom: 28px;
    font-size: 0.9rem;
  }

  .nav a {
    color: var(--accent);
    text-decoration: none;
  }

  .nav a:hover { text-decoration: underline; }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px 32px;
  }

  pre {
    font-family: 'DM Mono', monospace;
    font-size: 0.88rem;
    white-space: pre-wrap;
    line-height: 1.75;
    color: var(--text);
  }

  a { color: var(--accent); }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
  <h1>Help</h1>
  <div class="nav"><a href="/v2">&larr; Home</a></div>
  <div class="card">
    <pre>
This tool was created to simplify the summation of time intervals worked on different charge numbers. It will notify of breaks taken throughout the day and invalid time entries (overlapping entries or non ordered entries).

The time ranges in every line are required to be dashed intervals, comma separated and sorted. An identifier, followed by a space is required at the beginning of each time entry line. See examples below.

Time can be passed in with minutes or frational hours. The fractional hours will be calculated from minutes with precision through the summation. Totals are rounded to the nearest tenth and the subtime entries are ensured to add up to the exact rounded total. In order to do this, subtimes are adjusted to remove any rounding discrepancy. A preference is given to adjust subtimes closest to rounding the other way and then to subtimes with a larger amount of time worked. Rest assured that subtime adjustments do not short the employee any time worked and give the most accurate breakdown of time worked per category while not under or over representing the total hours worked.

The time is computed with two different methods. The first method assumes that the time inputs are ordered by the first time in each line. The second method assumes that lines starting with a PM time are encoded with a 'p' or written in 24 hour format (ie. 'id1 1p-2' or 'id2 13-2' rather than 'id3 1-2'). Note, it is only necessary to encode the first time in a line if it is indeed a PM time. If the two calculation methods compute different results for breaks or totals, both respective results are displayed. It is recommended to format inputs according to one of the calculation methods.


    Example inputs:

        id1 8-8:30, 9-9:30, 11-1, 1:42-3:12, 4:12-6
        id2 8:30-9, 9:30-11, 1-1:42, 3:12-4:12

        or

        id1 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6
        id2 8.5-9, 9.5-11, 1-1.7, 3.2-4.2

        or

        id1 8-12, 4-5
        id2 12-4
        id3 6p-9

        or

        id1 8-12, 4-5
        id2 12-4
        id3 18-9


    Example outputs:

        totals
        id1 = 3.7 hrs
        id2 = 6.3 hrs
        total: 10.0

        or

        breaks
        12:00p-1:00p = 1.0 hr

        totals
        id1 = 4.0 hr
        total: 4.0 hr

        or

        totals
        id1 = 5.0 hr
        id2 = 4.0 hr
        id3 = 3.0 hr
        total: 12.0 hr


    Encodings:

    Target hours can be specified by encoding a new line with \= or \==
        id1 8-5p
        \=9.6

        Target time: 5:34pm

    Inline comment notes are supported in three formats
        id1 8-10  # comment
        id2 10-11 //comment
        id3 11-6 &lt;comment&gt;


If you notice a calculation error, please <a href="mailto:7daniel49@gmail.com">contact</a> the maintainer with the time input or submit a pull request.

<a href="https://github.com/danielfrentzel/spacetime-calculator">Source</a>
    </pre>
  </div>
</div>
</body>
</html>
"""


@v2_bp.route("/help")
def help():
    return render_template_string(HELP_TEMPLATE)


def _parse_time(t_str):
    """Parse a time string to decimal hours.
    Supports H, H.H, H:MM with optional a/am/p/pm suffix."""
    t_str = t_str.strip()
    am = False
    pm = False

    if t_str.endswith('am'):
        t_str = t_str[:-2]
        am = True
    elif t_str.endswith('pm'):
        t_str = t_str[:-2]
        pm = True
    elif t_str.endswith('a'):
        t_str = t_str[:-1]
        am = True
    elif t_str.endswith('p'):
        t_str = t_str[:-1]
        pm = True

    if ':' in t_str:
        parts = t_str.split(':')
        hours = float(parts[0])
        minutes = round(float(parts[1]) / 60, 3)
    else:
        hours = float(t_str)
        minutes = 0

    if am and int(hours) == 12:
        hours = 0
    elif pm and int(hours) != 12:
        hours += 12

    return hours + minutes


def _frac_to_hhmm(frac):
    """Decimal hours → 'H:MM' (24h). e.g. 13.5 → '13:30'"""
    h = math.floor(frac)
    m = round((frac % 1) * 60)
    return f"{h}:{m:02d}"


def _frac_to_12h(frac):
    """Decimal hours → 'H:MMam/pm'. e.g. 13.567 → '1:34pm'"""
    h = math.floor(frac)
    m = round((frac % 1) * 60)
    if h > 12:
        return f"{h % 12}:{m:02d}pm"
    elif h == 12:
        return f"12:{m:02d}pm"
    else:
        return f"{h}:{m:02d}am"


def _strip_inline_comments(lines):
    result = []
    for line in lines:
        if '#' in line:
            line = line[:line.find('#')].strip()
        if '//' in line:
            line = line[:line.find('//')].strip()
        if '<' in line:
            line = line[:line.find('<')].strip()
        result.append(line)
    return result


def _parse_encoding(lines):
    """Extract \\= target-hours lines. Returns (remaining_lines, target_hours)."""
    target_hours = 0
    remaining = []
    for line in lines:
        if line[:3] == '\\==':
            try:
                target_hours = float(line[3:])
            except ValueError:
                pass
        elif line[:2] == '\\=':
            try:
                target_hours = float(line[2:])
            except ValueError:
                pass
        else:
            remaining.append(line)
    return remaining, target_hours


def _format_ranges(ranges_list):
    """Parse ['start-end', ...] into [[start_dec, end_dec], ...]."""
    result = []
    for rng in ranges_list:
        parts = rng.split('-')
        start = _parse_time(parts[0])
        end = _parse_time(parts[1])
        result.append([start, end])
    return result


def _split_line(line):
    """Split a line into (id, ranges_str) by finding the first digit-dash pattern.
    Returns (None, None) if no time range is found."""
    match = re.search(r'\s+(?=\d[\d.:]*(am?|pm?)?-)', line)
    if not match:
        return None, None
    return line[:match.start()], line[match.end():]


def _explicit_start_ids(lines):
    """Return the set of IDs whose first start time has an explicit AM/PM suffix.
    These IDs are already unambiguous and should not have +12 inferred."""
    explicit = set()
    for line in lines:
        if not line:
            continue
        str_id, ranges_str = _split_line(line)
        if str_id is None:
            continue
        first_time = ranges_str.split(',')[0].strip().split('-')[0].strip()
        if re.search(r'\d(am|pm|a|p)$', first_time, re.IGNORECASE) or re.match(r'^0\d', first_time):
            explicit.add(str_id)
    return explicit


def _convert_ordered_starts(hours_dict, explicit_ids=None):
    """If any line's start < first line's start, mark afternoon and add 12 to its first interval.
    IDs in explicit_ids already have unambiguous AM/PM — skip the +12 offset for those."""
    explicit_ids = explicit_ids or set()
    log.debug('  [ordered] converting ordered starts  (explicit AM/PM IDs skipped: %s)',
              sorted(explicit_ids) if explicit_ids else 'none')
    afternoon = False
    last_start = None
    for code, data in hours_dict.items():
        if not last_start:
            last_start = data[0][0]
        if last_start > data[0][0]:
            afternoon = True
        if afternoon and code not in explicit_ids:
            log.debug('  [ordered]   %s: start %.3f → %.3f (+12 inferred PM)', code, data[0][0], data[0][0] + 12)
            data[0] = [data[0][0] + 12, data[0][1]]


def _convert_mil_times(hours_dict):
    """Convert each ID's intervals to monotonic 24h times in place."""
    for code, data in hours_dict.items():
        mil_data = []
        afternoon = False
        for time in data:
            if mil_data and time[0] < mil_data[-1][1]:
                afternoon = True
            elif time[1] < time[0]:
                afternoon = True

            if not afternoon:
                new_time = time
            else:
                if time[1] < time[0] and time[1] <= 12:
                    new_time = [time[0], time[1] + 12]
                else:
                    new_time = [
                        time[0] + 12 if time[0] <= 12 else time[0],
                        time[1] + 12 if time[1] <= 12 else time[1],
                    ]

            if new_time[0] > 24 or new_time[1] > 24:
                raise ValueError(f"Interval for '{code}' exceeds 24 hours after conversion. "
                                 f"Hours can only be calculated within a single day.")
            if new_time[1] < new_time[0]:
                raise ValueError(f"Interval for '{code}' spans past midnight after conversion "
                                 f"({_frac_to_hhmm(new_time[0])}–{_frac_to_hhmm(new_time[1])} next day). "
                                 f"Hours can only be calculated within a single day.")
            if mil_data and new_time[0] < mil_data[-1][1]:
                raise ValueError(f"Interval for '{code}' overlaps a previous interval after conversion "
                                 f"({_frac_to_hhmm(new_time[0])}–{_frac_to_hhmm(new_time[1])} starts before "
                                 f"{_frac_to_hhmm(mil_data[-1][0])}–{_frac_to_hhmm(mil_data[-1][1])} ends). "
                                 f"Time entries may cross midnight — hours can only be calculated within a single day.")
            mil_data.append(new_time)
        hours_dict[code] = mil_data


def _next_charge(hours_dict):
    """Return the ID whose next interval starts earliest (ties: last one wins)."""
    nxt = None
    nxt_start = None
    for code, data in hours_dict.items():
        start = data[0][0]
        if not nxt:
            nxt = code
            nxt_start = start
        elif start <= nxt_start:
            nxt = code
            nxt_start = start
    return nxt


def _format_break_display(b):
    """Format a break triple ['H:MM','H:MM','dur'] for HTML display."""
    start_str, end_str, dur_str = b
    sh, sm = map(int, start_str.split(':'))
    eh, em = map(int, end_str.split(':'))
    dur = float(dur_str)
    dur_min = round(dur * 60)

    def to_12h(h, m):
        period = 'AM' if h < 12 else 'PM'
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {period}"

    return f"{to_12h(sh, sm)} \u2013 {to_12h(eh, em)}  ({dur_min} min / {dur:.2f} hrs)"


def process_input(text, ordered=False):
    """Parse time entries and return (results_dict, breaks_list, metadata_dict).

    results_dict : {'id': hours, ..., '$total': total}
    breaks_list  : [['H:MM', 'H:MM', 'dur_str'], ...]   (24h start/end, decimal dur)
    metadata_dict: {'target_time': 'H:MMam/pm' or None}
    """
    text = text.replace('\\n', '\n')
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    lines = _strip_inline_comments(lines)
    lines, target_hours = _parse_encoding(lines)

    # Build hours dict: id → [[start_dec, end_dec], ...]
    hours = {}
    charges = {}
    detected_ids = []
    for line in lines:
        if not line:
            continue
        line = line.rstrip(',')
        str_id, ranges_str = _split_line(line)
        if str_id is None:
            raise ValueError(f"Invalid line (missing time ranges): '{line}'")
        if ' ' in str_id and str_id not in detected_ids:
            detected_ids.append(str_id)
        ranges_list = [r.strip() for r in ranges_str.split(',')]
        ranges = _format_ranges(ranges_list)
        if str_id in hours:
            hours[str_id] += ranges  # combine duplicate IDs
        else:
            hours[str_id] = ranges
            charges[str_id] = 0

    mode = 'ordered' if ordered else 'unordered'
    log.debug('  [%s] starting calculation', mode)

    if ordered:
        _convert_ordered_starts(hours, explicit_ids=_explicit_start_ids(lines))
    _convert_mil_times(hours)

    # Snapshot the latest end time across all IDs (used for target time calc)
    last_time_snapshot = -1
    for code, data in hours.items():
        end_time = data[-1][1]
        if end_time > last_time_snapshot:
            last_time_snapshot = end_time

    # Walk all intervals in chronological order, charge durations, record breaks
    hours_copy = {code: [list(t) for t in data] for code, data in hours.items()}
    breaks = []
    last_time = None

    while hours_copy:
        nxt_chg = _next_charge(hours_copy)
        time = hours_copy[nxt_chg][0]
        duration = round(abs(time[1] - time[0]), 3)

        if last_time and time[0] < last_time:
            raise RuntimeError(f'Double charging or invalid range: {time[0]}-{last_time}. '
                               f'Ensure lines starting with a PM time are written in 24 hour format.')

        if last_time and last_time != time[0]:
            breaks.append([
                _frac_to_hhmm(round(last_time, 3)),
                _frac_to_hhmm(round(time[0], 3)),
                str(round(abs(time[0] - last_time), 2)),
            ])

        if len(hours_copy[nxt_chg]) > 1:
            hours_copy[nxt_chg] = hours_copy[nxt_chg][1:]
        else:
            del hours_copy[nxt_chg]

        last_time = time[1]
        charges[nxt_chg] += duration

    log.debug('  [%s] breaks: %s', mode, breaks if breaks else 'none')

    # Compute exact vs rounded totals for rounding adjustment
    total_exact = 0
    total_round = 0
    diffs = []
    for chg, duration in charges.items():
        total_exact += duration
        total_round += round(duration, 1)
        diff = round(duration - round(duration, 1), 4)
        diffs.append([chg, diff])

    # Target time: how much longer until target_hours is met
    target_time = None
    target_achieved_at = None
    if target_hours:
        unfulfilled = target_hours - total_exact - 0.05 + 0.01
        if unfulfilled > 0:
            target_time = _frac_to_12h(last_time_snapshot + unfulfilled)
        else:
            target_achieved_at = _frac_to_12h(last_time_snapshot + unfulfilled)

    # Distribute rounding error so per-ID values stay consistent with global total
    diffs = sorted(diffs, key=lambda d: charges[d[0]], reverse=True)
    total_diff = round(round(total_exact, 1) - total_round, 4)

    while abs(total_diff) >= 0.1:
        diffs = sorted(diffs, key=lambda d: abs(d[1]), reverse=True)
        for diff in diffs:
            if total_diff > 0:
                if diff[1] > 0:
                    charges[diff[0]] = round(charges[diff[0]] + 0.05, 2)
                    diff[1] = 0
                    total_diff -= 0.1
                    break
                else:
                    continue
            else:
                if diff[1] < 0:
                    charges[diff[0]] = round(charges[diff[0]] - 0.05, 2)
                    diff[1] = 0
                    total_diff += 0.1
                    break
                else:
                    continue

    results = {}
    total = 0
    for chg, duration in charges.items():
        results[chg] = round(duration, 1)
        total += round(duration, 1)
    results['$total'] = round(total, 1)

    # log.debug('  [%s] exact total:   %.4f', mode, total_exact)
    # log.debug('  [%s] rounded total: %.4f', mode, total_round)
    # log.debug('  [%s] final total:   %.4f', mode, total)
    log.debug('  [%s] exact, rounded, final total:   %.2f, %.2f, %.2f', mode, total_exact, total_round, total)
    log.debug('  [%s] per-ID results: %s', mode, {k: v for k, v in results.items() if k != '$total'})

    return results, breaks, {
        'target_time': target_time,
        'target_achieved_at': target_achieved_at,
        'detected_ids': detected_ids
    }


@v2_bp.route("/", methods=["GET", "POST"])
def index():
    input_text = ""
    results = None
    total = 0
    breaks = []
    target_time = None
    target_achieved_at = None
    detected_ids = []
    error = None
    order_warning = None
    order_error = None
    v1_ordered = None
    v1_ordered_total = 0
    v1_ordered_breaks = []
    v1_ordered_error = None
    v1_unordered = None
    v1_unordered_total = 0
    v1_unordered_breaks = []
    v1_unordered_error = None
    v2_unordered = None
    v2_unordered_total = 0
    v2_unordered_breaks = []
    v2_unordered_error = None
    methods_differ = False

    if request.method == "POST":
        input_text = request.form.get("input", "")
        try:
            log.debug('=' * 72)
            log.debug('NEW REQUEST')
            log.debug('Raw input:\n%s', input_text)
            log.debug('-' * 72)

            raw, raw_breaks, metadata = process_input(input_text, ordered=True)

            total = raw.pop('$total', 0)
            results = raw
            target_time = metadata.get('target_time')
            target_achieved_at = metadata.get('target_achieved_at')
            detected_ids = metadata.get('detected_ids', [])
            breaks = [_format_break_display(b) for b in raw_breaks]

        except (ValueError, RuntimeError) as e:
            error = str(e)
            log.debug('ERROR: %s', e)

        # v2 unordered — runs independently so a primary failure doesn't block it
        try:
            raw_ord, raw_ord_breaks, _ = process_input(input_text, ordered=False)
            v2_unordered = {k: v for k, v in raw_ord.items() if k != '$total'}
            v2_unordered_total = raw_ord.get('$total', 0)
            v2_unordered_breaks = [_format_break_display(b) for b in raw_ord_breaks]
            if results is not None and (v2_unordered != results or v2_unordered_total != total):
                order_warning = dict(v2_unordered)
                order_warning['Total'] = v2_unordered_total
        except RuntimeError as e:
            v2_unordered_error = str(e)
        except ValueError as e:
            order_error = str(e)
            v2_unordered_error = str(e)

        # Run v1 (HourCalculator) calculations on the same input
        v1_input = input_text.replace('\\n', '\n')
        try:
            h, b, _ = HourCalculator(v1_input).calculate(ordered=True)
            v1_ordered_total = h.pop('$total', 0)
            v1_ordered = h
            v1_ordered_breaks = [_format_break_display(brk) for brk in b]
        except Exception as e:
            v1_ordered_error = str(e)
        try:
            h, b, _ = HourCalculator(v1_input).calculate(ordered=False)
            v1_unordered_total = h.pop('$total', 0)
            v1_unordered = h
            v1_unordered_breaks = [_format_break_display(brk) for brk in b]
        except Exception as e:
            v1_unordered_error = str(e)

        # 4-method comparison summary log
        all_ids_set = set()
        for _m in [results, v2_unordered, v1_unordered, v1_ordered]:
            if _m is not None:
                all_ids_set.update(_m.keys())
        all_ids = list(all_ids_set)

        if all_ids or any([error, v2_unordered_error, v1_ordered_error, v1_unordered_error]):
            log.debug('-' * 72)
            log.debug('SUMMARY')
            col_w = max((len(k) for k in all_ids), default=4) + 2
            col_v = 12
            sep = '-' * (col_w + col_v * 3 + 18)
            log.debug('  %-*s  %-*s  %-*s  %-*s  %s', col_w, 'ID', col_v, 'V2 Ord', col_v, 'V2 Unord', col_v,
                      'V1 Unord', 'V1 Ord')
            log.debug('  %s', sep)
            for id_ in all_ids:
                v2u = f'{results[id_]:.1f}' if results and id_ in results else ('ERR' if error else 'n/a')
                v2o = f'{v2_unordered[id_]:.1f}' if v2_unordered and id_ in v2_unordered else (
                    'ERR' if v2_unordered_error else 'n/a')
                v1u = f'{v1_unordered[id_]:.1f}' if v1_unordered and id_ in v1_unordered else (
                    'ERR' if v1_unordered_error else 'n/a')
                v1o = f'{v1_ordered[id_]:.1f}' if v1_ordered and id_ in v1_ordered else (
                    'ERR' if v1_ordered_error else 'n/a')
                numeric = [float(v) for v in [v2u, v2o, v1u, v1o] if v not in ('ERR', 'n/a')]
                row_differs = len(set(numeric)) > 1
                log.debug('  %-*s  %-*s  %-*s  %-*s  %s%s', col_w, id_, col_v, v2u, col_v, v2o, col_v, v1u, v1o,
                          '  ← differs' if row_differs else '')
            log.debug('  %s', sep)
            v2u_t = f'{total:.1f}' if results is not None else ('ERR' if error else 'n/a')
            v2o_t = f'{v2_unordered_total:.1f}' if v2_unordered is not None else (
                'ERR' if v2_unordered_error else 'n/a')
            v1u_t = f'{v1_unordered_total:.1f}' if v1_unordered is not None else (
                'ERR' if v1_unordered_error else 'n/a')
            v1o_t = f'{v1_ordered_total:.1f}' if v1_ordered is not None else ('ERR' if v1_ordered_error else 'n/a')
            log.debug('  %-*s  %-*s  %-*s  %-*s  %s', col_w, 'Total', col_v, v2u_t, col_v, v2o_t, col_v, v1u_t, v1o_t)
            log.debug('  %s', sep)

            # Compute methods_differ for auto-expand
            id_differs = False
            for id_ in all_ids:
                vals = [m[id_] for m in [results, v2_unordered, v1_unordered, v1_ordered] if m is not None and id_ in m]
                if len(set(vals)) > 1:
                    id_differs = True
            total_vals = [
                t for m, t in [(results,
                                total), (v2_unordered,
                                         v2_unordered_total), (v1_unordered,
                                                               v1_unordered_total), (v1_ordered, v1_ordered_total)]
                if m is not None
            ]
            total_differs = len(set(total_vals)) > 1
            any_error = bool(error or v2_unordered_error or v1_ordered_error or v1_unordered_error)
            methods_differ = id_differs or total_differs or any_error

            if not methods_differ:
                log.debug('  All 4 methods agree.')
            else:
                parts = []
                disagree_ids = [
                    id_ for id_ in all_ids if len(
                        set(m[id_] for m in [results, v2_unordered, v1_unordered, v1_ordered]
                            if m is not None and id_ in m)) > 1
                ]
                if disagree_ids:
                    parts.append('IDs differ: ' + ', '.join(disagree_ids))
                if total_differs:
                    parts.append(f'totals differ ({v2u_t} / {v2o_t} / {v1u_t} / {v1o_t})')
                if any_error:
                    err_methods = [
                        name for name, err in [('V2 Ord', error), (
                            'V2 Unord', v2_unordered_error), ('V1 Unord',
                                                              v1_unordered_error), ('V1 Ord', v1_ordered_error)] if err
                    ]
                    parts.append('errors in: ' + ', '.join(err_methods))
                log.debug('  Methods disagree — %s', '; '.join(parts))
        log.debug('=' * 72)

    return render_template_string(
        HTML_TEMPLATE,
        input_text=input_text,
        results=results,
        total=total,
        breaks=breaks,
        target_time=target_time,
        target_achieved_at=target_achieved_at,
        detected_ids=detected_ids,
        error=error,
        order_warning=order_warning,
        order_error=order_error,
        v1_ordered=v1_ordered,
        v1_ordered_total=v1_ordered_total,
        v1_ordered_breaks=v1_ordered_breaks,
        v1_ordered_error=v1_ordered_error,
        v1_unordered=v1_unordered,
        v1_unordered_total=v1_unordered_total,
        v1_unordered_breaks=v1_unordered_breaks,
        v2_unordered=v2_unordered,
        v2_unordered_total=v2_unordered_total,
        v2_unordered_breaks=v2_unordered_breaks,
        v2_unordered_error=v2_unordered_error,
        methods_differ=methods_differ,
        v1_unordered_error=v1_unordered_error,
    )


if __name__ == "__main__":
    app.register_blueprint(v2_bp)
    app.run(debug=True, host="0.0.0.0", port=5001)

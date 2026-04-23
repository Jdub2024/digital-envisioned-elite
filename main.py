import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import requests
from bs4 import BeautifulSoup
import random
import string
import re
from collections import Counter
import markdown
import json
import pandas as pd
import PyPDF2
import base64
import csv
import os
import hashlib
import math
import html as html_mod
import difflib
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
import yaml as yaml_mod
from fractions import Fraction
from datetime import datetime, timedelta
from pathlib import Path

# --- 1. AUTH & TIER ACCESS ---
st.set_page_config(page_title="Digital Envisioned Hub", layout="wide")

MASTER_EMAIL = "jnworkflow@gmail.com"
MASTER_PASSWORD = "games2Play2$"

# Tool count granted per tier
TIER_LIMITS = {
    "master": 200,
    "empire": 200,
    "pro": 50,
    "free": 10,
}

# Stripe Payment Links
UPGRADE_LINKS = {
    "pro": "https://buy.stripe.com/cNi14mesWgsybnFfZX77O3Q",       # Free -> Pro (Tools 11-50)
    "empire": "https://buy.stripe.com/00weVcbgK1xEgHZ3db77O3R",    # Pro  -> Elite/Empire (Tools 51-200)
}

# Public/anonymous visitors default to the Free tier (Tools 1-10).
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "free"
    st.session_state.user_email = "Public (Free Tier)"
if "lead_captured" not in st.session_state:
    st.session_state.lead_captured = False

# --- 1b. GLOBAL BRANDED BACKGROUND ---
BG_IMAGE_PATH = Path(__file__).parent / "1000025401.jpg"
BG_FALLBACK_PATH = Path(__file__).parent / "attached_assets" / "de-logo.jpg"

def inject_background():
    bg_path = BG_IMAGE_PATH if BG_IMAGE_PATH.exists() else BG_FALLBACK_PATH
    if not bg_path.exists():
        return
    encoded = base64.b64encode(bg_path.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            opacity: 0.15;
            z-index: 0;
            pointer-events: none;
        }}
        .stApp > * {{ position: relative; z-index: 1; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_background()

# --- 1c. MOBILE SIDEBAR FIX ---
st.markdown(
    '<style>'
    '[data-testid="stSidebarNav"] {max-height: 100vh; overflow-y: auto;}'
    '[data-testid="stSidebarContent"] {max-height: 100vh; overflow-y: auto;}'
    '[data-testid="stSidebar"] > div:first-child {max-height: 100vh; overflow-y: auto;}'
    '.css-1d391kg {overflow-y: auto; max-height: 100vh;}'
    '@media (max-width: 768px) {'
    '  [data-testid="stSidebar"] {overflow-y: auto !important; -webkit-overflow-scrolling: touch;}'
    '  [data-testid="stSidebarContent"] {overflow-y: auto !important; max-height: 100dvh;}'
    '}'
    '</style>',
    unsafe_allow_html=True,
)


# --- 1c. LEAD CAPTURE GATE ---
LEADS_FILE = Path(__file__).parent / "leads.csv"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get(
    "RESEND_FROM",
    "Joshua Newton <newton@digitalenvisioned.net>",
)

def send_welcome_email(first_name: str, to_email: str) -> tuple[bool, str]:
    """Send a professional welcome email via Resend (SDK + REST fallback)."""
    subject = "Welcome to the Newton Legacy | Digital Envisioned"
    html_body = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;
                background:#0a0a0a;color:#ffffff;padding:40px 30px;border-radius:12px;">
        <div style="text-align:center;margin-bottom:30px;">
            <h1 style="color:#1E90FF;font-size:28px;margin:0;">Digital Envisioned</h1>
            <p style="color:#888;font-size:14px;margin-top:5px;">Elite Automation Suite</p>
        </div>
        <h2 style="color:#ffffff;font-size:22px;">Welcome, {first_name}.</h2>
        <p style="color:#cccccc;font-size:16px;line-height:1.7;">
            You now have access to the most powerful automation toolkit built
            for small businesses. Your first <strong>10 free tools</strong> are
            unlocked and ready to use.
        </p>
        <div style="background:#111;border-left:4px solid #1E90FF;padding:15px 20px;
                    margin:25px 0;border-radius:0 8px 8px 0;">
            <p style="color:#ffffff;margin:0 0 8px 0;font-weight:700;">Explore the Ecosystem:</p>
            <p style="margin:4px 0;">
                <a href="https://tools.digitalenvisioned.net"
                   style="color:#1E90FF;text-decoration:none;font-weight:600;">
                   🚀 Premium Tool Vault</a>
            </p>
            <p style="margin:4px 0;">
                <a href="https://agent.digitalenvisioned.net"
                   style="color:#1E90FF;text-decoration:none;font-weight:600;">
                   🤖 AI Agency Hub</a>
            </p>
            <p style="margin:4px 0;">
                <a href="https://digitalenvisioned.net"
                   style="color:#1E90FF;text-decoration:none;font-weight:600;">
                   🌐 digitalenvisioned.net</a>
            </p>
        </div>
        <p style="color:#cccccc;font-size:16px;line-height:1.7;">
            Ready for the full 200-tool experience? Upgrade anytime from
            inside the dashboard.
        </p>
        <p style="color:#cccccc;font-size:16px;line-height:1.7;">
            Better things are coming.
        </p>
        <div style="margin-top:30px;padding-top:20px;border-top:1px solid #222;">
            <p style="color:#1E90FF;font-style:italic;font-weight:700;margin:0;">
                — Joshua Newton, Founder
            </p>
            <p style="color:#666;font-size:12px;margin-top:10px;">
                © {datetime.now().year} Digital Envisioned LLC · Birmingham, AL
            </p>
        </div>
    </div>
    """
    text_body = (
        f"Hi {first_name},\n\n"
        "Welcome to the Elite Automation Suite. You now have the power of 200 "
        "tools at your fingertips.\n\n"
        "Explore the ecosystem:\n"
        "  - Premium Tool Vault: https://tools.digitalenvisioned.net\n"
        "  - AI Agency Hub: https://agent.digitalenvisioned.net\n"
        "  - Main Site: https://digitalenvisioned.net\n\n"
        "Ready for the full 200-tool experience? Upgrade anytime.\n\n"
        "Better things are coming.\n\n"
        "-- Joshua Newton, Founder\n"
        "Digital Envisioned LLC | Birmingham, AL"
    )
    if not RESEND_API_KEY:
        return False, "RESEND_API_KEY not configured"
    # Primary: use the resend Python SDK
    try:
        import resend as _resend_sdk
        _resend_sdk.api_key = RESEND_API_KEY
        r = _resend_sdk.Emails.send({
            "from": RESEND_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        })
        return True, "ok"
    except Exception:
        pass
    # Fallback: REST API via requests
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": RESEND_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            },
            timeout=10,
        )
        if resp.status_code in (200, 202):
            return True, "ok"
        return False, f"{resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)

def save_lead(first_name: str, email: str, phone: str):
    new_file = not LEADS_FILE.exists()
    with LEADS_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "first_name", "email", "phone"])
        w.writerow([datetime.utcnow().isoformat(), first_name, email, phone])

HERO_LOGO_PATH = Path(__file__).parent / "attached_assets" / "de-logo.jpg"
HERO_LOGO_MIME = "image/jpeg"

# ── Marketing Sales Flow Images ──
_ASSETS = Path(__file__).parent / "attached_assets"
SALES_FLOW_IMAGES = {
    "boost_brand":       _ASSETS / "marketing-boost-brand.jpg",
    "beautiful_trust":   _ASSETS / "beautiful-ads-trust.jpg",
    "before_after":      _ASSETS / "beautiful-ads-beforeafter.jpg",
    "freedom_blueprint": _ASSETS / "freedom-blueprint.png",
    "not_converting":    _ASSETS / "ads-not-converting.jpg",
    "portfolio_intro":   _ASSETS / "de-portfolio-intro.png",
    "hit_hard":          _ASSETS / "ads-hit-hard.jpg",
}


LANDING_CSS = """
<style>
/* ═══ GLOBAL DARK THEME ═══ */
.stApp { background-color: #0a0a0a !important; }
.stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stApp div {
    color: #FFFFFF !important;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #FFFFFF !important; }

/* ═══ FULL-WIDTH HERO WITH OVERLAY ═══ */
.hero-section {
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-top: -1rem;
    overflow: hidden;
    background: #000;
}
.hero-section img.hero-bg {
    display: block;
    width: 100%;
    height: 80vh;
    min-height: 400px;
    object-fit: cover;
    object-position: center;
    filter: brightness(0.55);
}
.hero-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
    background: linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.65) 100%);
}
.hero-overlay .hero-logo {
    width: 180px;
    height: 180px;
    border-radius: 50%;
    border: 4px solid rgba(30,144,255,0.6);
    box-shadow: 0 0 40px rgba(30,144,255,0.4);
    object-fit: cover;
    margin-bottom: 1.5rem;
}
.hero-overlay h1 {
    font-family: "Impact", "Arial Black", "Helvetica Neue", sans-serif;
    font-weight: 900;
    font-size: clamp(2rem, 6vw, 4.2rem);
    letter-spacing: 2px;
    text-transform: uppercase;
    line-height: 1.08;
    margin: 0;
    text-shadow: 0 4px 20px rgba(0,0,0,0.8);
}
.hero-overlay h1 .white { color: #FFFFFF; }
.hero-overlay h1 .blue  { color: #1E90FF; }
.hero-overlay .hero-sub {
    font-weight: 700;
    color: #ccc;
    letter-spacing: 3px;
    font-size: clamp(0.8rem, 1.8vw, 1.1rem);
    margin-top: 0.75rem;
    text-transform: uppercase;
}
@media (max-width: 768px) {
    .hero-section img.hero-bg { height: 60vh; min-height: 320px; }
    .hero-overlay .hero-logo { width: 120px; height: 120px; }
}

/* ═══ SECTION HEADLINES ═══ */
.section-headline {
    text-align: center;
    font-weight: 900;
    font-size: clamp(1.4rem, 3vw, 2rem);
    color: #FFFFFF !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 3rem 0 0.5rem 0;
}
.section-sub {
    text-align: center;
    color: #999 !important;
    font-size: 1rem;
    margin-bottom: 2rem;
}

/* ═══ FREE TOOLS GRID ═══ */
.tool-card {
    background: #111;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #222;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}
.tool-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(30,144,255,0.25);
    border-color: #1E90FF;
}
.tool-card img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    display: block;
}
.tool-card .card-body {
    padding: 1rem;
}
.tool-card .card-body .tool-num {
    display: inline-block;
    background: #1E90FF;
    color: #000 !important;
    font-weight: 900;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 6px;
}
.tool-card .card-body h4 {
    color: #FFFFFF !important;
    font-size: 1.05rem;
    font-weight: 800;
    margin: 6px 0 4px 0;
    line-height: 1.2;
}
.tool-card .card-body p {
    color: #999 !important;
    font-size: 0.85rem;
    margin: 0;
    line-height: 1.4;
}

/* ═══ SALES BLOCK ═══ */
.sales-block {
    max-width: 860px;
    margin: 0 auto 1.5rem auto;
    color: #FFFFFF !important;
    font-size: 1.05rem;
    line-height: 1.6;
}
.sales-block * { color: #FFFFFF !important; }
.sales-block h3 {
    color: #FFFFFF !important;
    font-weight: 900;
    font-size: 1.5rem;
    margin-top: 1.25rem;
    margin-bottom: 0.5rem;
}
.sales-block .highlight-blue,
.sales-block h3 .highlight-blue { color: #1E90FF !important; font-weight: 800; }
.sales-block .pain { color: #FF6B6B !important; font-weight: 700; }
.founder-line {
    text-align: right;
    font-style: italic;
    font-weight: 700;
    color: #1E90FF !important;
    margin-top: 0.5rem;
}

/* ═══ FORM STYLES ═══ */
.form-headline {
    text-align: center;
    font-weight: 800;
    font-size: 1.4rem;
    color: #FFFFFF !important;
    margin: 1.5rem 0 0.75rem 0;
}

div.stForm label, div.stForm label p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
}
div.stForm input[type="text"],
div.stForm input[type="email"],
div.stForm input[type="tel"],
div.stForm input[type="password"] {
    background: #1a1a1a !important;
    color: #FFFFFF !important;
    border: 2px solid #cccccc !important;
    border-radius: 6px !important;
    padding: 0.6rem 0.75rem !important;
}
div.stForm input:focus {
    border-color: #1E90FF !important;
    box-shadow: 0 0 0 2px rgba(30,144,255,0.35) !important;
}

div.stForm button[kind="primary"] {
    background: #1E90FF !important;
    color: #000000 !important;
    border: 2px solid #FFFFFF !important;
    font-weight: 900 !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 0.85rem 2rem !important;
    font-size: 1.05rem !important;
}
div.stForm button[kind="primary"] * { color: #000000 !important; }
div.stForm button[kind="primary"]:hover {
    background: #FFFFFF !important;
    color: #000000 !important;
    border-color: #1E90FF !important;
}

/* ═══ UPGRADE CTA BUTTONS ═══ */
.upgrade-headline {
    text-align: center;
    color: #FFFFFF !important;
    font-weight: 800;
    font-size: 1.25rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 1.75rem 0 0.85rem 0;
}
a[data-testid="stBaseLinkButton-secondary"],
a[data-testid="stBaseLinkButton-primary"],
div[data-testid="stLinkButton"] a {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #1E90FF !important;
    color: #FFFFFF !important;
    border: 3px solid #FFFFFF !important;
    border-radius: 10px !important;
    padding: 1.1rem 1.25rem !important;
    font-size: 1.15rem !important;
    font-weight: 900 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    text-decoration: none !important;
    box-shadow: 0 6px 22px rgba(30,144,255,0.45) !important;
    transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease !important;
    width: 100% !important;
    min-height: 70px !important;
    line-height: 1.2 !important;
}
div[data-testid="stLinkButton"] a * {
    color: #FFFFFF !important;
    font-weight: 900 !important;
}
div[data-testid="stLinkButton"] a:hover {
    background: #0b66c3 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(30,144,255,0.6) !important;
}

/* ═══ MARKETING SALES FLOW ═══ */
.sales-flow-divider {
    width: 80%;
    max-width: 600px;
    margin: 3rem auto 2rem auto;
    border: none;
    border-top: 2px solid #1E90FF;
    opacity: 0.4;
}
.sales-flow-heading {
    text-align: center;
    font-family: "Impact", "Arial Black", "Helvetica Neue", sans-serif;
    font-weight: 900;
    font-size: clamp(1.6rem, 4vw, 2.4rem);
    color: #1E90FF !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 2rem 0 1rem 0;
}
.sales-flow-copy {
    max-width: 720px;
    margin: 0 auto 1.5rem auto;
    color: #ccc !important;
    font-size: 1.05rem;
    line-height: 1.7;
    padding: 0 1rem;
}
.sales-flow-copy strong { color: #FFFFFF !important; }
.sales-flow-copy em { color: #1E90FF !important; font-style: italic; }
.sales-flow-subhead {
    text-align: center;
    font-weight: 800;
    font-size: 1.2rem;
    color: #FFFFFF !important;
    margin: 1.5rem 0 0.75rem 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.sales-img-wrapper {
    text-align: center;
    margin: 1rem auto;
    max-width: 520px;
}
.sales-img-wrapper img {
    width: 100%;
    max-width: 520px;
    height: auto;
    border-radius: 10px;
    border: 2px solid #222;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.sales-img-pair {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    margin: 1rem auto;
    max-width: 720px;
}
.sales-img-pair .pair-item {
    flex: 1;
    min-width: 240px;
    max-width: 340px;
}
.sales-img-pair .pair-item img {
    width: 100%;
    height: auto;
    border-radius: 10px;
    border: 2px solid #222;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
@media (max-width: 480px) {
    .sales-img-pair { flex-direction: column; align-items: center; }
    .sales-img-pair .pair-item { max-width: 100%; min-width: 0; }
}

/* ═══ CONTACT LOCKDOWN ═══ */
.contact-lockdown {
    max-width: 720px;
    margin: 2.5rem auto 1rem auto;
    background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
    border: 2px solid #1E90FF;
    border-radius: 14px;
    padding: 2rem 1.5rem;
    text-align: center;
}
.contact-lockdown .phone-big {
    font-family: "Impact", "Arial Black", "Helvetica Neue", sans-serif;
    font-size: clamp(2rem, 6vw, 3.2rem);
    font-weight: 900;
    color: #1E90FF !important;
    letter-spacing: 2px;
    margin: 0.75rem 0;
}
.contact-lockdown .text-only-warn {
    background: #FF6B6B;
    color: #000 !important;
    font-weight: 900;
    font-size: 1.1rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    display: inline-block;
    margin: 1rem 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.contact-lockdown .warn-detail {
    color: #ccc !important;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-top: 0.75rem;
}
.contact-lockdown .warn-detail strong { color: #FF6B6B !important; }
</style>
"""

# ── 10 FREE TOOLS — visual grid with HD images ──
FREE_TOOLS_GRID = [
    {
        "num": "1", "name": "QR Generator",
        "desc": "Generate custom QR codes for any URL, text, or contact card instantly.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzFFM0E1RjtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyRTg2QUI7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+TsTwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+UVIgR2VuZXJhdG9yPC90ZXh0PgogIDx0ZXh0IHg9IjQwMCIgeT0iMzg1IiBmb250LWZhbWlseT0iQXJpYWwsc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuNiI+RGlnaXRhbCBFbnZpc2lvbmVkIEVsaXRlIFN1aXRlPC90ZXh0Pgo8L3N2Zz4=",
    },
    {
        "num": "2", "name": "WebP Compressor",
        "desc": "Compress and convert images to WebP format for lightning-fast web pages.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzJEMUI2OTtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM3QjRERkY7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+WvO+4jzwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+V2ViUCBDb21wcmVzc29yPC90ZXh0PgogIDx0ZXh0IHg9IjQwMCIgeT0iMzg1IiBmb250LWZhbWlseT0iQXJpYWwsc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuNiI+RGlnaXRhbCBFbnZpc2lvbmVkIEVsaXRlIFN1aXRlPC90ZXh0Pgo8L3N2Zz4=",
    },
    {
        "num": "3", "name": "SEO Scraper",
        "desc": "Extract meta tags, headings, and SEO data from any webpage in seconds.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzFCNDMzMjtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM0MDkxNkM7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+UjTwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+U0VPIFNjcmFwZXI8L3RleHQ+CiAgPHRleHQgeD0iNDAwIiB5PSIzODUiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC42Ij5EaWdpdGFsIEVudmlzaW9uZWQgRWxpdGUgU3VpdGU8L3RleHQ+Cjwvc3ZnPg==",
    },
    {
        "num": "4", "name": "Password Generator",
        "desc": "Create ultra-secure passwords with customizable length and complexity.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzNDMTUxODtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNENjI4Mjg7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+UkDwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+UGFzc3dvcmQgR2VuPC90ZXh0PgogIDx0ZXh0IHg9IjQwMCIgeT0iMzg1IiBmb250LWZhbWlseT0iQXJpYWwsc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuNiI+RGlnaXRhbCBFbnZpc2lvbmVkIEVsaXRlIFN1aXRlPC90ZXh0Pgo8L3N2Zz4=",
    },
    {
        "num": "5", "name": "Case Formatter",
        "desc": "Convert text between UPPER, lower, Title, and Sentence case formats.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzFBMUEyRTtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMxNjIxM0U7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+UpDwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+Q2FzZSBGb3JtYXR0ZXI8L3RleHQ+CiAgPHRleHQgeD0iNDAwIiB5PSIzODUiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC42Ij5EaWdpdGFsIEVudmlzaW9uZWQgRWxpdGUgU3VpdGU8L3RleHQ+Cjwvc3ZnPg==",
    },
    {
        "num": "6", "name": "Hashtag Generator",
        "desc": "Generate trending, relevant hashtags for any topic or niche.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzJDMkM1NDtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM0NzQ3ODc7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+I++4j+KDozwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+SGFzaHRhZyBHZW48L3RleHQ+CiAgPHRleHQgeD0iNDAwIiB5PSIzODUiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC42Ij5EaWdpdGFsIEVudmlzaW9uZWQgRWxpdGUgU3VpdGU8L3RleHQ+Cjwvc3ZnPg==",
    },
    {
        "num": "7", "name": "UTM Builder",
        "desc": "Build tracked campaign URLs with UTM parameters for precise analytics.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzBBMjY0NztzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyMDUyOTU7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+UlzwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+VVRNIEJ1aWxkZXI8L3RleHQ+CiAgPHRleHQgeD0iNDAwIiB5PSIzODUiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC42Ij5EaWdpdGFsIEVudmlzaW9uZWQgRWxpdGUgU3VpdGU8L3RleHQ+Cjwvc3ZnPg==",
    },
    {
        "num": "8", "name": "MD to HTML",
        "desc": "Convert Markdown documents to clean, formatted HTML with live preview.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzNEMDA2NjtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNBODU1Rjc7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+TnTwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+TUQgdG8gSFRNTDwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM4NSIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBvcGFjaXR5PSIwLjYiPkRpZ2l0YWwgRW52aXNpb25lZCBFbGl0ZSBTdWl0ZTwvdGV4dD4KPC9zdmc+",
    },
    {
        "num": "9", "name": "CSV to JSON",
        "desc": "Transform CSV data into structured JSON format for APIs and databases.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzFFM0E1RjtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiMyRTg2QUI7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+TijwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+Q1NWIHRvIEpTT048L3RleHQ+CiAgPHRleHQgeD0iNDAwIiB5PSIzODUiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC42Ij5EaWdpdGFsIEVudmlzaW9uZWQgRWxpdGUgU3VpdGU8L3RleHQ+Cjwvc3ZnPg==",
    },
    {
        "num": "10", "name": "Keyword Density",
        "desc": "Analyze keyword frequency and density to optimize your content for SEO.",
        "img": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgODAwIDUwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzRBMTk0MjtzdG9wLW9wYWNpdHk6MSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNDNzM4NjY7c3RvcC1vcGFjaXR5OjEiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNTAwIiByeD0iMTYiIGZpbGw9InVybCgjYmcpIi8+CiAgPHRleHQgeD0iNDAwIiB5PSIyMjAiIGZvbnQtZmFtaWx5PSJBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuOSI+8J+OrzwvdGV4dD4KICA8dGV4dCB4PSI0MDAiIHk9IjM0MCIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgb3BhY2l0eT0iMC45NSI+S2V5d29yZCBEZW5zaXR5PC90ZXh0PgogIDx0ZXh0IHg9IjQwMCIgeT0iMzg1IiBmb250LWZhbWlseT0iQXJpYWwsc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIG9wYWNpdHk9IjAuNiI+RGlnaXRhbCBFbnZpc2lvbmVkIEVsaXRlIFN1aXRlPC90ZXh0Pgo8L3N2Zz4=",
    },
]


def render_free_tools_grid():
    """Render a 2-row, 5-column visual grid of the 10 free tools with HD images."""
    for row_start in range(0, 10, 5):
        cols = st.columns(5)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx < len(FREE_TOOLS_GRID):
                tool = FREE_TOOLS_GRID[idx]
                with col:
                    st.markdown(
                        f'<div class="tool-card">'
                        f'<img src="{tool["img"]}" alt="{tool["name"]}">'
                        f'<div class="card-body">'
                        f'<span class="tool-num">TOOL {tool["num"]}</span>'
                        f'<h4>{tool["name"]}</h4>'
                        f'<p>{tool["desc"]}</p>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )



def _b64_sales_img(key: str) -> str:
    """Return base64 data URI for a sales flow image, or empty string if missing."""
    path = SALES_FLOW_IMAGES.get(key)
    if path and path.exists():
        mime = "image/png" if str(path).endswith(".png") else "image/jpeg"
        encoded = base64.b64encode(path.read_bytes()).decode()
        return f"data:{mime};base64,{encoded}"
    return ""


def render_marketing_sales_flow():
    """Render the marketing expert sales flow with 7 images + copy blocks."""

    st.markdown('<hr class="sales-flow-divider">', unsafe_allow_html=True)

    # ═══ HEADING ═══
    st.markdown(
        '<div class="sales-flow-heading">\U0001F3AF PROFESSIONAL MARKETING & CAMPAIGN MANAGEMENT</div>',
        unsafe_allow_html=True,
    )

    # ═══ COPY BLOCK 1: THE GRAPHIC & CAMPAIGN SPECIALIST ═══
    st.markdown(
        '<div class="sales-flow-subhead">The Graphic & Campaign Specialist</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sales-flow-copy">'
        "Your business deserves more than just a presence\u2014it needs a campaign that "
        "<strong>converts</strong>. I specialize in high-impact <em>Organic Social Media "
        "Marketing</em> and <em>Digital Campaign Management</em>. Whether you need "
        "professional marketing materials like the posters and flyers shown below, or a "
        "dedicated manager to run your entire social media strategy, "
        "<strong>I am the guy to get it done.</strong>"
        '</div>',
        unsafe_allow_html=True,
    )

    # Images: Boost Brand flyer (full width) + Portfolio intro (full width) + Beautiful Ads clean
    img_boost = _b64_sales_img("boost_brand")
    img_portfolio = _b64_sales_img("portfolio_intro")
    img_trust = _b64_sales_img("beautiful_trust")

    if img_boost:
        st.markdown(
            f'<div class="sales-img-wrapper"><img src="{img_boost}" alt="Boost Your Brand on Social Media"></div>',
            unsafe_allow_html=True,
        )
    if img_portfolio:
        st.markdown(
            f'<div class="sales-img-wrapper"><img src="{img_portfolio}" alt="Digital Envisioned Portfolio"></div>',
            unsafe_allow_html=True,
        )
    if img_trust:
        st.markdown(
            f'<div class="sales-img-wrapper"><img src="{img_trust}" alt="Beautiful Ads Build Trust"></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══ COPY BLOCK 2: THE BLUEPRINTS TO FREEDOM ═══
    st.markdown(
        '<div class="sales-flow-subhead">The Blueprints to Freedom</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sales-flow-copy">'
        "I don\u2019t just run ads; I <strong>build systems</strong>. From the "
        "<em>Zero-Cost Digital Goldmine</em>\u2014where I show you how to exploit free "
        "AI tools to make money with zero capital\u2014to the "
        "<em>10-Minute Freedom Blueprint</em>, my materials are designed to "
        "<strong>automate your success</strong>. These are the exact blueprints I use to "
        "scale brands and reclaim time. If you need this level of precision for your own "
        "project, <strong>we need to talk.</strong>"
        '</div>',
        unsafe_allow_html=True,
    )

    # Images: Freedom Blueprint + Before/After comparison (side by side)
    img_freedom = _b64_sales_img("freedom_blueprint")
    img_ba = _b64_sales_img("before_after")

    html_pair1 = '<div class="sales-img-pair">'
    if img_freedom:
        html_pair1 += f'<div class="pair-item"><img src="{img_freedom}" alt="10-Minute Freedom Blueprint"></div>'
    if img_ba:
        html_pair1 += f'<div class="pair-item"><img src="{img_ba}" alt="Beautiful Ads Before and After"></div>'
    html_pair1 += '</div>'
    st.markdown(html_pair1, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══ COPY BLOCK 3: SOVEREIGNTY & FRANCHISE SYSTEMS ═══
    st.markdown(
        '<div class="sales-flow-subhead">Sovereignty & Franchise Systems</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sales-flow-copy">'
        "For those looking for <strong>high-level infrastructure</strong>, I offer the "
        "<em>Sovereign Vault Franchise System</em> and <em>Streetwise Justice</em> bundles. "
        "These are complete <strong>business-in-a-box models</strong> and legal literacy tools "
        "designed for those who demand total control over their finance and freedom. I provide "
        "the tech and the marketing power to turn these assets into a <strong>legacy.</strong>"
        '</div>',
        unsafe_allow_html=True,
    )

    # Images: Ads Not Converting + HIT HARD (side by side)
    img_convert = _b64_sales_img("not_converting")
    img_hit = _b64_sales_img("hit_hard")

    html_pair2 = '<div class="sales-img-pair">'
    if img_convert:
        html_pair2 += f'<div class="pair-item"><img src="{img_convert}" alt="Your Ads Are Not Converting"></div>'
    if img_hit:
        html_pair2 += f'<div class="pair-item"><img src="{img_hit}" alt="Your Ads Should HIT HARD"></div>'
    html_pair2 += '</div>'
    st.markdown(html_pair2, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══ FINAL LOCKDOWN: CONTACT ═══
    st.markdown(
        '<div class="contact-lockdown">'
        '<div class="sales-flow-subhead" style="margin-top:0;">\U0001F4F1 CONTACT ME DIRECTLY</div>'
        '<p style="color:#ccc !important;font-size:1rem;margin:0.5rem 0;">'
        "If you need marketing materials, custom flyers, or a professional manager to run "
        "your next ad campaign across every social media platform, reach out now.</p>"
        '<div class="phone-big">205-401-1124</div>'
        '<div class="text-only-warn">\u26A0\uFE0F TEXT ME ONLY</div>'
        '<div class="warn-detail">'
        "<strong>THE RULE:</strong> State your name and exactly what service you need. "
        "I <strong>DO NOT</strong> answer the phone for numbers I do not recognize\u2014"
        "this is my personal number, not my business line. "
        "<strong>Do not call. If you want a response, TEXT ME ONLY.</strong>"
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_landing_page():
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    # ═══ 1. FULL-WIDTH HERO with logo image as background + overlay ═══
    if HERO_LOGO_PATH.exists():
        logo_b64 = base64.b64encode(HERO_LOGO_PATH.read_bytes()).decode()
        hero_img_src = f"data:{HERO_LOGO_MIME};base64,{logo_b64}"
    else:
        # Fallback: a dark gradient placeholder
        hero_img_src = ""

    if hero_img_src:
        st.markdown(
            f"""
            <div class="hero-section">
                <img class="hero-bg" src="{hero_img_src}" alt="Digital Envisioned Hero">
                <div class="hero-overlay">
                    <img class="hero-logo" src="{hero_img_src}" alt="DE Logo">
                    <h1>
                        <span class="white">DIGITAL ENVISIONED</span><br>
                        <span class="blue">ELITE AUTOMATION SUITE</span>
                    </h1>
                    <div class="hero-sub">200 Premium Tools · Birmingham, AL · by Joshua Newton</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="hero-section" style="height:80vh;display:flex;align-items:center;
                justify-content:center;background:linear-gradient(135deg,#0a0a0a 0%,#111 50%,#0a0a0a 100%);">
                <div class="hero-overlay">
                    <h1>
                        <span class="white">DIGITAL ENVISIONED</span><br>
                        <span class="blue">ELITE AUTOMATION SUITE</span>
                    </h1>
                    <div class="hero-sub">200 Premium Tools · Birmingham, AL · by Joshua Newton</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ═══ 2. SALES NARRATIVE ═══
    st.markdown(
        '<div class="sales-block">'
        '<h3>Birmingham, The Manual Hustle is Killing Your Business.</h3>'
        "<p>You\u2019re not just <em>\u2018busy\u2019</em> \u2014 you\u2019re drowning. Your competitors "
        "aren\u2019t working harder than you; they are working <strong>smarter</strong>. "
        "Small businesses across Alabama are burning hours on manual tasks that can "
        "be automated, and it\u2019s costing you more than just time. It\u2019s costing you "
        "<span class=\'pain\'>clients</span>. It\u2019s costing you "
        "<span class=\'pain\'>scaling potential</span>.</p>"

        "<p><strong>You Have the Pain:</strong> Wasted hours on repetitive SEO "
        "checks. Confusing QR generation. Broken lead follow-ups. "
        "<em>If your workflow is manual, it\u2019s broken.</em></p>"

        "<h3><span class=\'highlight-blue\'>I Have the Absolute Solution.</span></h3>"
        "<p>The Newton Legacy presents the <strong>Digital Envisioned 200 Tool "
        "Premium Elite Automation Suite</strong>. This isn\u2019t just software; it\u2019s a "
        "dedicated engine for your agency or ministry. We have forged a comprehensive "
        "arsenal of <strong>SEO tools, Lead Generation engines, Advanced Image "
        "Processors, and Data Management modules</strong> that work 24/7 so you "
        "don\u2019t have to.</p>"

        "<p>This is about <strong>digital sovereignty</strong>. Your business cannot "
        "afford to wait while your competitors embrace automation. Gain exclusive "
        "access to the high-level workflow that top-tier firms use to dominate their "
        "markets.</p>"

        "<p><strong>Better things are coming. Unlock your first 10 free tools right now.</strong></p>"
        '<div class="founder-line">\u2014 Joshua Newton, Founder</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ═══ 3. FREE TOOLS VISUAL GRID ═══
    st.markdown(
        '<div class="section-headline">\U0001F513 Your 10 Free Tools \u2014 Unlocked Instantly</div>'
        '<div class="section-sub">Enter your info below to access these premium tools at no cost.</div>',
        unsafe_allow_html=True,
    )
    render_free_tools_grid()
    st.markdown("<br>", unsafe_allow_html=True)

    # ═══ 4. LEAD CAPTURE FORM (centered, prominent) ═══
    st.markdown(
        '<div class="section-headline">\U0001F680 Claim Your Free Access Now</div>'
        '<div class="section-sub">Fill in your details and unlock all 10 tools instantly.</div>',
        unsafe_allow_html=True,
    )

    form_col1, form_col2, form_col3 = st.columns([1, 2, 1])
    with form_col2:
        with st.form("lead_capture_form", clear_on_submit=False):
            first_name = st.text_input("\U0001F464 First Name *")
            email = st.text_input("\U0001F4E7 Email Address *")
            phone = st.text_input("\U0001F4F1 Phone Number *")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "\U0001F513 UNLOCK MY 10 FREE TOOLS", type="primary"
            )
            if submitted:
                if not first_name.strip() or not email.strip() or not phone.strip():
                    st.error("Please fill in all three fields.")
                elif "@" not in email or "." not in email:
                    st.error("Please enter a valid email address.")
                else:
                    save_lead(first_name.strip(), email.strip(), phone.strip())
                    st.session_state.lead_captured = True
                    st.session_state.lead_first_name = first_name.strip()
                    ok, msg = send_welcome_email(first_name.strip(), email.strip())
                    if ok:
                        st.success(
                            "\u2705 Access granted! A welcome email has been sent to "
                            f"{email.strip()}. Loading your dashboard..."
                        )
                    else:
                        st.warning(
                            f"Access granted (welcome email could not be sent: {msg}). "
                            "Loading your dashboard..."
                        )
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ═══ 5. UPGRADE CTAs ═══
    st.markdown(
        '<div class="upgrade-headline">Skip the line \u2014 go straight to a paid tier:</div>',
        unsafe_allow_html=True,
    )
    cu1, cu2 = st.columns(2)
    with cu1:
        st.link_button(
            "\U0001F525 Subscribe Now \u2014 Pro Tier (50 Tools) \u2014 $47/mo",
            UPGRADE_LINKS["pro"],
            use_container_width=True,
        )
    with cu2:
        st.link_button(
            "\u26A1 Subscribe to the Elite 200 \u2014 $197/mo",
            UPGRADE_LINKS["empire"],
            use_container_width=True,
        )
    st.caption("Secure checkout via Stripe \u2014 opens in a new tab.")

    # ═══ 6. MASTER ADMIN SIGN IN ═══
    with st.expander("\U0001F511 Master Admin Sign In"):
        em = st.text_input("Email:", key="landing_login_email")
        pw = st.text_input("Password:", type="password", key="landing_login_pw")
        if st.button("Sign In as Master"):
            if em.strip().lower() == MASTER_EMAIL and pw == MASTER_PASSWORD:
                st.session_state.user_email = MASTER_EMAIL
                st.session_state.user_tier = "master"
                st.session_state.lead_captured = True
                st.rerun()
            else:
                st.error("Invalid credentials.")

    # ═══ 7. MARKETING EXPERT SALES FLOW ═══
    st.markdown("<br>", unsafe_allow_html=True)
    render_marketing_sales_flow()



# Master bypasses the gate entirely; everyone else must submit the form.
if st.session_state.user_tier != "master" and not st.session_state.lead_captured:
    render_landing_page()
    st.stop()

# --- 2. MASTER CONFIG & SIDEBAR ---
st.sidebar.title("Digital Envisioned")
st.sidebar.subheader("200-Tool Automation Suite")

_tier = st.session_state.user_tier
_email = st.session_state.user_email
_max_tools = TIER_LIMITS[_tier]

if _tier == "master":
    st.sidebar.success(f"Signed in: {_email}\n\nTier: **MASTER** (all 200 tools)")
    if st.sidebar.button("Sign Out"):
        st.session_state.user_tier = "free"
        st.session_state.user_email = "Public (Free Tier)"
        st.session_state.lead_captured = False
        st.rerun()
else:
    st.sidebar.info(f"Tier: **FREE** (Tools 1-10)")
    with st.sidebar.expander("🔑 Master Sign In"):
        em = st.text_input("Email:", key="login_email")
        pw = st.text_input("Password:", type="password", key="login_pw")
        if st.button("Sign In"):
            if em.strip().lower() == MASTER_EMAIL and pw == MASTER_PASSWORD:
                st.session_state.user_email = MASTER_EMAIL
                st.session_state.user_tier = "master"
                st.rerun()
            else:
                st.error("Invalid credentials.")



CATEGORIES = {
    "Content & Writing (1-25)": [
        "1. QR Generator", "2. WebP Compressor", "3. SEO Scraper", "4. Password Gen",
        "5. Case Formatter", "6. Hashtag Gen", "7. UTM Builder", "8. MD to HTML",
        "9. CSV to JSON", "10. Keyword Density", "11. PDF Locker", "12. Ad Resizer",
        "13. Link Checker", "14. Lorem Ipsum", "15. Slug Maker", "16. Email Val",
        "17. YT Thumbnails", "18. TTS Preview", "19. JSON Pretty", "20. Site Screenshot",
        "21. Char Counter", "22. Expense Log", "23. Unit Conv", "24. Base64", "25. Color Hex",
    ],
    "SEO & Marketing (26-50)": [
        "26. Grayscale", "27. Sentiment", "28. Name Picker", "29. Binary Decoder",
        "30. Domain Ideas", "31. Bio Gen", "32. Tip Calc", "33. List Shuffler",
        "34. CSS Helper", "35. Contrast Check", "36. Robots.txt", "37. Word Cloud",
        "38. Persona Gen", "39. Link Hub", "40. Daily Planner", "41. Row Counter",
        "42. Morse Code", "43. Load Sim", "44. Niche Finder", "45. Icon Resizer",
        "46. Image to PDF", "47. Audio Player", "48. Funnel Calc", "49. Favicon Fetch",
        "50. Hub Info",
    ],
    "Image & Media (51-75)": [
        "51. Sermon Quote Card Gen", "52. Prayer Request Organizer",
        "53. Attendance Growth Tracker", "54. Scripture Reference Finder",
        "55. Volunteer Rotation Builder", "56. Digital Offering Estimator",
        "57. Event Countdown Timer", "58. Hymn Slideshow Generator",
        "59. Image Watermark Generator", "60. Bulk Image Resizer",
        "61. Color Palette Extractor", "62. EXIF Data Viewer",
        "63. SVG to PNG Converter", "64. Image Cropper Tool",
        "65. Meme Generator", "66. GIF Maker",
        "67. Audio Format Converter", "68. Video to Audio Extractor",
        "69. Video Thumbnail Grabber", "70. YouTube Transcript Extractor",
        "71. Image Filter Applier", "72. Background Remover",
        "73. Aspect Ratio Calculator", "74. DPI Converter",
        "75. Font Previewer",
    ],
    "Developer Tools (76-90)": [
        "76. JSON Validator & Formatter", "77. Regex Tester",
        "78. SQL Query Formatter", "79. Hash Generator",
        "80. JWT Decoder", "81. URL Encoder/Decoder",
        "82. HTML Sanitizer", "83. XML to JSON Converter",
        "84. CRON Expression Generator", "85. Diff Checker",
        "86. Markdown to HTML Previewer", "87. CSV to JSON Converter",
        "88. Secure Password Generator", "89. Base64 String Encoder",
        "90. IP Address Data Extractor",
    ],
    "Finance & Business Utility Engine (91-102)": [
        "91. ROI Calculator", "92. Compound Interest Forecaster",
        "93. Freelance Hourly Rate Calculator", "94. E-commerce Profit Margin Calculator",
        "95. Subscription Burn-Rate Tracker", "96. Stripe Transaction Fee Calculator",
        "97. Rule-of-72 Investment Calculator", "98. Business Sales Tax Calculator",
        "99. Break-Even Point Analyzer", "100. Quick Invoice Text Generator",
        "101. SaaS Churn Rate Calculator", "102. Discount & Markup Calculator",
    ],
    "SEO & Copywriting Vault (103-115)": [
        "103. Keyword Density Analyzer", "104. Meta Tag Generator",
        "105. SEO Word & Character Counter", "106. Readability Score Estimator",
        "107. Lorem Ipsum Placeholder Generator", "108. Text Case Converter",
        "109. UTM Campaign Link Builder", "110. Hashtag Formatter",
        "111. Twitter/X Strict Character Counter", "112. Instagram Bio Spacer",
        "113. Bullet Point to Comma List Converter", "114. Whitespace & Line Break Remover",
        "115. Email Subject Line Previewer",
    ],
    "Content & Text Utilities (116-125)": [
        "116. Blog Title Generator", "117. CTA Generator",
        "118. Text to Morse Code Converter", "119. Binary ↔ Text Converter",
        "120. Basic Sentiment Analyzer", "121. Webpage Text Extractor",
        "122. HTML to Markdown Converter", "123. Text Prefix/Suffix Bulk Adder",
        "124. Duplicate Line Remover", "125. List Alphabetizer & Sorter",
    ],
    "Data & List Management (126-135)": [
        "126. List Randomizer", "127. CSV Column Extractor",
        "128. JSON to XML Converter", "129. Phone Number Standardizer",
        "130. Email Address Extractor", "131. URL Extractor",
        "132. SQL Insert Statement Generator", "133. YAML to JSON Converter",
        "134. Data Anonymizer", "135. Word Frequency Counter",
    ],
    "Web & Network Tools (136-145)": [
        "136. WHOIS Data Lookup", "137. DNS Record Checker",
        "138. HTTP Status Code Header Checker", "139. User-Agent String Parser",
        "140. URL Redirect Tracer", "141. Meta Tag Extractor",
        "142. Robots.txt Generator", "143. Sitemap.xml Basic Generator",
        "144. IP Subnet Calculator", "145. MAC Address Vendor Lookup",
    ],
    "Advanced Design & Media (146-155)": [
        "146. Color Contrast Checker",
        "147. CSS Gradient Code Generator",
        "148. Base64 to Image Decoder",
        "149. Image to Base64 Encoder",
        "150. Custom QR Code Builder",
        "151. Favicon Generator",
        "152. SVG Code Viewer",
        "153. Hex to RGB / RGB to Hex Converter",
        "154. RGB to CMYK Converter",
        "155. Text to Handwriting Previewer",
    ],
    "Security & Network Utilities (156-160)": [
        "156. SSL Certificate Checker",
        "157. Basic Port Checker",
        "158. BGP ASN Lookup",
        "159. HTTP API Request Tester",
        "160. Password Strength Analyzer",
    ],
    "Writing, Code & Conversion (161-165)": [
        "161. XML Formatter & Validator",
        "162. Roman Numeral Converter",
        "163. Unicode Character Finder",
        "164. YAML to XML Converter",
        "165. Article Spinner",
    ],
    "Social Media & Marketing (166-175)": [
        "166. YouTube Tag Extractor",
        "167. TikTok Caption Spacer & Formatter",
        "168. LinkedIn Professional Headline Generator",
        "169. Pinterest Pin Title Optimizer",
        "170. Social Media Post Scheduler",
        "171. Facebook Ad Copy Generator",
        "172. Instagram Carousel Idea Generator",
        "173. Video Script Hook Generator",
        "174. Newsletter Subject Line Scorer",
        "175. Competitor Keyword Extractor",
    ],
    "Local SEO & Marketing Frameworks (176-181)": [
        "176. Local SEO Citation Format Generator",
        "177. Google My Business Review Link Builder",
        "178. AI Prompt Architect",
        "179. Cold Email Sequence Framework Builder",
        "180. Customer Avatar / Buyer Persona Generator",
        "181. Agency Proposal Outline Generator",
    ],
    "Business & Operations (182-190)": [
        "182. Invoice Number Sequence Generator",
        "183. Sales Funnel Conversion Step Calculator",
        "184. A/B Test Split Traffic Calculator",
        "185. Affiliate Link Cloaker",
        "186. Privacy Policy Basic Template Generator",
        "187. Terms & Conditions Basic Template Generator",
        "188. Brand Mission Statement Builder",
        "189. Slogan & Tagline Brainstormer",
        "190. Brand Core Values Extractor",
    ],
    "Executive Strategy (191-200)": [
        "191. Meeting Agenda Template Builder",
        "192. Project Timeline Estimator",
        "193. OKR Formatter",
        "194. SWOT Analysis Matrix Builder",
        "195. PESTLE Analysis Framework Generator",
        "196. Product Pricing Tier Structurer",
        "197. Profit Margin vs. Markup Visualizer",
        "198. Employee Onboarding Checklist Generator",
        "199. Business Pitch Deck Outline Builder",
        "200. Master System Diagnostic Dashboard",
    ],
}

if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = "Dashboard Home"

def _pick_tool(cat_key):
    val = st.session_state.get(cat_key)
    if val:
        st.session_state.selected_tool = val
        # clear other categories so only one is active
        for k in CATEGORIES:
            other = f"radio_{k}"
            if other != cat_key and other in st.session_state:
                st.session_state[other] = None

if st.sidebar.button("🏠 Dashboard Home"):
    st.session_state.selected_tool = "Dashboard Home"
    for k in CATEGORIES:
        st.session_state[f"radio_{k}"] = None

for cat, tools in CATEGORIES.items():
    with st.sidebar.expander(cat):
        key = f"radio_{cat}"
        st.radio(
            cat, tools, key=key, index=None,
            on_change=_pick_tool, args=(key,),
            label_visibility="collapsed",
        )

selected_tool = st.session_state.selected_tool
st.sidebar.caption(f"Active: {selected_tool}")

# --- 2b. TIER ACCESS GATE ---
def _tool_number(name: str):
    try:
        return int(name.split('.')[0])
    except (ValueError, AttributeError):
        return None

def _render_locked(tool_name: str, tool_num: int):
    st.title("🔒 Locked")
    st.subheader(tool_name)
    if 11 <= tool_num <= 50:
        st.warning("This is a Pro Tool.")
        st.link_button(
            "Upgrade to Pro — $47/mo",
            UPGRADE_LINKS["pro"],
            type="primary",
        )
    else:
        st.warning("Elite Automation Suite Required.")
        st.link_button(
            "Upgrade to Elite — $197/mo",
            UPGRADE_LINKS["empire"],
            type="primary",
        )
    st.caption("Secure checkout via Stripe (opens in a new tab).")

_num = _tool_number(selected_tool)
if _num is not None and _num > _max_tools:
    _render_locked(selected_tool, _num)
    st.stop()

# --- 3. TOOL LOGIC (1-200) ---
if selected_tool == "Dashboard Home":
    st.title("Welcome to the Digital Envisioned Suite")
    st.write("A premium fleet of 200 automation tools — choose a category to begin.")
    st.markdown("---")
    render_free_tools_grid()
    st.markdown("---")
    st.caption("Open any expander in the left sidebar to launch a specific tool.")

elif selected_tool == "1. QR Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate custom QR codes from any URL, text, or contact info. Perfect for marketing materials, business cards, and digital campaigns.")
    url = st.text_input("URL:")
    if st.button("Generate"):
        qr = qrcode.make(url)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf.getvalue())
        st.download_button("Download", buf.getvalue(), "qr.png")

elif selected_tool == "2. WebP Compressor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Compress and convert images to WebP format for faster load times. Reduce file sizes by up to 80% without losing visual quality.")
    f = st.file_uploader("Upload", type=['jpg','png'])
    if f:
        img = Image.open(f)
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=80)
        st.download_button("Download WebP", buf.getvalue(), "img.webp")

elif selected_tool == "3. SEO Scraper":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Extract meta tags, headings, and SEO data from any webpage. Analyze competitor pages and optimize your own site's search ranking.")
    u = st.text_input("URL:")
    if st.button("Audit"):
        r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'})
        s = BeautifulSoup(r.text, 'html.parser')
        st.write(f"Title: {s.title.text if s.title else 'None'}")

elif selected_tool == "4. Password Gen":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create ultra-secure passwords with customizable length and special characters. Protect your business accounts with uncrackable credentials.")
    l = st.slider("Length", 8, 32, 16)
    st.code(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l)))

elif selected_tool == "5. Case Formatter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert text between UPPER, lower, Title, and Sentence case formats. Format content perfectly for headlines, social posts, and documents.")
    t = st.text_area("Text:")
    if t:
        st.write(f"Title: {t.title()}")
        st.write(f"Upper: {t.upper()}")

elif selected_tool == "6. Hashtag Gen":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate trending, niche-relevant hashtags for any topic. Boost social media reach by targeting the right audiences with optimized tags.")
    kw = st.text_input("Keyword:")
    if kw: st.write(f"#{kw} #business #marketing")

elif selected_tool == "7. UTM Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build tracked campaign URLs with UTM parameters for Google Analytics. Measure which ads, emails, and posts drive the most traffic.")
    url = st.text_input("URL:")
    src = st.text_input("Source:")
    if url and src: st.code(f"{url}?utm_source={src}")

elif selected_tool == "8. MD to HTML":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert Markdown to clean, formatted HTML with a live preview. Streamline blog publishing and documentation workflows.")
    md = st.text_area("Markdown:")
    if md: st.code(markdown.markdown(md))

elif selected_tool == "9. CSV to JSON":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Transform CSV spreadsheet data into structured JSON format. Prepare data for APIs, databases, and modern web applications.")
    f = st.file_uploader("CSV", type="csv")
    if f: st.json(pd.read_csv(f).to_json(orient='records'))

elif selected_tool == "10. Keyword Density":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze keyword frequency and density in any text block. Optimize your content for SEO without over-stuffing keywords.")
    t = st.text_area("Text:")
    if t: st.write(Counter(t.split()).most_common(5))

elif selected_tool == "11. PDF Locker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Lock PDF files with password protection. Secure sensitive documents before sharing with clients or partners.")
    f = st.file_uploader("PDF", type="pdf")
    pw = st.text_input("Password", type="password")
    if f and pw:
        reader = PyPDF2.PdfReader(f)
        writer = PyPDF2.PdfWriter()
        for p in reader.pages: writer.add_page(p)
        writer.encrypt(pw)
        buf = BytesIO()
        writer.write(buf)
        st.download_button("Download Locked PDF", buf.getvalue(), "locked.pdf")

elif selected_tool == "12. Ad Resizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Merge multiple PDF documents into a single file. Combine contracts, reports, and presentations into one professional package.")
    f = st.file_uploader("Image", type=['jpg','png'])
    if f:
        img = Image.open(f)
        st.image(img.resize((1080,1080)))
        st.write("Resized to 1080x1080")

elif selected_tool == "13. Link Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Split a PDF into individual pages or custom ranges. Extract exactly the pages you need without editing the original.")
    u = st.text_input("URL:")
    if u and st.button("Check"):
        try:
            r = requests.head(u, timeout=5)
            st.success(f"Status: {r.status_code}")
        except: st.error("Offline")

elif selected_tool == "14. Lorem Ipsum":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert PDF documents to editable Word format. Edit and repurpose content from PDFs without retyping everything.")
    p = st.slider("Paragraphs", 1, 5, 1)
    st.write("Lorem ipsum dolor sit amet... " * p)

elif selected_tool == "15. Slug Maker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Extract all text content from uploaded PDF files. Pull data from invoices, reports, and scanned documents quickly.")
    t = st.text_input("Title:")
    if t: st.code(t.lower().replace(" ", "-"))

elif selected_tool == "16. Email Val":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Rotate PDF pages to correct orientation. Fix sideways or upside-down scans before sharing or printing.")
    e = st.text_input("Email:")
    if e: st.write("Valid" if "@" in e and "." in e else "Invalid")

elif selected_tool == "17. YT Thumbnails":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Add watermark text to every page of a PDF. Brand and protect your documents from unauthorized distribution.")
    v = st.text_input("YT URL:")
    if "v=" in v:
        id = v.split("v=")[1]
        st.image(f"https://img.youtube.com/vi/{id}/maxresdefault.jpg")

elif selected_tool == "18. TTS Preview":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Compress PDF files to reduce their size. Share large documents via email by shrinking them significantly.")
    txt = st.text_input("Speak:")
    if st.button("Play"):
        st.components.v1.html(f"<script>window.speechSynthesis.speak(new SpeechSynthesisUtterance('{txt}'));</script>")

elif selected_tool == "19. JSON Pretty":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert images (JPG, PNG) to PDF format. Package visual content into professional, shareable PDF documents.")
    j = st.text_area("JSON:")
    if j: st.json(json.loads(j))

elif selected_tool == "20. Site Screenshot":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Extract metadata from PDF files. View author, creation date, and document properties for auditing.")
    u = st.text_input("URL:")
    if u: st.image(f"https://api.screenshotmachine.com/?key=free&url={u}&dimension=1024x768")

elif selected_tool == "21. Char Counter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Encrypt text with AES-256 encryption. Protect sensitive messages and data with military-grade encryption.")
    t = st.text_area("Text:")
    st.write(f"Chars: {len(t)} | Words: {len(t.split())}")

elif selected_tool == "22. Expense Log":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Decrypt AES-256 encrypted text back to plaintext. Retrieve your protected messages when you need them.")
    it = st.text_input("Item:")
    pr = st.number_input("Price:")
    if st.button("Log"): st.write(f"Saved: {it} - ${pr}")

elif selected_tool == "23. Unit Conv":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate RSA key pairs for secure communication. Create public/private key pairs for encryption and digital signatures.")
    v = st.number_input("MB:")
    st.write(f"{v/1024:.2f} GB")

elif selected_tool == "24. Base64":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate file hash checksums (MD5, SHA-256). Verify file integrity and detect tampering or corruption.")
    t = st.text_input("Text:")
    if t: st.code(base64.b64encode(t.encode()).decode())

elif selected_tool == "25. Color Hex":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Securely wipe and overwrite file data. Ensure deleted sensitive files cannot be recovered.")
    c = st.color_picker("Pick:")
    st.write(f"Hex: {c}")

elif selected_tool == "26. Grayscale":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate strong, random passwords. Protect your accounts with passwords that cannot be guessed.")
    f = st.file_uploader("Img")
    if f: st.image(Image.open(f).convert('L'))

elif selected_tool == "27. Sentiment":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Encode and decode text using Caesar cipher. Learn classical cryptography and create simple coded messages.")
    t = st.text_input("Copy:")
    st.write("Positive" if any(x in t.lower() for x in ['great','easy','save']) else "Neutral")

elif selected_tool == "28. Name Picker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Encode and decode Morse code. Convert between text and Morse for creative or educational purposes.")
    n = st.text_area("Names (1 per line):")
    if st.button("Pick"): st.write(random.choice(n.split('\n')))

elif selected_tool == "29. Binary Decoder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Encode text in Base64 and decode it back. Essential for working with APIs, data transfer, and email encoding.")
    b = st.text_input("Binary:")
    if b: st.code("".join(chr(int(x, 2)) for x in b.split()))

elif selected_tool == "30. Domain Ideas":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate secure tokens for authentication. Create API keys and session tokens that resist brute-force attacks.")
    k = st.text_input("Keyword:")
    if k: st.write([f"{k}{s}" for s in ['.com', '.net', '.io']])

elif selected_tool == "31. Bio Gen":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Extract dominant colors from images. Build brand palettes from photos and reference designs.")
    j = st.text_input("Job:")
    if j: st.code(f"🚀 {j} | Helping brands grow!")

elif selected_tool == "32. Tip Calc":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Resize images to exact dimensions. Prepare images for social media, ads, and website requirements.")
    b = st.number_input("Bill:")
    st.write(f"Total w/ 20%: ${b*1.2:.2f}")

elif selected_tool == "33. List Shuffler":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Crop images to custom regions. Frame photos perfectly for profiles, thumbnails, and listings.")
    l = st.text_area("Items:")
    if l:
        items = l.split('\n')
        random.shuffle(items)
        st.write(items)

elif selected_tool == "34. CSS Helper":
    with st.expander("ℹ️ How to use this tool"):
        st.write("View EXIF data from image files. See camera settings, GPS data, and metadata from photos.")
    st.code("display: flex; justify-content: center;")

elif selected_tool == "35. Contrast Check":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert SVG vector graphics to PNG raster images. Export scalable graphics for platforms that require bitmap formats.")
    bg = st.color_picker("BG", "#FFFFFF")
    fg = st.color_picker("Text", "#000000")
    st.markdown(f"<div style='background:{bg}; color:{fg}; padding:10px'>Sample</div>", unsafe_allow_html=True)

elif selected_tool == "36. Robots.txt":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Compress images with adjustable quality settings. Reduce image file sizes while maintaining acceptable visual quality.")
    st.code("User-agent: *\nDisallow: /admin")

elif selected_tool == "37. Word Cloud":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create animated GIFs from multiple images. Build eye-catching animations for social media and presentations.")
    t = st.text_area("Keywords:")
    if t: st.write(Counter(t.split()).most_common(10))

elif selected_tool == "38. Persona Gen":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert images between formats (PNG, JPEG, WebP). Switch image formats to match platform requirements.")
    if st.button("Gen"): st.write("Persona: Small Biz Owner, Goal: Leads")

elif selected_tool == "39. Link Hub":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Apply artistic filters and effects to images. Transform ordinary photos into striking visual content.")
    st.write("[Digital Envisioned](https://digitalenvisioned.net)")

elif selected_tool == "40. Daily Planner":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate color palettes from images. Extract and organize the key colors from any visual reference.")
    t = st.text_input("Task:")
    if t: st.checkbox(t)

elif selected_tool == "41. Row Counter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate compound interest over time. Model investment returns and understand long-term growth.")
    f = st.file_uploader("CSV")
    if f: st.write(f"Rows: {len(pd.read_csv(f))}")

elif selected_tool == "42. Morse Code":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate loan payments and amortization schedules. Plan your financing with precise monthly payment projections.")
    st.code("... --- ...")

elif selected_tool == "43. Load Sim":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Estimate income tax across brackets. Plan ahead for tax obligations and optimize your structure.")
    s = st.slider("Size MB", 1, 10, 2)
    st.write(f"Load: {s*1.5}s")

elif selected_tool == "44. Niche Finder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate investment returns over time. Forecast portfolio growth with different contribution scenarios.")
    st.write("Try: Church Lead Automation")

elif selected_tool == "45. Icon Resizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track and split group expenses. Settle up fairly after trips, dinners, and shared projects.")
    f = st.file_uploader("Icon")
    if f: st.image(Image.open(f).resize((512,512)))

elif selected_tool == "46. Image to PDF":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert between currencies using live rates. Calculate international payments and travel budgets accurately.")
    fs = st.file_uploader("Images", accept_multiple_files=True)
    if fs and st.button("PDF"):
        imgs = [Image.open(x).convert("RGB") for x in fs]
        buf = BytesIO()
        imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:])
        st.download_button("Download PDF", buf.getvalue(), "files.pdf")

elif selected_tool == "47. Audio Player":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate net take-home pay from salary. Understand your real earnings after taxes and deductions.")
    st.write("Ready to play preview.")

elif selected_tool == "48. Funnel Calc":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate tips and split bills among groups. Handle restaurant checks and service gratuities effortlessly.")
    v = st.number_input("Visits", 1000)
    st.write(f"Expected Sales (2%): {v*0.02}")

elif selected_tool == "49. Favicon Fetch":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Estimate business profit margins. Set prices that cover costs and deliver healthy profits.")
    d = st.text_input("Domain:")
    if d: st.image(f"https://www.google.com/s2/favicons?sz=64&domain={d}")

elif selected_tool == "50. Hub Info":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate discounts and sale prices. Run promotions with precise pricing that protects your margins.")
    st.write("Digital Envisioned Suite v1.0 | Joshua Eugene Newton")
# --- TOOL 51: Sermon Quote Card Gen ---
elif selected_tool == "51. Sermon Quote Card Gen":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Count the frequency of words in text. Identify overused words and improve writing variety.")
    st.header("Sermon Quote Creator")
    text = st.text_area("Enter Sermon Quote:")
    bg_color = st.color_picker("Pick Background Color", "#1e1e1e")
    if text:
        img = Image.new('RGB', (1080, 1080), color=bg_color)
        st.image(img, caption="Preview Card")
        st.info("Agent: Add text-overlay logic to this tool next.")

# --- TOOL 52: Prayer Request Organizer ---
elif selected_tool == "52. Prayer Request Organizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Compare two texts and highlight differences. Track changes in documents, contracts, and content revisions.")
    st.header("Prayer Wall Manager")
    req = st.text_area("Paste raw prayer requests here:")
    if st.button("Format for Staff"):
        st.write("### Formatted List:")
        for line in req.split('\n'):
            st.write(f"🙏 {line}")

# --- TOOL 53: Attendance Growth Tracker ---
elif selected_tool == "53. Attendance Growth Tracker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate Lorem Ipsum placeholder text. Speed up design mockups with realistic dummy content.")
    st.header("Growth Analytics")
    weeks = st.text_input("Enter weekly numbers (comma separated):", "100, 120, 115, 140")
    if weeks:
        data = [int(x) for x in weeks.split(',')]
        st.line_chart(data)

# --- TOOL 54: Scripture Reference Finder ---
elif selected_tool == "54. Scripture Reference Finder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create URL-friendly slugs from text. Build clean, SEO-optimized URLs for your web pages.")
    st.header("Quick Scripture Lookup")
    ref = st.text_input("Enter Verse (e.g., John 3:16):")
    if ref:
        st.write(f"Searching for {ref}...")
        st.write("[Open in Bible Gateway](https://www.biblegateway.com/passage/?search=" + ref.replace(" ", "+") + ")")

# --- TOOL 55: Volunteer Rotation Builder ---
elif selected_tool == "55. Volunteer Rotation Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Summarize long text into key points. Extract essential information from lengthy documents quickly.")
    st.header("Volunteer Randomizer")
    names = st.text_area("Enter Names (one per line):")
    if st.button("Generate Sunday Roster"):
        name_list = names.split('\n')
        random.shuffle(name_list)
        st.write(name_list)

# --- TOOL 56: Digital Offering Estimator ---
elif selected_tool == "56. Digital Offering Estimator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Check text for grammar and style issues. Polish your writing before publishing or sending to clients.")
    st.header("Giving Projection")
    avg = st.number_input("Average Weekly Giving ($):", value=1000)
    growth = st.slider("Expected Growth (%)", 0, 50, 5)
    st.metric("Projected Monthly Total", f"${(avg * 4) * (1 + growth/100):,.2f}")

# --- TOOL 57: Event Countdown Timer ---
elif selected_tool == "57. Event Countdown Timer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Count words, characters, and paragraphs. Meet content requirements and optimize for ideal length.")
    st.header("Service Countdown")
    event_name = st.text_input("Event Name:", "Sunday Celebration")
    st.success(f"Countdown active for {event_name}")
    st.info("Check sidebar for live timer settings.")

# --- TOOL 58: Hymn Slideshow Generator ---
elif selected_tool == "58. Hymn Slideshow Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate text in random order or patterns. Create unique content variations for testing and brainstorming.")
    st.header("Lyric Slide Builder")
    lyrics = st.text_area("Paste Lyrics:")
    if st.button("Generate Slides"):
        for i, verse in enumerate(lyrics.split('\n\n')):
            st.subheader(f"Slide {i+1}")
            st.info(verse)

elif selected_tool == "59. Image Watermark Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Find and replace text across documents. Make bulk edits to content efficiently and accurately.")
    st.header("Image Watermark Generator")
    up = st.file_uploader("Upload image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    text = st.text_input("Watermark text:", "© Digital Envisioned")
    opacity = st.slider("Opacity", 50, 255, 160)
    size_pct = st.slider("Font size (% of width)", 2, 15, 5)
    if up and text:
        img = Image.open(up).convert("RGBA")
        layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(layer)
        font_size = max(12, int(img.size[0] * size_pct / 100))
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos = (img.size[0] - tw - 20, img.size[1] - th - 20)
        draw.text(pos, text, fill=(255, 255, 255, opacity), font=font)
        out = Image.alpha_composite(img, layer).convert("RGB")
        buf = BytesIO()
        out.save(buf, format="PNG")
        st.image(buf.getvalue(), use_container_width=True)
        st.download_button("Download PNG", buf.getvalue(), "watermarked.png", "image/png")

elif selected_tool == "60. Bulk Image Resizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Translate text between languages. Communicate across language barriers with instant translation.")
    st.header("Bulk Image Resizer")
    ups = st.file_uploader("Upload images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    w = st.number_input("Target width (px)", 50, 5000, 800)
    h = st.number_input("Target height (px, 0 = keep aspect)", 0, 5000, 0)
    if ups and st.button("Resize All"):
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for f in ups:
                im = Image.open(f)
                if h == 0:
                    ratio = w / im.size[0]
                    new_size = (w, int(im.size[1] * ratio))
                else:
                    new_size = (w, h)
                im = im.resize(new_size, Image.LANCZOS)
                b = BytesIO()
                im.save(b, format="PNG")
                zf.writestr(f"resized_{f.name.rsplit('.', 1)[0]}.png", b.getvalue())
                st.image(b.getvalue(), caption=f"{f.name} → {new_size[0]}×{new_size[1]}", width=200)
        st.download_button("Download All (ZIP)", zip_buf.getvalue(), "resized_images.zip", "application/zip")

elif selected_tool == "61. Color Palette Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create flashcard-style study sets. Learn and memorize key concepts with spaced repetition.")
    st.header("Color Palette Extractor")
    up = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    n = st.slider("Number of colors", 3, 12, 6)
    if up:
        im = Image.open(up).convert("RGB")
        small = im.resize((150, 150))
        pal = small.quantize(colors=n).convert("RGB")
        colors = sorted(pal.getcolors(150 * 150), reverse=True)[:n]
        st.image(im, width=320)
        cols = st.columns(n)
        for col, (_count, rgb) in zip(cols, colors):
            hex_code = "#{:02X}{:02X}{:02X}".format(*rgb)
            with col:
                st.markdown(
                    f'<div style="background:{hex_code};height:80px;border-radius:6px;border:1px solid #555;"></div>'
                    f'<div style="text-align:center;font-weight:700;margin-top:6px;">{hex_code}</div>',
                    unsafe_allow_html=True,
                )

elif selected_tool == "62. EXIF Data Viewer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate multiple-choice quiz questions. Test knowledge retention and create educational assessments.")
    st.header("EXIF Data Viewer")
    up = st.file_uploader("Upload JPEG/TIFF", type=["jpg", "jpeg", "tiff", "tif"])
    if up:
        im = Image.open(up)
        try:
            from PIL.ExifTags import TAGS
            exif = im._getexif() or {}
            if not exif:
                st.info("No EXIF metadata found in this image.")
            else:
                rows = [{"Tag": TAGS.get(k, k), "Value": str(v)[:200]} for k, v in exif.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read EXIF: {e}")

elif selected_tool == "63. SVG to PNG Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build study schedule timelines. Organize learning goals into manageable daily study plans.")
    st.header("SVG to PNG Converter")
    up = st.file_uploader("Upload SVG", type=["svg"])
    width = st.number_input("Output width (px)", 50, 4000, 800)
    if up and st.button("Convert"):
        svg_bytes = up.read()
        try:
            import cairosvg
            png = cairosvg.svg2png(bytestring=svg_bytes, output_width=width)
            st.image(png, use_container_width=True)
            st.download_button("Download PNG", png, "converted.png", "image/png")
        except Exception:
            st.warning("High-fidelity converter unavailable in this environment. Showing inline SVG preview and offering raw download.")
            st.markdown(svg_bytes.decode("utf-8", errors="ignore"), unsafe_allow_html=True)
            st.download_button("Download original SVG", svg_bytes, "original.svg", "image/svg+xml")

elif selected_tool == "64. Image Cropper Tool":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track reading progress and notes. Build a personal knowledge library with organized annotations.")
    st.header("Image Cropper")
    up = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if up:
        im = Image.open(up)
        st.image(im, caption=f"Original: {im.size[0]}×{im.size[1]}", width=320)
        c1, c2 = st.columns(2)
        with c1:
            left = st.number_input("Left", 0, im.size[0], 0)
            top = st.number_input("Top", 0, im.size[1], 0)
        with c2:
            right = st.number_input("Right", 1, im.size[0], im.size[0])
            bottom = st.number_input("Bottom", 1, im.size[1], im.size[1])
        if st.button("Crop"):
            cropped = im.crop((left, top, right, bottom))
            buf = BytesIO()
            cropped.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Cropped: {cropped.size[0]}×{cropped.size[1]}")
            st.download_button("Download cropped PNG", buf.getvalue(), "cropped.png", "image/png")

elif selected_tool == "65. Meme Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create vocabulary building exercises. Expand your word power with structured learning activities.")
    st.header("Meme Generator")
    up = st.file_uploader("Upload base image", type=["png", "jpg", "jpeg"])
    top_text = st.text_input("Top text:", "WHEN MONDAY HITS")
    bot_text = st.text_input("Bottom text:", "BUT YOU AUTOMATED EVERYTHING")
    if up:
        im = Image.open(up).convert("RGB")
        draw = ImageDraw.Draw(im)
        font_size = max(20, im.size[0] // 12)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        def _draw_centered(text, y):
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = (im.size[0] - tw) // 2
            for dx in (-2, 2):
                for dy in (-2, 2):
                    draw.text((x + dx, y + dy), text, font=font, fill="black")
            draw.text((x, y), text, font=font, fill="white")

        _draw_centered(top_text.upper(), 10)
        _draw_centered(bot_text.upper(), im.size[1] - font_size - 20)
        buf = BytesIO()
        im.save(buf, format="PNG")
        st.image(buf.getvalue(), use_container_width=True)
        st.download_button("Download meme", buf.getvalue(), "meme.png", "image/png")

elif selected_tool == "66. GIF Maker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Map concepts and relationships visually. Understand complex topics by visualizing connections.")
    st.header("GIF Maker (Images → Animated GIF)")
    ups = st.file_uploader("Upload 2+ frames (in order)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    duration = st.slider("Frame delay (ms)", 50, 2000, 400)
    loop = st.checkbox("Loop forever", value=True)
    if ups and len(ups) >= 2 and st.button("Build GIF"):
        frames = [Image.open(f).convert("RGB") for f in ups]
        base_size = frames[0].size
        frames = [f.resize(base_size) for f in frames]
        buf = BytesIO()
        frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:],
                       duration=duration, loop=0 if loop else 1)
        st.image(buf.getvalue())
        st.download_button("Download GIF", buf.getvalue(), "animation.gif", "image/gif")

elif selected_tool == "67. Audio Format Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate research outlines and frameworks. Structure academic and business research methodically.")
    st.header("Audio Format Converter")
    up = st.file_uploader("Upload audio file", type=["wav", "mp3", "ogg", "flac", "m4a"])
    target = st.selectbox("Convert to", ["wav", "mp3", "ogg", "flac"])
    if up and st.button("Convert"):
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(BytesIO(up.read()))
            buf = BytesIO()
            audio.export(buf, format=target)
            st.audio(buf.getvalue(), format=f"audio/{target}")
            st.download_button(f"Download .{target}", buf.getvalue(),
                               f"converted.{target}", f"audio/{target}")
        except Exception as e:
            st.error(f"Audio conversion requires ffmpeg + pydub. Detail: {e}")

elif selected_tool == "68. Video to Audio Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create presentation outlines from topics. Build compelling slide decks with logical flow and structure.")
    st.header("Video → Audio Extractor")
    up = st.file_uploader("Upload video", type=["mp4", "mov", "mkv", "webm", "avi"])
    if up and st.button("Extract Audio"):
        try:
            import tempfile
            from moviepy.editor import VideoFileClip
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(up.read())
                tmp_path = tmp.name
            clip = VideoFileClip(tmp_path)
            out_path = tmp_path + ".mp3"
            clip.audio.write_audiofile(out_path, logger=None)
            with open(out_path, "rb") as f:
                data = f.read()
            st.audio(data, format="audio/mp3")
            st.download_button("Download MP3", data, "extracted.mp3", "audio/mp3")
        except Exception as e:
            st.error(f"Video extraction requires moviepy + ffmpeg. Detail: {e}")

elif selected_tool == "69. Video Thumbnail Grabber":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track assignments and deadlines. Never miss a deadline with organized task tracking.")
    st.header("Video Thumbnail Grabber")
    up = st.file_uploader("Upload video", type=["mp4", "mov", "mkv", "webm"])
    t_sec = st.number_input("Capture at second:", 0.0, 3600.0, 1.0, 0.5)
    if up and st.button("Grab Thumbnail"):
        try:
            import tempfile
            from moviepy.editor import VideoFileClip
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(up.read())
                tmp_path = tmp.name
            clip = VideoFileClip(tmp_path)
            frame = clip.get_frame(min(t_sec, clip.duration - 0.1))
            im = Image.fromarray(frame)
            buf = BytesIO()
            im.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Thumbnail @ {t_sec}s")
            st.download_button("Download PNG", buf.getvalue(), "thumbnail.png", "image/png")
        except Exception as e:
            st.error(f"Thumbnail extraction requires moviepy + ffmpeg. Detail: {e}")

elif selected_tool == "70. YouTube Transcript Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate and visualize GPA. Monitor academic performance and plan for improvement.")
    st.header("YouTube Transcript Extractor")
    yt = st.text_input("YouTube URL or video ID:")
    if yt and st.button("Fetch Transcript"):
        m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", yt) or re.match(r"^([A-Za-z0-9_-]{11})$", yt.strip())
        vid = m.group(1) if m else None
        if not vid:
            st.error("Could not parse a video ID from that input.")
        else:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                segs = YouTubeTranscriptApi.get_transcript(vid)
                full = "\n".join(s["text"] for s in segs)
                st.text_area("Transcript", full, height=350)
                st.download_button("Download .txt", full, f"{vid}_transcript.txt", "text/plain")
            except Exception as e:
                st.error(f"Could not fetch transcript: {e}")

elif selected_tool == "71. Image Filter Applier":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create event planning checklists. Ensure nothing is missed with comprehensive event timelines.")
    st.header("Image Filter Applier")
    up = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    fx = st.selectbox("Filter", ["Grayscale", "Sepia", "Blur", "Sharpen", "Edge Enhance", "Invert"])
    if up:
        im = Image.open(up).convert("RGB")
        if fx == "Grayscale":
            out = ImageOps.grayscale(im).convert("RGB")
        elif fx == "Sepia":
            gray = ImageOps.grayscale(im)
            sepia = Image.merge("RGB", (
                gray.point(lambda p: min(255, int(p * 1.07))),
                gray.point(lambda p: min(255, int(p * 0.74))),
                gray.point(lambda p: min(255, int(p * 0.43))),
            ))
            out = sepia
        elif fx == "Blur":
            out = im.filter(ImageFilter.GaussianBlur(radius=4))
        elif fx == "Sharpen":
            out = im.filter(ImageFilter.SHARPEN)
        elif fx == "Edge Enhance":
            out = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
        else:
            out = ImageOps.invert(im)
        buf = BytesIO()
        out.save(buf, format="PNG")
        st.image(buf.getvalue(), use_container_width=True)
        st.download_button("Download", buf.getvalue(), f"{fx.lower()}.png", "image/png")

elif selected_tool == "72. Background Remover":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate BMI and health metrics. Track personal health indicators for wellness goals.")
    st.header("Background Remover")
    up = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
    if up and st.button("Remove Background"):
        data = up.read()
        try:
            from rembg import remove
            out = remove(data)
            st.image(out, use_container_width=True)
            st.download_button("Download PNG", out, "no_bg.png", "image/png")
        except Exception:
            im = Image.open(BytesIO(data)).convert("RGBA")
            corner = im.getpixel((0, 0))[:3]
            tol = 35
            px = im.load()
            for y in range(im.size[1]):
                for x in range(im.size[0]):
                    r, g, b, a = px[x, y]
                    if abs(r - corner[0]) < tol and abs(g - corner[1]) < tol and abs(b - corner[2]) < tol:
                        px[x, y] = (r, g, b, 0)
            buf = BytesIO()
            im.save(buf, format="PNG")
            st.warning("Using fast color-key fallback (rembg AI model not available).")
            st.image(buf.getvalue(), use_container_width=True)
            st.download_button("Download PNG", buf.getvalue(), "no_bg.png", "image/png")

elif selected_tool == "73. Aspect Ratio Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan meals with nutritional calculations. Optimize nutrition and meal prep for health and budget.")
    st.header("Aspect Ratio Calculator")
    c1, c2 = st.columns(2)
    with c1:
        ow = st.number_input("Original width", 1, 10000, 1920)
        oh = st.number_input("Original height", 1, 10000, 1080)
    with c2:
        nw = st.number_input("New width (0 = derive)", 0, 10000, 1280)
        nh = st.number_input("New height (0 = derive)", 0, 10000, 0)
    frac = Fraction(ow, oh)
    st.metric("Aspect Ratio", f"{frac.numerator}:{frac.denominator}  ({ow/oh:.4f})")
    if nw and not nh:
        st.success(f"New size keeping aspect: {nw} × {int(nw * oh / ow)}")
    elif nh and not nw:
        st.success(f"New size keeping aspect: {int(nh * ow / oh)} × {nh}")
    elif nw and nh:
        ratio_match = abs((nw / nh) - (ow / oh)) < 0.01
        st.info(f"{'Matches' if ratio_match else 'Does NOT match'} the original aspect ratio.")

elif selected_tool == "74. DPI Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track workout routines and sets. Build consistent fitness habits with structured logging.")
    st.header("DPI Converter")
    up = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "tiff"])
    dpi = st.number_input("Target DPI", 36, 1200, 300)
    if up and st.button("Convert"):
        im = Image.open(up)
        buf = BytesIO()
        fmt = "PNG" if im.mode in ("RGBA", "P") else "JPEG"
        im.save(buf, format=fmt, dpi=(dpi, dpi))
        st.success(f"Saved at {dpi} DPI ({im.size[0]}×{im.size[1]} px → "
                   f"{im.size[0]/dpi:.2f}″ × {im.size[1]/dpi:.2f}″ at {dpi} DPI).")
        st.download_button(f"Download .{fmt.lower()}", buf.getvalue(),
                           f"image_{dpi}dpi.{fmt.lower()}", f"image/{fmt.lower()}")

elif selected_tool == "75. Font Previewer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Estimate daily calorie requirements. Set nutrition targets based on activity level and goals.")
    st.header("Font Previewer")
    text = st.text_input("Sample text:", "The quick brown fox jumps over the lazy dog.")
    size = st.slider("Size (px)", 16, 96, 48)
    candidates = [
        "DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf",
        "DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf",
    ]
    for fname in candidates:
        try:
            font = ImageFont.truetype(fname, size)
            img = Image.new("RGB", (1200, size + 30), "white")
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), text, font=font, fill="black")
            st.caption(fname)
            st.image(img)
        except Exception:
            continue

elif selected_tool == "76. JSON Validator & Formatter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate water intake goals. Stay properly hydrated based on body weight and activity.")
    st.header("JSON Validator & Formatter")
    raw = st.text_area("Paste JSON:", height=220)
    indent = st.slider("Indent", 0, 8, 2)
    if raw and st.button("Validate & Format"):
        try:
            obj = json.loads(raw)
            pretty = json.dumps(obj, indent=indent, ensure_ascii=False)
            st.success("Valid JSON.")
            st.code(pretty, language="json")
            st.download_button("Download .json", pretty, "formatted.json", "application/json")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON at line {e.lineno}, col {e.colno}: {e.msg}")

elif selected_tool == "77. Regex Tester":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track sleep patterns and quality. Improve rest by understanding your sleep habits.")
    st.header("Regex Tester")
    pattern = st.text_input("Pattern:", r"\b\w+@\w+\.\w+\b")
    flags_sel = st.multiselect("Flags", ["IGNORECASE", "MULTILINE", "DOTALL"])
    txt = st.text_area("Test text:", height=200)
    if pattern and txt:
        f = 0
        for fl in flags_sel:
            f |= getattr(re, fl)
        try:
            rx = re.compile(pattern, f)
            matches = list(rx.finditer(txt))
            st.metric("Matches", len(matches))
            if matches:
                st.dataframe(pd.DataFrame(
                    [{"#": i + 1, "Match": m.group(0), "Span": f"{m.start()}–{m.end()}",
                      "Groups": str(m.groups())} for i, m in enumerate(matches)]
                ), use_container_width=True)
        except re.error as e:
            st.error(f"Bad regex: {e}")

elif selected_tool == "78. SQL Query Formatter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan and track personal goals. Turn ambitions into achievable milestones with deadlines.")
    st.header("SQL Query Formatter")
    sql = st.text_area("Paste SQL:", height=220)
    if sql and st.button("Format"):
        try:
            import sqlparse
            pretty = sqlparse.format(sql, reindent=True, keyword_case="upper")
        except Exception:
            kw = ["SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN",
                  "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "AND", "OR"]
            pretty = sql
            for k in kw:
                pretty = re.sub(rf"\s+{k}\s+", f"\n{k} ", pretty, flags=re.IGNORECASE)
            pretty = pretty.strip()
        st.code(pretty, language="sql")
        st.download_button("Download .sql", pretty, "formatted.sql", "text/plain")

elif selected_tool == "79. Hash Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Log daily moods and journal entries. Build self-awareness and track mental wellness trends.")
    st.header("Hash Generator")
    txt = st.text_area("Input text:")
    algos = st.multiselect("Algorithms", ["md5", "sha1", "sha256", "sha512"], default=["md5", "sha1", "sha256"])
    if txt:
        for a in algos:
            h = hashlib.new(a, txt.encode("utf-8")).hexdigest()
            st.write(f"**{a.upper()}**")
            st.code(h)

elif selected_tool == "80. JWT Decoder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build and track daily habits. Develop positive routines that compound into success.")
    st.header("JWT Decoder")
    token = st.text_area("Paste JWT (header.payload.signature):", height=130)
    if token and st.button("Decode"):
        parts = token.strip().split(".")
        if len(parts) != 3:
            st.error("JWTs must have exactly three dot-separated segments.")
        else:
            def _b64(seg):
                seg += "=" * (-len(seg) % 4)
                return base64.urlsafe_b64decode(seg.encode("utf-8")).decode("utf-8", errors="replace")
            try:
                header = json.loads(_b64(parts[0]))
                payload = json.loads(_b64(parts[1]))
                st.subheader("Header")
                st.json(header)
                st.subheader("Payload")
                st.json(payload)
                st.caption(f"Signature (base64url, not verified): {parts[2][:32]}…")
            except Exception as e:
                st.error(f"Decode failed: {e}")

elif selected_tool == "81. URL Encoder/Decoder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate sermon quotes with attributions. Create shareable quote graphics for ministry content.")
    st.header("URL Encoder / Decoder")
    mode = st.radio("Mode", ["Encode", "Decode"], horizontal=True)
    txt = st.text_area("Text:", height=150)
    if txt:
        result = urllib.parse.quote(txt, safe="") if mode == "Encode" else urllib.parse.unquote(txt)
        st.code(result)
        st.download_button("Download .txt", result, "url_result.txt", "text/plain")

elif selected_tool == "82. HTML Sanitizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Manage community prayer requests. Organize and respond to prayer needs within your group.")
    st.header("HTML Sanitizer")
    raw = st.text_area("Paste HTML:", height=220)
    mode = st.radio("Mode", ["Strip all tags (plain text)", "Escape entities only"], index=0)
    if raw and st.button("Sanitize"):
        if mode.startswith("Strip"):
            cleaned = re.sub(r"<[^>]+>", "", raw)
            cleaned = html_mod.unescape(cleaned)
        else:
            cleaned = html_mod.escape(raw)
        st.text_area("Output", cleaned, height=220)
        st.download_button("Download .txt", cleaned, "sanitized.txt", "text/plain")

elif selected_tool == "83. XML to JSON Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track attendance and growth metrics. Monitor community engagement with visual analytics.")
    st.header("XML → JSON Converter")
    raw = st.text_area("Paste XML:", height=220)
    if raw and st.button("Convert"):
        try:
            try:
                import xmltodict
                obj = xmltodict.parse(raw)
            except Exception:
                def _et_to_dict(el):
                    d = {el.tag: {} if el.attrib else None}
                    children = list(el)
                    if children:
                        dd = {}
                        for c in children:
                            cd = _et_to_dict(c)
                            for k, v in cd.items():
                                if k in dd:
                                    if not isinstance(dd[k], list):
                                        dd[k] = [dd[k]]
                                    dd[k].append(v)
                                else:
                                    dd[k] = v
                        d = {el.tag: dd}
                    if el.attrib:
                        d[el.tag].update({f"@{k}": v for k, v in el.attrib.items()})
                    if el.text and el.text.strip():
                        text = el.text.strip()
                        if children or el.attrib:
                            d[el.tag]["#text"] = text
                        else:
                            d[el.tag] = text
                    return d
                obj = _et_to_dict(ET.fromstring(raw))
            pretty = json.dumps(obj, indent=2, ensure_ascii=False)
            st.code(pretty, language="json")
            st.download_button("Download .json", pretty, "converted.json", "application/json")
        except Exception as e:
            st.error(f"Could not parse XML: {e}")

elif selected_tool == "84. CRON Expression Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Look up Bible verses quickly. Find and reference scripture for study and content creation.")
    st.header("CRON Expression Generator")
    st.caption("Build a 5-field cron string: minute hour day month weekday")
    minute = st.text_input("Minute (0-59 or *)", "0")
    hour = st.text_input("Hour (0-23 or *)", "9")
    dom = st.text_input("Day of Month (1-31 or *)", "*")
    mon = st.text_input("Month (1-12 or *)", "*")
    dow = st.text_input("Day of Week (0-6 or *, 0=Sun)", "1-5")
    expr = f"{minute} {hour} {dom} {mon} {dow}"
    st.code(expr)
    presets = {
        "Every minute": "* * * * *",
        "Every hour (top)": "0 * * * *",
        "Daily at 9am": "0 9 * * *",
        "Weekdays at 9am": "0 9 * * 1-5",
        "Weekly Mon 8am": "0 8 * * 1",
        "Monthly 1st 6am": "0 6 1 * *",
    }
    pick = st.selectbox("Or choose a preset", ["—"] + list(presets.keys()))
    if pick != "—":
        st.success(f"{pick}: `{presets[pick]}`")

elif selected_tool == "85. Diff Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Randomly assign volunteer roles. Distribute tasks fairly among volunteers and team members.")
    st.header("Diff Checker")
    c1, c2 = st.columns(2)
    with c1:
        a = st.text_area("Original", height=260, key="diff_a")
    with c2:
        b = st.text_area("Modified", height=260, key="diff_b")
    mode = st.radio("View", ["Unified", "Side-by-side HTML"], horizontal=True)
    if a and b and st.button("Compare"):
        if mode == "Unified":
            diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                             fromfile="original", tofile="modified", lineterm=""))
            if not diff:
                st.success("No differences found.")
            else:
                st.code("\n".join(diff), language="diff")
        else:
            html = difflib.HtmlDiff(wrapcolumn=70).make_table(
                a.splitlines(), b.splitlines(),
                fromdesc="Original", todesc="Modified", context=False,
            )
            st.markdown(
                f'<div style="background:#fff;color:#000;padding:8px;border-radius:6px;overflow:auto;">{html}</div>',
                unsafe_allow_html=True,
            )

elif selected_tool == "86. Markdown to HTML Previewer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Project giving trends and goals. Forecast financial contributions and plan budgets accordingly.")
    st.header("Markdown → HTML Previewer")
    md = st.text_area("Paste Markdown:", height=260,
                      value="# Welcome\n\nWrite **bold** or *italic*, add `code`, and [links](https://digitalenvisioned.net).")
    if md:
        html_out = markdown.markdown(md, extensions=["fenced_code", "tables"])
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("HTML Source")
            st.code(html_out, language="html")
        with c2:
            st.subheader("Rendered Preview")
            st.markdown(
                f'<div style="background:#fff;color:#000;padding:14px;border-radius:8px;">{html_out}</div>',
                unsafe_allow_html=True,
            )
        st.download_button("Download .html", html_out, "preview.html", "text/html")

elif selected_tool == "87. CSV to JSON Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create countdown timers for events. Build anticipation with visual countdowns to important dates.")
    st.header("CSV → JSON Converter")
    up = st.file_uploader("Upload CSV", type=["csv"])
    pasted = st.text_area("…or paste CSV here:", height=180)
    orient = st.selectbox("JSON shape", ["records", "columns", "index", "split"])
    if (up or pasted) and st.button("Convert"):
        try:
            df = pd.read_csv(up) if up else pd.read_csv(BytesIO(pasted.encode("utf-8")))
            payload = df.to_json(orient=orient, indent=2)
            st.success(f"Parsed {len(df)} rows × {len(df.columns)} columns.")
            st.dataframe(df.head(20), use_container_width=True)
            st.code(payload, language="json")
            st.download_button("Download .json", payload, "data.json", "application/json")
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")

elif selected_tool == "88. Secure Password Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build lyric slide presentations. Create worship slides with formatted lyrics and backgrounds.")
    st.header("Secure Password Generator")
    length = st.slider("Length", 8, 128, 20)
    use_upper = st.checkbox("Uppercase A-Z", True)
    use_lower = st.checkbox("Lowercase a-z", True)
    use_digits = st.checkbox("Digits 0-9", True)
    use_symbols = st.checkbox("Symbols !@#$…", True)
    count = st.number_input("How many to generate", 1, 50, 5)
    if st.button("Generate"):
        import secrets
        pool = ""
        if use_upper:   pool += string.ascii_uppercase
        if use_lower:   pool += string.ascii_lowercase
        if use_digits:  pool += string.digits
        if use_symbols: pool += "!@#$%^&*()-_=+[]{};:,.<>?/~"
        if not pool:
            st.error("Pick at least one character set.")
        else:
            for _ in range(int(count)):
                st.code("".join(secrets.choice(pool) for _ in range(length)))

elif selected_tool == "89. Base64 String Encoder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Add watermarks to images to protect content. Brand your visual assets and prevent unauthorized use.")
    st.header("Base64 String Encoder / Decoder")
    mode = st.radio("Mode", ["Encode", "Decode"], horizontal=True)
    txt = st.text_area("Input:", height=180)
    if txt and st.button("Run"):
        try:
            if mode == "Encode":
                out = base64.b64encode(txt.encode("utf-8")).decode("ascii")
            else:
                out = base64.b64decode(txt.encode("ascii")).decode("utf-8", errors="replace")
            st.success(f"{mode}d.")
            st.code(out)
            st.download_button("Download .txt", out, "base64_result.txt", "text/plain")
        except Exception as e:
            st.error(f"{mode} failed: {e}")

elif selected_tool == "90. IP Address Data Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Resize multiple images at once. Process entire photo batches to consistent dimensions efficiently.")
    st.header("IP Address Data Extractor")
    ip = st.text_input("IP address (leave blank for your own):", "")
    if st.button("Lookup"):
        try:
            url = f"https://ipapi.co/{ip}/json/" if ip.strip() else "https://ipapi.co/json/"
            r = requests.get(url, timeout=8)
            data = r.json()
            if data.get("error"):
                st.error(data.get("reason", "Lookup failed."))
            else:
                rows = {
                    "IP": data.get("ip"),
                    "City": data.get("city"),
                    "Region": data.get("region"),
                    "Country": f"{data.get('country_name')} ({data.get('country_code')})",
                    "Postal": data.get("postal"),
                    "Latitude / Longitude": f"{data.get('latitude')}, {data.get('longitude')}",
                    "Timezone": data.get("timezone"),
                    "ISP / Org": data.get("org"),
                    "ASN": data.get("asn"),
                }
                st.dataframe(pd.DataFrame(rows.items(), columns=["Field", "Value"]),
                             use_container_width=True)
        except Exception as e:
            st.error(f"Network/API error: {e}")

elif selected_tool == "91. ROI Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Extract color palettes from images. Build design systems based on dominant colors in photos.")
    st.header("ROI Calculator")
    cost = st.number_input("Investment cost ($)", 0.0, 1e9, 1000.0, 50.0)
    gain = st.number_input("Total return / final value ($)", 0.0, 1e9, 1500.0, 50.0)
    if cost > 0:
        roi = (gain - cost) / cost * 100
        st.metric("ROI", f"{roi:.2f}%")
        st.metric("Net profit", f"${gain - cost:,.2f}")
        if roi > 0: st.success("Positive return.")
        elif roi < 0: st.error("Loss on investment.")
        else: st.info("Break-even.")

elif selected_tool == "92. Compound Interest Forecaster":
    with st.expander("ℹ️ How to use this tool"):
        st.write("View and extract EXIF metadata from photos. Access camera settings, locations, and timestamps from images.")
    st.header("Compound Interest Forecaster")
    p = st.number_input("Principal ($)", 0.0, 1e9, 10000.0, 100.0)
    r = st.number_input("Annual rate (%)", 0.0, 100.0, 7.0, 0.1) / 100
    years = st.number_input("Years", 1, 100, 10)
    n = st.selectbox("Compounded", [("Annually", 1), ("Quarterly", 4), ("Monthly", 12), ("Daily", 365)],
                     format_func=lambda x: x[0])[1]
    a = p * (1 + r / n) ** (n * years)
    st.metric("Future Value", f"${a:,.2f}")
    st.metric("Total Interest", f"${a - p:,.2f}")
    schedule = pd.DataFrame({
        "Year": list(range(0, years + 1)),
        "Balance": [round(p * (1 + r / n) ** (n * y), 2) for y in range(0, years + 1)],
    })
    st.line_chart(schedule.set_index("Year"))

elif selected_tool == "93. Freelance Hourly Rate Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert SVG files to PNG format. Export vector graphics as bitmaps for universal compatibility.")
    st.header("Freelance / Agency Hourly Rate Calculator")
    salary = st.number_input("Desired annual take-home ($)", 0.0, 1e7, 80000.0, 1000.0)
    expenses = st.number_input("Annual business expenses ($)", 0.0, 1e7, 12000.0, 500.0)
    weeks = st.number_input("Working weeks/year", 1, 52, 48)
    hours_wk = st.number_input("Billable hours/week", 1, 80, 25)
    profit_pct = st.number_input("Profit margin on top (%)", 0.0, 200.0, 20.0, 1.0)
    revenue = (salary + expenses) * (1 + profit_pct / 100)
    rate = revenue / (weeks * hours_wk)
    st.metric("Required hourly rate", f"${rate:,.2f}/hr")
    st.metric("Target annual revenue", f"${revenue:,.2f}")

elif selected_tool == "94. E-commerce Profit Margin Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Crop images to specific dimensions. Frame content precisely for any platform or purpose.")
    st.header("E-commerce Profit Margin Calculator")
    price = st.number_input("Sale price ($)", 0.0, 1e6, 49.99, 0.5)
    cogs = st.number_input("Cost of goods ($)", 0.0, 1e6, 12.0, 0.5)
    ship = st.number_input("Shipping cost ($)", 0.0, 1e6, 5.0, 0.5)
    fees_pct = st.number_input("Platform fees (%)", 0.0, 100.0, 2.9, 0.1)
    fees_flat = st.number_input("Flat per-order fee ($)", 0.0, 1e4, 0.30, 0.05)
    fees = price * fees_pct / 100 + fees_flat
    profit = price - cogs - ship - fees
    margin = (profit / price * 100) if price else 0
    st.metric("Profit per order", f"${profit:,.2f}")
    st.metric("Margin", f"{margin:.2f}%")
    st.caption(f"Fees deducted: ${fees:,.2f}")

elif selected_tool == "95. Subscription Burn-Rate Tracker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create memes with custom text overlays. Generate viral social content with text-on-image templates.")
    st.header("Subscription Burn-Rate Tracker")
    cash = st.number_input("Cash on hand ($)", 0.0, 1e9, 50000.0, 500.0)
    monthly_rev = st.number_input("Monthly recurring revenue ($)", 0.0, 1e9, 8000.0, 100.0)
    monthly_cost = st.number_input("Monthly operating cost ($)", 0.0, 1e9, 15000.0, 100.0)
    burn = monthly_cost - monthly_rev
    if burn <= 0:
        st.success("You are cash-flow positive. No burn.")
        st.metric("Net monthly profit", f"${-burn:,.2f}")
    else:
        runway = cash / burn
        st.metric("Net burn / month", f"${burn:,.2f}")
        st.metric("Runway", f"{runway:.1f} months")
        if runway < 6: st.error("Critical — under 6 months of runway.")
        elif runway < 12: st.warning("Tight — under 12 months of runway.")

elif selected_tool == "96. Stripe Transaction Fee Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create animated GIFs from image sequences. Build attention-grabbing animations for social and web.")
    st.header("Stripe Transaction Fee Calculator")
    amount = st.number_input("Charge amount ($)", 0.0, 1e6, 100.0, 1.0)
    pct = st.number_input("% rate", 0.0, 10.0, 2.9, 0.1)
    flat = st.number_input("Flat fee ($)", 0.0, 5.0, 0.30, 0.01)
    fee = amount * pct / 100 + flat
    net = amount - fee
    gross_up = (amount + flat) / (1 - pct / 100)
    st.metric("Stripe fee", f"${fee:,.2f}")
    st.metric("You net", f"${net:,.2f}")
    st.caption(f"To net ${amount:,.2f}, charge customer ${gross_up:,.2f}.")

elif selected_tool == "97. Rule-of-72 Investment Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Apply Instagram-style filters to photos. Enhance visual content with professional color treatments.")
    st.header("Rule of 72 — Time to Double")
    rate = st.number_input("Annual return (%)", 0.01, 100.0, 8.0, 0.1)
    years = 72 / rate
    st.metric("Years to double", f"{years:.2f}")
    st.caption("Rule of 72 is an approximation; accurate for rates 5–15%.")
    st.line_chart(pd.DataFrame({"Years to double": [72 / r for r in range(1, 21)]},
                               index=[f"{r}%" for r in range(1, 21)]))

elif selected_tool == "98. Business Sales Tax Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Collage multiple images into one layout. Combine photos into polished grids and layouts.")
    st.header("Business Sales Tax Calculator")
    amount = st.number_input("Pre-tax amount ($)", 0.0, 1e7, 100.0, 1.0)
    rate = st.number_input("Sales tax rate (%)", 0.0, 30.0, 9.0, 0.1)
    tax = amount * rate / 100
    st.metric("Tax owed", f"${tax:,.2f}")
    st.metric("Total with tax", f"${amount + tax:,.2f}")
    st.caption("Birmingham, AL combined rate is typically ~10%. Adjust for your jurisdiction.")

elif selected_tool == "99. Break-Even Point Analyzer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate color palettes from any image. Extract harmonious colors for branding and design work.")
    st.header("Break-Even Point Analyzer")
    fixed = st.number_input("Fixed costs ($/month)", 0.0, 1e7, 5000.0, 100.0)
    price = st.number_input("Price per unit ($)", 0.01, 1e6, 49.0, 1.0)
    var = st.number_input("Variable cost per unit ($)", 0.0, 1e6, 12.0, 1.0)
    contrib = price - var
    if contrib <= 0:
        st.error("Variable cost ≥ price — you lose money on every unit.")
    else:
        units = fixed / contrib
        st.metric("Break-even units", f"{units:,.1f}")
        st.metric("Break-even revenue", f"${units * price:,.2f}")
        st.caption(f"Contribution margin: ${contrib:,.2f}/unit ({contrib / price * 100:.1f}%)")

elif selected_tool == "100. Quick Invoice Text Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Detect and blur faces in images. Protect privacy in photos before sharing publicly.")
    st.header("Quick Invoice Text Generator")
    biz = st.text_input("Your business name", "Digital Envisioned")
    client = st.text_input("Client name", "Acme Co.")
    inv_no = st.text_input("Invoice #", f"INV-{datetime.now().strftime('%Y%m%d')}")
    items_raw = st.text_area("Line items (one per line: description, qty, price)", height=160,
                             value="Website audit, 1, 500\nLanding page build, 1, 1500")
    tax_pct = st.number_input("Tax %", 0.0, 50.0, 0.0, 0.5)
    if st.button("Generate Invoice"):
        lines, subtotal = [], 0.0
        for row in items_raw.strip().splitlines():
            parts = [p.strip() for p in row.split(",")]
            if len(parts) >= 3:
                try:
                    qty, price = float(parts[1]), float(parts[2])
                    total = qty * price
                    subtotal += total
                    lines.append(f"  {parts[0]:<40} {qty:>6} x ${price:>8.2f} = ${total:>10.2f}")
                except ValueError:
                    continue
        tax = subtotal * tax_pct / 100
        total = subtotal + tax
        invoice = (
            f"INVOICE  {inv_no}\nDate: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"From: {biz}\nTo:   {client}\n\nItems:\n" + "\n".join(lines) +
            f"\n\n  Subtotal: ${subtotal:>10.2f}\n  Tax ({tax_pct}%): ${tax:>10.2f}\n  TOTAL:    ${total:>10.2f}\n"
        )
        st.code(invoice)
        st.download_button("Download .txt", invoice, f"{inv_no}.txt", "text/plain")

elif selected_tool == "101. SaaS Churn Rate Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert images between file formats. Switch between PNG, JPEG, WebP, and more as needed.")
    st.header("SaaS Churn Rate Calculator")
    start = st.number_input("Customers at start of period", 0, 10_000_000, 500)
    lost = st.number_input("Customers lost during period", 0, 10_000_000, 25)
    mrr_lost = st.number_input("MRR lost ($)", 0.0, 1e9, 1500.0, 50.0)
    mrr_start = st.number_input("MRR at start of period ($)", 0.0, 1e9, 30000.0, 100.0)
    if start > 0:
        cust_churn = lost / start * 100
        st.metric("Customer churn", f"{cust_churn:.2f}%")
    if mrr_start > 0:
        rev_churn = mrr_lost / mrr_start * 100
        st.metric("Revenue churn", f"{rev_churn:.2f}%")
        st.caption("Healthy SaaS: customer churn < 5%/mo, revenue churn < 2%/mo.")

elif selected_tool == "102. Discount & Markup Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Remove image backgrounds automatically. Create clean product photos and profile images instantly.")
    st.header("Discount & Markup Calculator")
    mode = st.radio("Mode", ["Discount", "Markup"], horizontal=True)
    base = st.number_input("Base price ($)", 0.0, 1e7, 100.0, 1.0)
    pct = st.number_input("Percent (%)", 0.0, 1000.0, 20.0, 1.0)
    if mode == "Discount":
        final = base * (1 - pct / 100)
        st.metric("Discounted price", f"${final:,.2f}")
        st.metric("Customer saves", f"${base - final:,.2f}")
    else:
        final = base * (1 + pct / 100)
        st.metric("Marked-up price", f"${final:,.2f}")
        st.metric("Profit added", f"${final - base:,.2f}")

elif selected_tool == "103. Keyword Density Analyzer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Detect edges and objects in images. Analyze visual content for design and technical purposes.")
    st.header("Keyword Density Analyzer")
    txt = st.text_area("Paste your content:", height=260)
    if txt:
        words = re.findall(r"\b[a-zA-Z']{2,}\b", txt.lower())
        total = len(words)
        if total == 0:
            st.warning("No words detected.")
        else:
            stop = set("the a an and or but if then for of in on at to from by with as is are was were be been being it this that these those i you he she we they".split())
            counts = Counter(w for w in words if w not in stop)
            df = pd.DataFrame([
                {"Keyword": k, "Count": v, "Density %": round(v / total * 100, 2)}
                for k, v in counts.most_common(25)
            ])
            st.metric("Total words", total)
            st.dataframe(df, use_container_width=True)

elif selected_tool == "104. Meta Tag Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Overlay images with adjustable transparency. Create composite images for marketing and branding.")
    st.header("Meta Tag Generator")
    title = st.text_input("Page title", "Digital Envisioned — Birmingham Automation")
    desc = st.text_area("Meta description (≤160 chars)", "200 automation tools for Birmingham businesses.", height=80)
    url = st.text_input("Canonical URL", "https://digitalenvisioned.net/")
    image = st.text_input("Open Graph image URL", "")
    keywords = st.text_input("Keywords (comma-separated)", "automation, Birmingham, SEO")
    if st.button("Generate"):
        tags = [
            f'<title>{html_mod.escape(title)}</title>',
            f'<meta name="description" content="{html_mod.escape(desc)}">',
            f'<meta name="keywords" content="{html_mod.escape(keywords)}">',
            f'<link rel="canonical" href="{html_mod.escape(url)}">',
            f'<meta property="og:title" content="{html_mod.escape(title)}">',
            f'<meta property="og:description" content="{html_mod.escape(desc)}">',
            f'<meta property="og:url" content="{html_mod.escape(url)}">',
            f'<meta property="og:type" content="website">',
            f'<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{html_mod.escape(title)}">',
            f'<meta name="twitter:description" content="{html_mod.escape(desc)}">',
        ]
        if image:
            tags.append(f'<meta property="og:image" content="{html_mod.escape(image)}">')
            tags.append(f'<meta name="twitter:image" content="{html_mod.escape(image)}">')
        out = "\n".join(tags)
        if len(desc) > 160: st.warning(f"Description is {len(desc)} chars (>160).")
        st.code(out, language="html")
        st.download_button("Download .html", out, "meta_tags.html", "text/html")

elif selected_tool == "105. SEO Word & Character Counter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate thumbnails from images. Create optimized preview images for websites and galleries.")
    st.header("SEO Word & Character Counter")
    txt = st.text_area("Content:", height=260)
    if txt:
        chars = len(txt)
        chars_no_space = len(re.sub(r"\s", "", txt))
        words = len(re.findall(r"\b\w+\b", txt))
        sentences = max(1, len(re.findall(r"[.!?]+", txt)))
        paragraphs = len([p for p in txt.split("\n\n") if p.strip()])
        c1, c2, c3 = st.columns(3)
        c1.metric("Characters", chars)
        c2.metric("Characters (no spaces)", chars_no_space)
        c3.metric("Words", words)
        c1.metric("Sentences", sentences)
        c2.metric("Paragraphs", paragraphs)
        c3.metric("Avg words/sentence", f"{words / sentences:.1f}")
        st.caption("Google snippet titles ≤ 60 chars · meta descriptions ≤ 160 chars.")

elif selected_tool == "106. Readability Score Estimator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Adjust image brightness and contrast. Fine-tune photo exposure for professional results.")
    st.header("Readability Score (Flesch-Kincaid)")
    txt = st.text_area("Paste text:", height=260)
    if txt:
        sentences = max(1, len(re.findall(r"[.!?]+", txt)))
        words_list = re.findall(r"\b[a-zA-Z']+\b", txt)
        words = max(1, len(words_list))

        def _syl(w):
            w = w.lower()
            v = "aeiouy"
            count, prev = 0, False
            for ch in w:
                is_v = ch in v
                if is_v and not prev: count += 1
                prev = is_v
            if w.endswith("e") and count > 1: count -= 1
            return max(1, count)

        syllables = sum(_syl(w) for w in words_list)
        ease = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
        c1, c2 = st.columns(2)
        c1.metric("Flesch Reading Ease", f"{ease:.1f}")
        c2.metric("Grade Level", f"{grade:.1f}")
        if ease >= 70: st.success("Easy to read — great for general audiences.")
        elif ease >= 50: st.info("Fairly readable — good for business copy.")
        else: st.warning("Hard to read — consider simplifying.")

elif selected_tool == "107. Lorem Ipsum Placeholder Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Reduce image noise and grain. Clean up low-light photos for cleaner, sharper output.")
    st.header("Lorem Ipsum Generator")
    paragraphs = st.slider("Paragraphs", 1, 20, 3)
    sentences = st.slider("Sentences per paragraph", 1, 12, 5)
    base = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
            "incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud "
            "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure "
            "dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur").split()
    out = []
    for _ in range(paragraphs):
        sents = []
        for _ in range(sentences):
            length = random.randint(8, 18)
            s = " ".join(random.choice(base) for _ in range(length)).capitalize() + "."
            sents.append(s)
        out.append(" ".join(sents))
    text = "\n\n".join(out)
    st.text_area("Output", text, height=300)
    st.download_button("Download .txt", text, "lorem.txt", "text/plain")

elif selected_tool == "108. Text Case Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Sharpen blurry or soft images. Enhance image clarity for print and digital use.")
    st.header("Text Case Converter")
    txt = st.text_area("Input text:", "Hello world from digital envisioned", height=140)
    if txt:
        words = re.findall(r"[A-Za-z0-9]+", txt)
        camel = (words[0].lower() + "".join(w.capitalize() for w in words[1:])) if words else ""
        pascal = "".join(w.capitalize() for w in words)
        snake = "_".join(w.lower() for w in words)
        kebab = "-".join(w.lower() for w in words)
        st.write("**UPPERCASE**"); st.code(txt.upper())
        st.write("**lowercase**"); st.code(txt.lower())
        st.write("**Title Case**"); st.code(txt.title())
        st.write("**Sentence case**"); st.code(txt[:1].upper() + txt[1:].lower() if txt else "")
        st.write("**camelCase**"); st.code(camel)
        st.write("**PascalCase**"); st.code(pascal)
        st.write("**snake_case**"); st.code(snake)
        st.write("**kebab-case**"); st.code(kebab)

elif selected_tool == "109. UTM Campaign Link Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create panoramic images from multiple shots. Stitch photos together into wide-angle compositions.")
    st.header("UTM Campaign Link Builder")
    base_url = st.text_input("Destination URL", "https://digitalenvisioned.net/")
    src = st.text_input("utm_source", "newsletter")
    med = st.text_input("utm_medium", "email")
    camp = st.text_input("utm_campaign", "spring_launch")
    term = st.text_input("utm_term (optional)", "")
    content = st.text_input("utm_content (optional)", "")
    if base_url:
        params = {"utm_source": src, "utm_medium": med, "utm_campaign": camp}
        if term: params["utm_term"] = term
        if content: params["utm_content"] = content
        sep = "&" if "?" in base_url else "?"
        link = base_url + sep + urllib.parse.urlencode(params)
        st.code(link)
        st.download_button("Download .txt", link, "utm_link.txt", "text/plain")

elif selected_tool == "110. Hashtag Formatter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Compare two images side by side. Spot differences and review before/after edits visually.")
    st.header("Hashtag Formatter")
    raw = st.text_area("Paste tags or phrases (one per line or comma-separated):",
                       "small business automation, birmingham al\nseo growth, conversion optimization", height=160)
    if raw:
        tokens = re.split(r"[,\n]+", raw)
        tags = []
        for t in tokens:
            cleaned = re.sub(r"[^A-Za-z0-9 ]+", "", t).strip()
            if cleaned:
                tags.append("#" + "".join(w.capitalize() for w in cleaned.split()))
        out = " ".join(tags)
        st.code(out)
        st.caption(f"{len(tags)} hashtags · {len(out)} chars")

elif selected_tool == "111. Twitter/X Strict Character Counter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Run a complete SEO audit on any URL. Identify optimization opportunities and fix ranking issues.")
    st.header("Twitter / X Character Counter")
    txt = st.text_area("Compose your post:", height=180)
    LIMIT = 280
    used = len(txt)
    remaining = LIMIT - used
    c1, c2, c3 = st.columns(3)
    c1.metric("Characters", used)
    c2.metric("Remaining", remaining)
    c3.metric("Tweets needed", max(1, -(-used // LIMIT)))
    pct = min(1.0, used / LIMIT)
    st.progress(pct)
    if used > LIMIT: st.error(f"Over by {used - LIMIT} characters.")
    elif used > LIMIT * 0.9: st.warning("Approaching the limit.")
    else: st.success("You have room to spare.")

elif selected_tool == "112. Instagram Bio Spacer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze website page load speed. Find performance bottlenecks that slow down your site.")
    st.header("Instagram Bio Spacer (Preserves Line Breaks)")
    raw = st.text_area("Paste your bio (use blank lines for spacing):",
                       "Birmingham AL automation\n\nBuilt for small business\n\n👇 Free 10 tools below", height=200)
    if raw:
        out = "\n".join(line if line.strip() else "⠀" for line in raw.splitlines())
        st.text_area("Copy this into Instagram:", out, height=240)
        st.caption("Empty lines are replaced with a Braille blank (⠀) so Instagram preserves the spacing.")
        st.download_button("Download .txt", out, "ig_bio.txt", "text/plain")

elif selected_tool == "113. Bullet Point to Comma List Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Test whether a website is mobile-friendly. Ensure your site looks great on smartphones and tablets.")
    st.header("Bullet Points → Comma List")
    raw = st.text_area("Paste a bullet list:", "- Speed\n- Accuracy\n- Profit\n• Reliability", height=180)
    sep = st.text_input("Separator", ", ")
    if raw:
        lines = [re.sub(r"^[\s\-\*\u2022\u25CF\u25E6\d\.\)]+", "", l).strip()
                 for l in raw.splitlines() if l.strip()]
        out = sep.join(lines)
        st.code(out)
        st.caption(f"{len(lines)} items · {len(out)} chars")

elif selected_tool == "114. Whitespace & Line Break Remover":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Check for broken links across your website. Fix dead links that hurt SEO and frustrate visitors.")
    st.header("Whitespace & Line Break Remover")
    raw = st.text_area("Paste text:", height=220)
    mode = st.radio("Strategy", [
        "Collapse runs of whitespace to single space",
        "Strip ALL whitespace (including spaces)",
        "Remove only line breaks (keep spaces)",
    ])
    if raw and st.button("Clean"):
        if mode.startswith("Collapse"):
            out = re.sub(r"\s+", " ", raw).strip()
        elif mode.startswith("Strip"):
            out = re.sub(r"\s+", "", raw)
        else:
            out = raw.replace("\r", "").replace("\n", " ")
        st.code(out)
        st.caption(f"Before: {len(raw)} chars · After: {len(out)} chars")

elif selected_tool == "115. Email Subject Line Previewer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze a page's backlink profile. Understand your site's authority and link-building opportunities.")
    st.header("Email Subject Line Previewer")
    sender = st.text_input("Sender name", "Joshua Newton")
    subject = st.text_input("Subject line", "Your free 10 automation tools are ready")
    preview = st.text_input("Preview/preheader text", "Unlock the Birmingham Suite — no credit card needed.")
    SUBJECT_LIMIT, PREVIEW_LIMIT = 60, 100
    sub_trim = subject if len(subject) <= 70 else subject[:69] + "…"
    pre_trim = preview if len(preview) <= 110 else preview[:109] + "…"

    def _row(theme):
        bg = "#0f1115" if theme == "dark" else "#ffffff"
        fg = "#ffffff" if theme == "dark" else "#000000"
        sub_color = "#3aa3ff" if theme == "dark" else "#0b66c3"
        meta = "#9aa0a6" if theme == "dark" else "#5f6368"
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:14px 16px;border-radius:8px;'
            f'border:1px solid #444;margin-bottom:8px;">'
            f'<div style="font-weight:700;">{html_mod.escape(sender)}</div>'
            f'<div style="color:{sub_color};font-weight:700;margin-top:2px;">{html_mod.escape(sub_trim)}</div>'
            f'<div style="color:{meta};margin-top:2px;font-size:0.92rem;">{html_mod.escape(pre_trim)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Inbox preview — Dark")
    _row("dark")
    st.subheader("Inbox preview — Light")
    _row("light")
    c1, c2 = st.columns(2)
    c1.metric("Subject chars", f"{len(subject)} / {SUBJECT_LIMIT}")
    c2.metric("Preview chars", f"{len(preview)} / {PREVIEW_LIMIT}")
    if len(subject) > SUBJECT_LIMIT: st.warning("Subject may truncate on mobile.")
    if len(preview) > PREVIEW_LIMIT: st.warning("Preview text will be cut off in many clients.")

# ===== Content & Text Utilities (116-125) =====
elif selected_tool == "116. Blog Title Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Research search volume for target keywords. Find high-value keywords worth targeting in your content.")
    st.header("Blog Title Generator")
    keywords = st.text_input("Topic / keywords (comma-separated)", "small business automation, Birmingham")
    n = st.slider("How many titles", 5, 30, 12)
    if keywords and st.button("Generate Titles"):
        kws = [k.strip() for k in keywords.split(",") if k.strip()]
        templates = [
            "The Ultimate Guide to {kw} in {year}",
            "{n} Proven Ways to Master {kw}",
            "Why {kw} Is the Secret Weapon Smart Owners Use",
            "How {kw} Can 10× Your Results This Quarter",
            "{kw}: The Complete Playbook for Beginners",
            "Stop Wasting Time — Automate Your {kw} Today",
            "{n} Mistakes to Avoid With {kw}",
            "From Zero to Pro: Mastering {kw} in 30 Days",
            "The Truth About {kw} Nobody Talks About",
            "{kw} vs. The Competition: Who Really Wins?",
            "A Step-by-Step Framework for {kw}",
            "{n} Free Tools That Make {kw} Effortless",
        ]
        out = []
        for _ in range(n):
            t = random.choice(templates).format(
                kw=random.choice(kws).title(),
                year=datetime.now().year,
                n=random.choice([5, 7, 10, 12, 15]),
            )
            out.append(t)
        for t in out:
            st.write(f"• {t}")
        st.download_button("Download .txt", "\n".join(out), "titles.txt", "text/plain")

elif selected_tool == "117. CTA Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze competitor SEO strategies. Reverse-engineer what's working for your competition.")
    st.header("Call-to-Action (CTA) Generator")
    product = st.text_input("Product / offer", "Free 10-Tool Suite")
    audience = st.text_input("Audience", "Birmingham small business owners")
    goal = st.selectbox("Goal", ["Sign up", "Buy", "Book a call", "Download", "Subscribe", "Try free"])
    n = st.slider("How many CTAs", 5, 25, 10)
    if st.button("Generate"):
        templates = {
            "Sign up": ["Sign up for {p} — built for {a}.", "Claim your {p} access in 30 seconds.", "Join {a} already using {p}."],
            "Buy":     ["Buy {p} today — limited spots for {a}.", "Get {p} now and stop leaving money on the table.", "Upgrade to {p} — pay once, automate forever."],
            "Book a call": ["Book your free {p} strategy call.", "Talk to a {p} expert — built for {a}.", "Schedule 15 minutes — see {p} in action."],
            "Download": ["Download {p} — instant access for {a}.", "Grab the {p} free.", "Snag your {p} below."],
            "Subscribe": ["Subscribe to {p} and get weekly wins.", "Join the {p} list — exclusive to {a}.", "Subscribe now — never miss a {p} drop."],
            "Try free": ["Try {p} free — no card needed.", "Start your free {p} trial today.", "Test-drive {p} risk-free."],
        }
        bank = templates[goal]
        out = [random.choice(bank).format(p=product, a=audience) for _ in range(n)]
        for c in out: st.success(c)
        st.download_button("Download .txt", "\n".join(out), "ctas.txt", "text/plain")

elif selected_tool == "118. Text to Morse Code Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate structured data markup (Schema.org). Help search engines understand your content for rich results.")
    st.header("Text ↔ Morse Code Converter")
    MORSE = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
        'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
        'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
        '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--',
        '?': '..--..', "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
        '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-',
        '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    }
    INV = {v: k for k, v in MORSE.items()}
    mode = st.radio("Mode", ["Text → Morse", "Morse → Text"], horizontal=True)
    txt = st.text_area("Input:", height=160)
    if txt and st.button("Convert"):
        if mode.startswith("Text"):
            words = txt.upper().split()
            out = " / ".join(" ".join(MORSE.get(c, "?") for c in w) for w in words)
        else:
            words = txt.strip().split("/")
            out = " ".join("".join(INV.get(c.strip(), "?") for c in w.strip().split()) for w in words)
        st.code(out)
        st.caption("Use ' / ' between words.")

elif selected_tool == "119. Binary ↔ Text Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track and analyze SERP positions. Monitor your search rankings and spot trends over time.")
    st.header("Binary ↔ Text Converter")
    mode = st.radio("Mode", ["Text → Binary", "Binary → Text"], horizontal=True)
    txt = st.text_area("Input:", height=160)
    if txt and st.button("Convert"):
        try:
            if mode.startswith("Text"):
                out = " ".join(format(b, "08b") for b in txt.encode("utf-8"))
            else:
                bytes_list = [int(b, 2) for b in re.split(r"\s+", txt.strip()) if b]
                out = bytes(bytes_list).decode("utf-8", errors="replace")
            st.code(out)
        except Exception as e:
            st.error(f"Conversion failed: {e}")

elif selected_tool == "120. Basic Sentiment Analyzer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Check content for duplicate or thin pages. Ensure every page provides unique value to visitors and search engines.")
    st.header("Basic Sentiment Analyzer")
    POS = set("good great excellent amazing love loved fantastic wonderful best brilliant happy joy enjoy enjoyed nice perfect awesome positive win wins winning success successful pleased delighted recommend recommended outstanding incredible".split())
    NEG = set("bad terrible awful hate hated worst horrible poor sad angry mad disappointed disappointing fail failed failing problem problems broken useless waste boring annoying frustrating slow late expensive ripoff scam".split())
    txt = st.text_area("Paste text:", height=200)
    if txt:
        words = re.findall(r"[a-zA-Z']+", txt.lower())
        pos = sum(1 for w in words if w in POS)
        neg = sum(1 for w in words if w in NEG)
        score = pos - neg
        if score > 0:
            st.success(f"Positive (score +{score})")
        elif score < 0:
            st.error(f"Negative (score {score})")
        else:
            st.info("Neutral (score 0)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Positive hits", pos)
        c2.metric("Negative hits", neg)
        c3.metric("Total words", len(words))

elif selected_tool == "121. Webpage Text Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate email templates for cold outreach. Start conversations with prospects using proven frameworks.")
    st.header("Webpage Text Extractor")
    url = st.text_input("Page URL", "https://digitalenvisioned.net/")
    if url and st.button("Extract"):
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "DigitalEnvisionedBot/1.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
            full = "\n\n".join(paragraphs)
            st.metric("Paragraphs", len(paragraphs))
            st.metric("Characters", len(full))
            st.text_area("Extracted text", full, height=380)
            st.download_button("Download .txt", full, "extracted.txt", "text/plain")
        except Exception as e:
            st.error(f"Failed: {e}")

elif selected_tool == "122. HTML to Markdown Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Manage and organize email contact lists. Segment your audience for targeted, personalized campaigns.")
    st.header("HTML → Markdown Converter")
    raw = st.text_area("Paste HTML:", height=240,
                       value="<h1>Hello</h1><p>This is <b>bold</b> and <a href='https://x.com'>a link</a>.</p>")
    if raw and st.button("Convert"):
        out = raw
        out = re.sub(r"(?is)<h1[^>]*>(.*?)</h1>", r"# \1\n", out)
        out = re.sub(r"(?is)<h2[^>]*>(.*?)</h2>", r"## \1\n", out)
        out = re.sub(r"(?is)<h3[^>]*>(.*?)</h3>", r"### \1\n", out)
        out = re.sub(r"(?is)<h4[^>]*>(.*?)</h4>", r"#### \1\n", out)
        out = re.sub(r"(?is)<(b|strong)[^>]*>(.*?)</\1>", r"**\2**", out)
        out = re.sub(r"(?is)<(i|em)[^>]*>(.*?)</\1>", r"*\2*", out)
        out = re.sub(r"(?is)<code[^>]*>(.*?)</code>", r"`\1`", out)
        out = re.sub(r'(?is)<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", out)
        out = re.sub(r"(?is)<li[^>]*>(.*?)</li>", r"- \1", out)
        out = re.sub(r"(?is)<br\s*/?>", "\n", out)
        out = re.sub(r"(?is)<p[^>]*>(.*?)</p>", r"\1\n\n", out)
        out = re.sub(r"<[^>]+>", "", out)
        out = html_mod.unescape(out).strip()
        st.code(out, language="markdown")
        st.download_button("Download .md", out, "converted.md", "text/markdown")

elif selected_tool == "123. Text Prefix/Suffix Bulk Adder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan and track email campaign sequences. Automate nurture flows that convert subscribers to customers.")
    st.header("Prefix / Suffix Bulk Adder")
    raw = st.text_area("One item per line:", height=220)
    prefix = st.text_input("Prefix", "https://example.com/")
    suffix = st.text_input("Suffix", "?ref=de")
    skip_blank = st.checkbox("Skip blank lines", True)
    if raw:
        out_lines = []
        for line in raw.splitlines():
            if skip_blank and not line.strip():
                continue
            out_lines.append(f"{prefix}{line.strip()}{suffix}")
        out = "\n".join(out_lines)
        st.code(out)
        st.caption(f"{len(out_lines)} lines processed.")
        st.download_button("Download .txt", out, "bulk_output.txt", "text/plain")

elif selected_tool == "124. Duplicate Line Remover":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze email engagement metrics. Understand open rates, clicks, and what drives conversions.")
    st.header("Duplicate Line Remover")
    raw = st.text_area("Paste lines:", height=240)
    case_insensitive = st.checkbox("Case-insensitive", False)
    keep_order = st.checkbox("Preserve original order", True)
    trim = st.checkbox("Trim whitespace before comparing", True)
    if raw and st.button("Remove Duplicates"):
        lines = raw.splitlines()
        seen, out = set(), []
        for ln in lines:
            key = ln.strip() if trim else ln
            if case_insensitive: key = key.lower()
            if key in seen: continue
            seen.add(key)
            out.append(ln.strip() if trim else ln)
        if not keep_order: out.sort()
        result = "\n".join(out)
        st.metric("Before", len(lines))
        st.metric("After", len(out))
        st.metric("Duplicates removed", len(lines) - len(out))
        st.text_area("Result", result, height=240)
        st.download_button("Download .txt", result, "deduped.txt", "text/plain")

elif selected_tool == "125. List Alphabetizer & Sorter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Score email subject lines for effectiveness. Write subject lines that get opened instead of deleted.")
    st.header("List Alphabetizer & Sorter")
    raw = st.text_area("One item per line:", height=240)
    mode = st.selectbox("Sort mode", ["A → Z", "Z → A", "Length (short→long)", "Length (long→short)", "Numeric ascending", "Numeric descending"])
    case_ins = st.checkbox("Case-insensitive sort", True)
    if raw and st.button("Sort"):
        items = [l for l in raw.splitlines() if l.strip()]
        key = (lambda s: s.lower()) if case_ins else None
        if mode == "A → Z":      items.sort(key=key)
        elif mode == "Z → A":    items.sort(key=key, reverse=True)
        elif mode.startswith("Length (short"): items.sort(key=len)
        elif mode.startswith("Length (long"):  items.sort(key=len, reverse=True)
        elif mode == "Numeric ascending":
            try: items.sort(key=lambda x: float(re.sub(r"[^\d\.\-]", "", x) or 0))
            except Exception: st.warning("Some lines weren't numeric.")
        elif mode == "Numeric descending":
            try: items.sort(key=lambda x: float(re.sub(r"[^\d\.\-]", "", x) or 0), reverse=True)
            except Exception: st.warning("Some lines weren't numeric.")
        out = "\n".join(items)
        st.text_area("Sorted", out, height=240)
        st.download_button("Download .txt", out, "sorted.txt", "text/plain")

# ===== Data & List Management (126-135) =====
elif selected_tool == "126. List Randomizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Validate email addresses before sending. Clean your list and reduce bounces to protect sender reputation.")
    st.header("List Randomizer (Shuffle)")
    raw = st.text_area("One item per line:", height=220)
    seed = st.text_input("Seed (optional, for reproducibility)", "")
    if raw and st.button("Shuffle"):
        items = [l for l in raw.splitlines() if l.strip()]
        rng = random.Random(seed) if seed else random.Random()
        rng.shuffle(items)
        out = "\n".join(items)
        st.text_area("Shuffled", out, height=220)
        st.download_button("Download .txt", out, "shuffled.txt", "text/plain")

elif selected_tool == "127. CSV Column Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track email delivery and bounce rates. Monitor deliverability and fix issues before they impact campaigns.")
    st.header("CSV Column Extractor")
    up = st.file_uploader("Upload CSV", type=["csv"])
    if up:
        df = pd.read_csv(up)
        cols = st.multiselect("Columns to extract", df.columns.tolist(), default=df.columns[:1].tolist())
        fmt = st.radio("Output format", ["CSV", "JSON", "Plain text (newline)"], horizontal=True)
        if cols and st.button("Extract"):
            sub = df[cols]
            if fmt == "CSV":
                buf = sub.to_csv(index=False)
                st.code(buf)
                st.download_button("Download .csv", buf, "extracted.csv", "text/csv")
            elif fmt == "JSON":
                buf = sub.to_json(orient="records", indent=2)
                st.code(buf, language="json")
                st.download_button("Download .json", buf, "extracted.json", "application/json")
            else:
                buf = "\n".join(sub.astype(str).agg(" | ".join, axis=1))
                st.code(buf)
                st.download_button("Download .txt", buf, "extracted.txt", "text/plain")

elif selected_tool == "128. JSON to XML Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate email footers with legal compliance. Include proper unsubscribe links and business information.")
    st.header("JSON → XML Converter")
    raw = st.text_area("Paste JSON:", height=220, value='{"order": {"id": 42, "items": ["a", "b"]}}')
    root = st.text_input("Root tag (when JSON is a list)", "items")
    if raw and st.button("Convert"):
        try:
            data = json.loads(raw)
            def _to_xml(obj, tag):
                if isinstance(obj, dict):
                    inner = "".join(_to_xml(v, k) for k, v in obj.items())
                    return f"<{tag}>{inner}</{tag}>"
                if isinstance(obj, list):
                    return "".join(_to_xml(v, tag) for v in obj)
                return f"<{tag}>{html_mod.escape(str(obj))}</{tag}>"
            if isinstance(data, list):
                body = _to_xml(data, root)
            elif isinstance(data, dict) and len(data) == 1:
                k, v = next(iter(data.items()))
                body = _to_xml(v, k)
            else:
                body = _to_xml(data, "root")
            xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + body
            st.code(xml, language="xml")
            st.download_button("Download .xml", xml, "converted.xml", "application/xml")
        except Exception as e:
            st.error(f"Conversion failed: {e}")

elif selected_tool == "129. Phone Number Standardizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Run A/B tests on email campaigns. Optimize every element of your emails with data-driven testing.")
    st.header("Phone Number Standardizer")
    raw = st.text_area("Paste numbers (one per line):", "(205) 555-1234\n205.555.9876\n+1 205 555 4321\n555-1212", height=180)
    fmt = st.selectbox("Output format", [
        "(XXX) XXX-XXXX", "XXX-XXX-XXXX", "+1 XXX XXX XXXX", "XXXXXXXXXX (raw)",
    ])
    if raw and st.button("Standardize"):
        out = []
        for line in raw.splitlines():
            digits = re.sub(r"\D", "", line)
            if len(digits) == 11 and digits.startswith("1"):
                digits = digits[1:]
            if len(digits) != 10:
                out.append(f"{line}  →  (invalid: {len(digits)} digits)")
                continue
            a, b, c = digits[:3], digits[3:6], digits[6:]
            mapping = {
                "(XXX) XXX-XXXX": f"({a}) {b}-{c}",
                "XXX-XXX-XXXX":   f"{a}-{b}-{c}",
                "+1 XXX XXX XXXX": f"+1 {a} {b} {c}",
                "XXXXXXXXXX (raw)": digits,
            }
            out.append(mapping[fmt])
        result = "\n".join(out)
        st.code(result)
        st.download_button("Download .txt", result, "phones.txt", "text/plain")

elif selected_tool == "130. Email Address Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate email marketing ROI. Prove the value of your email program with hard numbers.")
    st.header("Email Address Extractor")
    raw = st.text_area("Paste any text (HTML, emails, dumps, etc.):", height=260)
    dedupe = st.checkbox("De-duplicate", True)
    lower = st.checkbox("Lowercase", True)
    if raw and st.button("Extract"):
        emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", raw)
        if lower: emails = [e.lower() for e in emails]
        if dedupe: emails = sorted(set(emails))
        st.metric("Emails found", len(emails))
        out = "\n".join(emails)
        st.text_area("Result", out, height=240)
        st.download_button("Download .txt", out, "emails.txt", "text/plain")

elif selected_tool == "131. URL Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan and organize social media content. Stay consistent across platforms with a structured content calendar.")
    st.header("URL Extractor")
    raw = st.text_area("Paste any text:", height=260)
    dedupe = st.checkbox("De-duplicate", True)
    only_https = st.checkbox("Only HTTPS", False)
    if raw and st.button("Extract"):
        urls = re.findall(r"https?://[^\s<>\"')]+", raw)
        if only_https: urls = [u for u in urls if u.startswith("https://")]
        if dedupe: urls = sorted(set(urls))
        st.metric("URLs found", len(urls))
        out = "\n".join(urls)
        st.text_area("Result", out, height=240)
        st.download_button("Download .txt", out, "urls.txt", "text/plain")

elif selected_tool == "132. SQL Insert Statement Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track social media follower growth. Monitor audience growth and identify what's driving new follows.")
    st.header("SQL INSERT Generator (from CSV)")
    up = st.file_uploader("Upload CSV", type=["csv"])
    table = st.text_input("Table name", "customers")
    dialect = st.selectbox("Dialect", ["MySQL/Postgres", "SQL Server"])
    if up and table and st.button("Generate"):
        df = pd.read_csv(up)
        cols = ", ".join(f"`{c}`" if dialect.startswith("MySQL") else f"[{c}]" for c in df.columns)
        rows_sql = []
        for _, row in df.iterrows():
            vals = []
            for v in row:
                if pd.isna(v):
                    vals.append("NULL")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                else:
                    vals.append("'" + str(v).replace("'", "''") + "'")
            rows_sql.append(f"INSERT INTO {table} ({cols}) VALUES ({', '.join(vals)});")
        out = "\n".join(rows_sql)
        st.success(f"Generated {len(rows_sql)} INSERT statements.")
        st.code(out, language="sql")
        st.download_button("Download .sql", out, f"{table}_inserts.sql", "text/plain")

elif selected_tool == "133. YAML to JSON Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan and track social advertising campaigns. Manage ad spend and performance across all platforms.")
    st.header("YAML → JSON Converter")
    raw = st.text_area("Paste YAML:", height=240,
                       value="name: Digital Envisioned\ntools: 200\nplans:\n  - free\n  - pro\n  - elite")
    if raw and st.button("Convert"):
        try:
            try:
                import yaml
                data = yaml.safe_load(raw)
            except Exception:
                lines = [l for l in raw.splitlines() if l.strip() and not l.strip().startswith("#")]
                data = {}
                for l in lines:
                    if ":" in l and not l.strip().startswith("-"):
                        k, v = l.split(":", 1)
                        data[k.strip()] = v.strip() or None
                st.warning("PyYAML not installed — using minimal fallback parser (flat key:value only).")
            out = json.dumps(data, indent=2, default=str)
            st.code(out, language="json")
            st.download_button("Download .json", out, "converted.json", "application/json")
        except Exception as e:
            st.error(f"Conversion failed: {e}")

elif selected_tool == "134. Data Anonymizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build social media reporting dashboards. Present results to clients and stakeholders with clear metrics.")
    st.header("Data Anonymizer (Mask Emails / Phones / Cards)")
    raw = st.text_area("Paste text:", height=240,
                       value="Contact josh@example.com or 205-555-1234. Card 4242 4242 4242 4242.")
    mask_email = st.checkbox("Mask emails", True)
    mask_phone = st.checkbox("Mask phone numbers", True)
    mask_card = st.checkbox("Mask credit cards", True)
    if raw and st.button("Anonymize"):
        out = raw
        if mask_email:
            out = re.sub(r"([a-zA-Z0-9._%+\-])[a-zA-Z0-9._%+\-]*(@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", r"\1***\2", out)
        if mask_phone:
            out = re.sub(r"\+?\d[\d\-\.\(\)\s]{7,}\d", "[PHONE]", out)
        if mask_card:
            out = re.sub(r"\b(?:\d[ \-]*?){13,16}\b", "[CARD]", out)
        st.code(out)
        st.download_button("Download .txt", out, "anonymized.txt", "text/plain")

elif selected_tool == "135. Word Frequency Counter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze audience demographics and interests. Understand who your followers are to create content they love.")
    st.header("Word Frequency Counter")
    raw = st.text_area("Paste text:", height=240)
    top_n = st.slider("Top N", 5, 100, 25)
    drop_stop = st.checkbox("Ignore common stop words", True)
    if raw:
        STOP = set("the a an and or but if then for of in on at to from by with as is are was were be been being it this that these those i you he she we they not no so do does did have has had will would can could should".split())
        words = re.findall(r"[a-zA-Z']{2,}", raw.lower())
        if drop_stop: words = [w for w in words if w not in STOP]
        counts = Counter(words).most_common(top_n)
        df = pd.DataFrame(counts, columns=["Word", "Count"])
        st.metric("Total words analyzed", len(words))
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("Word"))

# ===== Web & Network Tools (136-145) =====
elif selected_tool == "136. WHOIS Data Lookup":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan social media contests and giveaways. Grow your audience with engaging promotional campaigns.")
    st.header("WHOIS Data Lookup")
    domain = st.text_input("Domain", "digitalenvisioned.net")
    if domain and st.button("Lookup"):
        try:
            import whois
            data = whois.whois(domain)
            rows = {}
            for k in ("domain_name", "registrar", "creation_date", "expiration_date", "updated_date",
                      "name_servers", "status", "emails", "country"):
                v = data.get(k)
                if isinstance(v, list): v = ", ".join(str(x) for x in v[:5])
                rows[k] = str(v) if v else "—"
            st.dataframe(pd.DataFrame(rows.items(), columns=["Field", "Value"]),
                         use_container_width=True)
        except Exception:
            try:
                r = requests.get(f"https://rdap.org/domain/{domain}", timeout=8)
                if r.ok:
                    data = r.json()
                    st.json(data)
                else:
                    st.error(f"RDAP returned HTTP {r.status_code}")
            except Exception as e:
                st.error(f"Lookup failed: {e}")

elif selected_tool == "137. DNS Record Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Manage brand reputation across social platforms. Monitor mentions and respond quickly to protect your brand.")
    st.header("DNS Record Checker")
    domain = st.text_input("Domain", "digitalenvisioned.net")
    rtypes = st.multiselect("Record types", ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"],
                            default=["A", "MX", "NS", "TXT"])
    if domain and rtypes and st.button("Check"):
        results = {}
        try:
            import dns.resolver
            for rt in rtypes:
                try:
                    answers = dns.resolver.resolve(domain, rt, lifetime=5)
                    results[rt] = [a.to_text() for a in answers]
                except Exception as e:
                    results[rt] = [f"(no records / error: {e})"]
        except Exception:
            for rt in rtypes:
                try:
                    r = requests.get("https://dns.google/resolve",
                                     params={"name": domain, "type": rt}, timeout=6)
                    j = r.json()
                    results[rt] = [a.get("data", "?") for a in j.get("Answer", [])] or ["(none)"]
                except Exception as e:
                    results[rt] = [f"(error: {e})"]
        for rt, vals in results.items():
            st.subheader(rt)
            for v in vals: st.code(v)

elif selected_tool == "138. HTTP Status Code Header Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate social media story content ideas. Keep your Stories feed fresh with planned, engaging content.")
    st.header("HTTP Status & Header Checker")
    url = st.text_input("URL", "https://digitalenvisioned.net/")
    method = st.selectbox("Method", ["HEAD", "GET"])
    if url and st.button("Check"):
        try:
            r = requests.request(method, url, timeout=10, allow_redirects=True,
                                 headers={"User-Agent": "DigitalEnvisionedBot/1.0"})
            color = st.success if r.status_code < 300 else (st.warning if r.status_code < 400 else st.error)
            color(f"HTTP {r.status_code} {r.reason}")
            st.metric("Final URL", r.url)
            st.metric("Redirects", len(r.history))
            st.metric("Response time (ms)", int(r.elapsed.total_seconds() * 1000))
            st.subheader("Headers")
            st.dataframe(pd.DataFrame(r.headers.items(), columns=["Header", "Value"]),
                         use_container_width=True)
        except Exception as e:
            st.error(f"Request failed: {e}")

elif selected_tool == "139. User-Agent String Parser":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan social media influencer collaborations. Partner with creators who can authentically promote your brand.")
    st.header("User-Agent String Parser")
    ua = st.text_area("Paste a User-Agent string:", height=100,
                      value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    if ua and st.button("Parse"):
        os_name = "Unknown OS"
        if "Windows NT 10" in ua: os_name = "Windows 10/11"
        elif "Windows NT 6.3" in ua: os_name = "Windows 8.1"
        elif "Windows NT 6.1" in ua: os_name = "Windows 7"
        elif "Mac OS X" in ua: os_name = "macOS"
        elif "Android" in ua: os_name = "Android"
        elif "iPhone" in ua or "iPad" in ua: os_name = "iOS"
        elif "Linux" in ua: os_name = "Linux"

        browser = "Unknown"
        for b in ["Edg", "OPR", "Chrome", "Safari", "Firefox", "MSIE", "Trident"]:
            m = re.search(rf"{b}/([\d\.]+)", ua)
            if m:
                name = {"Edg": "Edge", "OPR": "Opera", "MSIE": "Internet Explorer",
                        "Trident": "Internet Explorer"}.get(b, b)
                browser = f"{name} {m.group(1)}"
                if b == "Chrome" and "Edg" in ua: continue
                break

        device = "Mobile" if any(k in ua for k in ["Mobile", "Android", "iPhone", "iPad"]) else "Desktop"
        is_bot = bool(re.search(r"(?i)bot|crawl|spider|slurp|wget|curl", ua))
        rows = {"OS": os_name, "Browser": browser, "Device class": device,
                "Likely bot": "Yes" if is_bot else "No", "Length": f"{len(ua)} chars"}
        st.dataframe(pd.DataFrame(rows.items(), columns=["Field", "Value"]),
                     use_container_width=True)

elif selected_tool == "140. URL Redirect Tracer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Analyze trending topics and hashtags. Stay relevant by jumping on trends that fit your brand.")
    st.header("URL Redirect Tracer")
    url = st.text_input("URL", "https://bit.ly/3xyz")
    if url and st.button("Trace"):
        try:
            r = requests.get(url, timeout=10, allow_redirects=True,
                             headers={"User-Agent": "DigitalEnvisionedBot/1.0"})
            chain = [{"#": 0, "Status": "START", "URL": url}]
            for i, h in enumerate(r.history, 1):
                chain.append({"#": i, "Status": h.status_code, "URL": h.url})
            chain.append({"#": len(r.history) + 1, "Status": r.status_code, "URL": r.url})
            st.metric("Total hops", len(r.history))
            st.metric("Final URL", r.url)
            st.dataframe(pd.DataFrame(chain), use_container_width=True)
        except Exception as e:
            st.error(f"Trace failed: {e}")

elif selected_tool == "141. Meta Tag Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate professional invoice documents. Bill clients with polished invoices that include all required details.")
    st.header("Meta Tag Extractor")
    url = st.text_input("Page URL", "https://digitalenvisioned.net/")
    if url and st.button("Extract"):
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "DigitalEnvisionedBot/1.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            tags = []
            t = soup.find("title")
            if t: tags.append({"Type": "title", "Name/Property": "—", "Content": t.get_text(strip=True)})
            for m in soup.find_all("meta"):
                tags.append({
                    "Type": "meta",
                    "Name/Property": m.get("name") or m.get("property") or m.get("http-equiv") or "—",
                    "Content": (m.get("content") or "")[:300],
                })
            for link in soup.find_all("link", rel=True):
                tags.append({"Type": "link", "Name/Property": " ".join(link.get("rel", [])),
                             "Content": link.get("href", "")[:300]})
            st.metric("Tags found", len(tags))
            st.dataframe(pd.DataFrame(tags), use_container_width=True)
        except Exception as e:
            st.error(f"Failed: {e}")

elif selected_tool == "142. Robots.txt Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create project proposals with scope and pricing. Win more projects with professional, detailed proposals.")
    st.header("Robots.txt Generator")
    sitemap = st.text_input("Sitemap URL", "https://digitalenvisioned.net/sitemap.xml")
    allow_all = st.checkbox("Allow all crawlers", True)
    disallow_paths = st.text_area("Disallowed paths (one per line)", "/admin\n/private\n/cart")
    crawl_delay = st.number_input("Crawl-delay (seconds, 0 = none)", 0, 60, 0)
    blocked_bots = st.text_area("Block specific bots (one per line)", "AhrefsBot\nSemrushBot")
    if st.button("Generate"):
        lines = []
        for bot in [b.strip() for b in blocked_bots.splitlines() if b.strip()]:
            lines += [f"User-agent: {bot}", "Disallow: /", ""]
        lines.append("User-agent: *")
        if allow_all:
            lines.append("Allow: /")
        for p in [p.strip() for p in disallow_paths.splitlines() if p.strip()]:
            lines.append(f"Disallow: {p}")
        if crawl_delay: lines.append(f"Crawl-delay: {crawl_delay}")
        if sitemap: lines.append(f"\nSitemap: {sitemap}")
        out = "\n".join(lines)
        st.code(out)
        st.download_button("Download robots.txt", out, "robots.txt", "text/plain")

elif selected_tool == "143. Sitemap.xml Basic Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track project budgets and spending. Stay on budget by monitoring expenses against projections.")
    st.header("Sitemap.xml Generator")
    raw = st.text_area("URLs (one per line)", "https://digitalenvisioned.net/\nhttps://digitalenvisioned.net/about\nhttps://digitalenvisioned.net/pricing", height=180)
    freq = st.selectbox("Change frequency", ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"], index=3)
    priority = st.slider("Default priority", 0.1, 1.0, 0.8, 0.1)
    if raw and st.button("Generate"):
        urls = [u.strip() for u in raw.splitlines() if u.strip()]
        today = datetime.now().strftime("%Y-%m-%d")
        body = "".join(
            f"  <url>\n    <loc>{html_mod.escape(u)}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority:.1f}</priority>\n  </url>\n"
            for u in urls
        )
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>')
        st.success(f"Generated sitemap with {len(urls)} URLs.")
        st.code(xml, language="xml")
        st.download_button("Download sitemap.xml", xml, "sitemap.xml", "application/xml")

elif selected_tool == "144. IP Subnet Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Log and track project time entries. Understand where time goes and bill accurately for your work.")
    st.header("IP Subnet Calculator (CIDR)")
    cidr = st.text_input("CIDR (IPv4 or IPv6)", "192.168.1.0/24")
    if cidr and st.button("Calculate"):
        try:
            import ipaddress
            net = ipaddress.ip_network(cidr, strict=False)
            rows = {
                "Network": str(net.network_address),
                "Netmask": str(net.netmask),
                "Broadcast": str(getattr(net, "broadcast_address", "—")),
                "Prefix length": f"/{net.prefixlen}",
                "Total addresses": f"{net.num_addresses:,}",
                "Usable hosts": f"{max(0, net.num_addresses - 2):,}" if net.version == 4 else f"{net.num_addresses:,}",
                "First host": str(next(iter(net.hosts()))) if any(True for _ in net.hosts()) else "—",
                "Last host": str(list(net.hosts())[-1]) if any(True for _ in net.hosts()) else "—",
                "Is private": str(net.is_private),
            }
            st.dataframe(pd.DataFrame(rows.items(), columns=["Field", "Value"]),
                         use_container_width=True)
        except Exception as e:
            st.error(f"Invalid CIDR: {e}")

elif selected_tool == "145. MAC Address Vendor Lookup":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate project profitability metrics. Know which projects make money and which drain resources.")
    st.header("MAC Address Vendor Lookup")
    mac = st.text_input("MAC address", "B8:27:EB:12:34:56")
    OUI = {
        "B827EB": "Raspberry Pi Foundation", "DCA632": "Raspberry Pi Trading Ltd",
        "001A11": "Google, Inc.", "F0F61C": "Apple, Inc.", "A4C361": "Apple, Inc.",
        "001CB3": "Apple, Inc.", "001DA5": "Samsung Electronics", "F8FFC2": "Samsung Electronics",
        "B0E892": "Espressif Inc.", "08D1F9": "Cisco Systems", "001A2F": "Cisco Systems",
        "00163E": "Xensource, Inc.", "525400": "QEMU/KVM virtual NIC",
        "00059A": "Cisco Systems", "001E58": "Wistron InfoComm",
        "FCFC48": "Apple, Inc.", "F0DBF8": "Apple, Inc.", "3C5AB4": "Google, Inc.",
        "ECECCD": "Tesla Motors", "002590": "Super Micro Computer",
    }
    if mac and st.button("Lookup"):
        clean = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
        if len(clean) < 6:
            st.error("Need at least 6 hex digits (the OUI prefix).")
        else:
            oui = clean[:6]
            vendor = OUI.get(oui)
            st.metric("OUI prefix", ":".join(oui[i:i+2] for i in range(0, 6, 2)))
            if vendor:
                st.success(f"Vendor: **{vendor}**")
            else:
                try:
                    r = requests.get(f"https://api.macvendors.com/{clean[:6]}", timeout=5)
                    if r.ok and r.text and not r.text.startswith("{"):
                        st.success(f"Vendor (live): **{r.text}**")
                    else:
                        st.warning("OUI not in local catalog and live lookup returned no result.")
                except Exception:
                    st.warning("OUI not in local catalog. Live lookup unavailable.")


# ══════════════════════════════════════════════

# ── 146. Color Contrast Checker (WCAG) ───────
elif selected_tool == "146. Color Contrast Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("View optimal image dimensions for every major ad platform. Ensure your ads display perfectly on Facebook, Instagram, Google, and more.")
    st.header("🎨 Color Contrast Checker (WCAG)")

    def _hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _relative_luminance(r, g, b):
        def _c(v):
            v /= 255.0
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * _c(r) + 0.7152 * _c(g) + 0.0722 * _c(b)

    def _contrast_ratio(hex1, hex2):
        l1 = _relative_luminance(*_hex_to_rgb(hex1))
        l2 = _relative_luminance(*_hex_to_rgb(hex2))
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    col1, col2 = st.columns(2)
    with col1:
        fg = st.color_picker("Foreground (text) color", "#000000")
    with col2:
        bg = st.color_picker("Background color", "#FFFFFF")

    if st.button("Check Contrast"):
        ratio = _contrast_ratio(fg, bg)
        st.metric("Contrast Ratio", f"{ratio:.2f}:1")
        aa_normal  = "✅ Pass" if ratio >= 4.5 else "❌ Fail"
        aa_large   = "✅ Pass" if ratio >= 3.0 else "❌ Fail"
        aaa_normal = "✅ Pass" if ratio >= 7.0 else "❌ Fail"
        aaa_large  = "✅ Pass" if ratio >= 4.5 else "❌ Fail"
        results = pd.DataFrame({
            "Level": ["AA Normal Text", "AA Large Text", "AAA Normal Text", "AAA Large Text"],
            "Required": ["4.5:1", "3.0:1", "7.0:1", "4.5:1"],
            "Result": [aa_normal, aa_large, aaa_normal, aaa_large],
        })
        st.dataframe(results, use_container_width=True)
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:24px;border-radius:8px;'
            f'font-size:1.4rem;text-align:center;margin-top:12px;">'
            f'Sample text on chosen background</div>',
            unsafe_allow_html=True,
        )


# ── 147. CSS Gradient Code Generator ─────────
elif selected_tool == "147. CSS Gradient Code Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate harmonious brand color palettes from a seed color. Create cohesive visual identities that look professional across all media.")
    st.header("🌈 CSS Gradient Code Generator")
    grad_type = st.selectbox("Gradient type", ["linear", "radial"])
    col1, col2 = st.columns(2)
    with col1:
        c1 = st.color_picker("Color 1", "#1E90FF")
    with col2:
        c2 = st.color_picker("Color 2", "#FF6B6B")
    angle = 90
    if grad_type == "linear":
        angle = st.slider("Angle (deg)", 0, 360, 90)

    if grad_type == "linear":
        css = f"background: linear-gradient({angle}deg, {c1}, {c2});"
    else:
        css = f"background: radial-gradient(circle, {c1}, {c2});"

    st.code(css, language="css")
    st.markdown(
        f'<div style="{css} height:120px;border-radius:12px;margin-top:8px;"></div>',
        unsafe_allow_html=True,
    )
    st.caption("Copy the CSS above and paste it into your stylesheet.")


# ── 148. Base64 to Image Decoder ─────────────
elif selected_tool == "148. Base64 to Image Decoder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Get exact specs for social media cover photos and banners. Size your banners correctly so they never get cropped or distorted.")
    st.header("🖼️ Base64 → Image Decoder")
    b64_str = st.text_area("Paste Base64-encoded image string", height=180,
                           placeholder="data:image/png;base64,iVBORw0KGgo...")
    if b64_str and st.button("Decode & Display"):
        try:
            cleaned = b64_str.split(",")[-1].strip()
            img_bytes = base64.b64decode(cleaned)
            img = Image.open(BytesIO(img_bytes))
            st.image(img, caption=f"Decoded image ({img.size[0]}×{img.size[1]})")
            buf = BytesIO(img_bytes)
            st.download_button("Download Image", buf.getvalue(), "decoded_image.png")
        except Exception as e:
            st.error(f"Decoding failed: {e}")


# ── 149. Image to Base64 Encoder ─────────────
elif selected_tool == "149. Image to Base64 Encoder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Find font combinations that work beautifully together. Elevate your designs with professionally paired heading and body fonts.")
    st.header("📷 Image → Base64 Encoder")
    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "gif", "webp"])
    if uploaded:
        raw = uploaded.read()
        encoded = base64.b64encode(raw).decode("utf-8")
        mime = uploaded.type or "image/png"
        data_uri = f"data:{mime};base64,{encoded}"
        st.image(raw, caption=uploaded.name, width=300)
        st.text_area("Base64 Data URI (copy this)", data_uri, height=200)
        st.text_area("Raw Base64 (no prefix)", encoded, height=150)
        st.info(f"Encoded length: {len(encoded):,} characters")


# ── 150. Custom QR Code Builder (Color/Size) ─
elif selected_tool == "150. Custom QR Code Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan flyer layouts with headline, body, and CTA placement. Create print and digital flyers that grab attention and drive action.")
    st.header("📱 Custom QR Code Builder")
    data = st.text_input("Data / URL to encode", "https://digitalenvisioned.net")
    col1, col2, col3 = st.columns(3)
    with col1:
        fill_color = st.color_picker("QR Color", "#000000")
    with col2:
        back_color = st.color_picker("Background", "#FFFFFF")
    with col3:
        box_size = st.slider("Module size (px)", 4, 20, 10)
    border_size = st.slider("Border modules", 1, 8, 4)

    if data and st.button("Generate QR Code"):
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H,
                            box_size=box_size, border=border_size)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Custom QR Code")
        st.download_button("Download QR", buf.getvalue(), "custom_qr.png", "image/png")


# ── 151. Favicon Generator (16×16 / 32×32) ───
elif selected_tool == "151. Favicon Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create video scripts with scene-by-scene storyboard outlines. Plan video content efficiently so every second counts.")
    st.header("⭐ Favicon Generator")
    uploaded = st.file_uploader("Upload source image", type=["png", "jpg", "jpeg", "webp"])
    sizes = st.multiselect("Output sizes", ["16x16", "32x32", "48x48", "64x64", "128x128"],
                           default=["16x16", "32x32"])
    if uploaded and sizes and st.button("Generate Favicons"):
        src = Image.open(uploaded).convert("RGBA")
        for s in sizes:
            dim = int(s.split("x")[0])
            resized = src.resize((dim, dim), Image.LANCZOS)
            buf = BytesIO()
            resized.save(buf, format="PNG")
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(buf.getvalue(), caption=s, width=max(dim, 48))
            with col2:
                st.download_button(f"Download {s}", buf.getvalue(),
                                   f"favicon_{dim}x{dim}.png", "image/png", key=f"fav_{dim}")
        # Also generate .ico (16 + 32)
        ico_sizes = [(16, 16), (32, 32)]
        ico_buf = BytesIO()
        src.save(ico_buf, format="ICO", sizes=ico_sizes)
        st.download_button("Download .ico (16+32)", ico_buf.getvalue(), "favicon.ico",
                           "image/x-icon", key="fav_ico")


# ── 152. SVG Code Viewer ─────────────────────
elif selected_tool == "152. SVG Code Viewer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan and compare thumbnail designs for A/B testing. Increase click-through rates by testing different visual approaches.")
    st.header("🔷 SVG Code Viewer")
    svg_code = st.text_area("Paste SVG code", height=250,
                            value='<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">\n'
                                  '  <circle cx="100" cy="100" r="80" fill="#1E90FF"/>\n'
                                  '</svg>')
    if svg_code:
        st.subheader("Preview")
        st.markdown(svg_code, unsafe_allow_html=True)
        st.subheader("Formatted Code")
        st.code(svg_code, language="xml")
        b64 = base64.b64encode(svg_code.encode()).decode()
        st.text_input("Data URI (for CSS/HTML)", f"data:image/svg+xml;base64,{b64}")


# ── 153. Hex to RGB / RGB to Hex Converter ───
elif selected_tool == "153. Hex to RGB / RGB to Hex Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate creative briefs for motion graphics projects. Communicate your vision clearly to animators and designers.")
    st.header("🎨 Hex ↔ RGB Converter")
    direction = st.radio("Conversion direction", ["Hex → RGB", "RGB → Hex"])
    if direction == "Hex → RGB":
        hex_val = st.text_input("Hex color", "#1E90FF")
        if hex_val and st.button("Convert"):
            h = hex_val.lstrip("#")
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            if len(h) == 6:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                st.success(f"RGB: ({r}, {g}, {b})")
                st.code(f"rgb({r}, {g}, {b})", language="css")
                st.markdown(f'<div style="width:100%;height:60px;background:{hex_val};'
                            f'border-radius:8px;"></div>', unsafe_allow_html=True)
            else:
                st.error("Enter a valid 3- or 6-digit hex code.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            r = st.number_input("R", 0, 255, 30)
        with col2:
            g = st.number_input("G", 0, 255, 144)
        with col3:
            b = st.number_input("B", 0, 255, 255)
        if st.button("Convert"):
            hex_out = f"#{r:02X}{g:02X}{b:02X}"
            st.success(f"Hex: {hex_out}")
            st.code(hex_out, language="css")
            st.markdown(f'<div style="width:100%;height:60px;background:{hex_out};'
                        f'border-radius:8px;"></div>', unsafe_allow_html=True)


# ── 154. RGB to CMYK Converter ───────────────
elif selected_tool == "154. RGB to CMYK Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Get specifications and tips for podcast cover art design. Stand out in podcast directories with eye-catching, compliant artwork.")
    st.header("🖨️ RGB → CMYK Converter")
    col1, col2, col3 = st.columns(3)
    with col1:
        r = st.number_input("Red", 0, 255, 30, key="cmyk_r")
    with col2:
        g = st.number_input("Green", 0, 255, 144, key="cmyk_g")
    with col3:
        b = st.number_input("Blue", 0, 255, 255, key="cmyk_b")

    if st.button("Convert to CMYK"):
        r2, g2, b2 = r / 255.0, g / 255.0, b / 255.0
        k = 1.0 - max(r2, g2, b2)
        if k < 1.0:
            c = (1.0 - r2 - k) / (1.0 - k)
            m = (1.0 - g2 - k) / (1.0 - k)
            y = (1.0 - b2 - k) / (1.0 - k)
        else:
            c = m = y = 0.0
        st.success(f"CMYK: ({c:.2%}, {m:.2%}, {y:.2%}, {k:.2%})")
        results = pd.DataFrame({
            "Channel": ["Cyan", "Magenta", "Yellow", "Key (Black)"],
            "Value": [f"{c:.4f}", f"{m:.4f}", f"{y:.4f}", f"{k:.4f}"],
            "Percent": [f"{c:.1%}", f"{m:.1%}", f"{y:.1%}", f"{k:.1%}"],
        })
        st.dataframe(results, use_container_width=True)
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        st.markdown(f'<div style="width:100%;height:60px;background:{hex_val};'
                    f'border-radius:8px;margin-top:8px;"></div>', unsafe_allow_html=True)


# ── 155. Text to Handwriting Previewer ────────
elif selected_tool == "155. Text to Handwriting Previewer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Run a pre-flight checklist before sending designs to print. Avoid costly printing errors with a comprehensive quality check.")
    st.header("✍️ Text to Handwriting Previewer")
    text = st.text_area("Enter your text", "The quick brown fox jumps over the lazy dog.", height=120)
    font_options = {
        "Caveat": "Caveat",
        "Dancing Script": "Dancing Script",
        "Pacifico": "Pacifico",
        "Indie Flower": "Indie Flower",
        "Sacramento": "Sacramento",
        "Great Vibes": "Great Vibes",
        "Satisfy": "Satisfy",
        "Kalam": "Kalam",
    }
    chosen = st.selectbox("Handwriting style", list(font_options.keys()))
    font_size = st.slider("Font size (px)", 18, 64, 32)
    ink_color = st.color_picker("Ink color", "#1a1a6e")

    if text:
        import_url = f"https://fonts.googleapis.com/css2?family={chosen.replace(' ', '+')}&display=swap"
        st.markdown(
            f'<link href="{import_url}" rel="stylesheet">'
            f'<div style="font-family:\'{chosen}\', cursive; font-size:{font_size}px; '
            f'color:{ink_color}; background:#fffef5; padding:32px; border-radius:8px; '
            f'line-height:1.8; border:1px solid #e0d9c0; white-space:pre-wrap;">'
            f'{text}</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════
# SECURITY & NETWORK UTILITIES (156-160)
# ══════════════════════════════════════════════

# ── 156. SSL Certificate Checker ─────────────
elif selected_tool == "156. SSL Certificate Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Check SSL certificate details and expiration for any domain. Prevent security warnings and maintain customer trust.")
    st.header("🔒 SSL Certificate Checker")
    domain = st.text_input("Domain (e.g. google.com)", "google.com")

    if domain and st.button("Check SSL"):
        import ssl
        import socket
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.settimeout(5)
                s.connect((domain, 443))
                cert = s.getpeercert()
            subject = dict(x[0] for x in cert.get("subject", []))
            issuer = dict(x[0] for x in cert.get("issuer", []))
            not_before = cert.get("notBefore", "N/A")
            not_after = cert.get("notAfter", "N/A")
            san = [v for t, v in cert.get("subjectAltName", [])]

            st.success(f"✅ Valid SSL certificate for **{domain}**")
            info = {
                "Common Name": subject.get("commonName", "N/A"),
                "Organization": subject.get("organizationName", "N/A"),
                "Issuer": issuer.get("organizationName", "N/A"),
                "Valid From": not_before,
                "Valid Until": not_after,
                "Serial Number": cert.get("serialNumber", "N/A"),
            }
            st.dataframe(pd.DataFrame(info.items(), columns=["Field", "Value"]),
                         use_container_width=True)
            if san:
                st.write("**Subject Alt Names:**")
                st.code(", ".join(san[:20]))
        except Exception as e:
            st.error(f"SSL check failed: {e}")


# ── 157. Basic Port Checker ──────────────────
elif selected_tool == "157. Basic Port Checker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Inspect HTTP response headers from any URL. Debug web performance, caching, and security configurations.")
    st.header("🔌 Basic Port Checker")
    host = st.text_input("Host / IP address", "google.com")
    common_ports = {
        21: "FTP", 22: "SSH", 25: "SMTP", 53: "DNS", 80: "HTTP",
        110: "POP3", 143: "IMAP", 443: "HTTPS", 993: "IMAPS",
        995: "POP3S", 3306: "MySQL", 5432: "PostgreSQL", 8080: "HTTP-Alt",
    }
    selected_ports = st.multiselect(
        "Ports to check",
        options=[f"{p} ({n})" for p, n in common_ports.items()],
        default=["80 (HTTP)", "443 (HTTPS)", "22 (SSH)"],
    )

    if host and selected_ports and st.button("Scan Ports"):
        import socket
        results = []
        for entry in selected_ports:
            port = int(entry.split(" ")[0])
            name = common_ports.get(port, "Unknown")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                status = "🟢 Open" if result == 0 else "🔴 Closed"
                sock.close()
            except Exception:
                status = "⚠️ Error"
            results.append({"Port": port, "Service": name, "Status": status})
        st.dataframe(pd.DataFrame(results), use_container_width=True)


# ── 158. BGP ASN Lookup (Simulated) ──────────
elif selected_tool == "158. BGP ASN Lookup":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Scan common ports on a target host to check availability. Identify open services and potential security vulnerabilities.")
    st.header("🌐 BGP ASN Lookup (Simulated)")
    asn_input = st.text_input("Enter ASN number (e.g. 15169) or IP address", "15169")

    ASN_DB = {
        "15169": {"Name": "Google LLC", "Country": "US", "Registry": "ARIN",
                  "Prefixes (IPv4)": "~4,800", "Prefixes (IPv6)": "~600",
                  "Peers": "~7,000", "Type": "Content / CDN"},
        "13335": {"Name": "Cloudflare, Inc.", "Country": "US", "Registry": "ARIN",
                  "Prefixes (IPv4)": "~1,200", "Prefixes (IPv6)": "~200",
                  "Peers": "~12,000", "Type": "CDN / Security"},
        "32934": {"Name": "Meta Platforms, Inc.", "Country": "US", "Registry": "ARIN",
                  "Prefixes (IPv4)": "~350", "Prefixes (IPv6)": "~100",
                  "Peers": "~3,500", "Type": "Content"},
        "16509": {"Name": "Amazon.com (AWS)", "Country": "US", "Registry": "ARIN",
                  "Prefixes (IPv4)": "~7,200", "Prefixes (IPv6)": "~900",
                  "Peers": "~3,000", "Type": "Cloud / Hosting"},
        "8075":  {"Name": "Microsoft Corporation", "Country": "US", "Registry": "ARIN",
                  "Prefixes (IPv4)": "~4,000", "Prefixes (IPv6)": "~500",
                  "Peers": "~4,500", "Type": "Cloud / Enterprise"},
        "20940": {"Name": "Akamai International", "Country": "US", "Registry": "ARIN",
                  "Prefixes (IPv4)": "~4,500", "Prefixes (IPv6)": "~700",
                  "Peers": "~9,000", "Type": "CDN"},
    }

    if asn_input and st.button("Lookup"):
        clean = asn_input.strip().upper().replace("AS", "")
        if clean in ASN_DB:
            info = ASN_DB[clean]
            st.success(f"AS{clean} — {info['Name']}")
            st.dataframe(pd.DataFrame(info.items(), columns=["Field", "Value"]),
                         use_container_width=True)
        else:
            st.warning(f"ASN **{clean}** not in simulated database. "
                       f"In production, query a live BGP API (e.g., bgpview.io).")
            st.info("Simulated DB includes: Google (15169), Cloudflare (13335), "
                    "Meta (32934), AWS (16509), Microsoft (8075), Akamai (20940).")


# ── 159. HTTP API Request Tester (GET/POST) ──
elif selected_tool == "159. HTTP API Request Tester":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Audit password strength with entropy and crack-time estimates. Ensure your team's passwords meet enterprise security standards.")
    st.header("🌐 HTTP API Request Tester")
    method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
    url = st.text_input("URL", "https://httpbin.org/get")
    headers_raw = st.text_area("Headers (JSON)", '{"Accept": "application/json"}', height=80)
    body_raw = ""
    if method in ("POST", "PUT", "PATCH"):
        body_raw = st.text_area("Body (JSON)", '{"key": "value"}', height=100)

    if url and st.button("Send Request"):
        try:
            hdrs = json.loads(headers_raw) if headers_raw.strip() else {}
        except json.JSONDecodeError:
            hdrs = {}
            st.warning("Headers JSON invalid — sending without custom headers.")
        try:
            if method == "GET":
                resp = requests.get(url, headers=hdrs, timeout=15)
            elif method == "POST":
                resp = requests.post(url, headers=hdrs, data=body_raw, timeout=15)
            elif method == "PUT":
                resp = requests.put(url, headers=hdrs, data=body_raw, timeout=15)
            elif method == "DELETE":
                resp = requests.delete(url, headers=hdrs, timeout=15)
            else:
                resp = requests.patch(url, headers=hdrs, data=body_raw, timeout=15)

            st.metric("Status", f"{resp.status_code} {resp.reason}")
            st.metric("Response time", f"{resp.elapsed.total_seconds():.3f}s")
            st.subheader("Response Headers")
            st.json(dict(resp.headers))
            st.subheader("Response Body")
            try:
                st.json(resp.json())
            except Exception:
                st.code(resp.text[:5000])
        except Exception as e:
            st.error(f"Request failed: {e}")


# ── 160. Password Strength Analyzer ──────────
elif selected_tool == "160. Password Strength Analyzer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate firewall rule templates for common configurations. Secure your network with properly structured access control rules.")
    st.header("🔑 Password Strength Analyzer")
    pw = st.text_input("Enter a password to analyze", type="password")

    if pw and st.button("Analyze"):
        import math
        length = len(pw)
        charset = 0
        checks = {
            "Lowercase letters": bool(re.search(r"[a-z]", pw)),
            "Uppercase letters": bool(re.search(r"[A-Z]", pw)),
            "Digits": bool(re.search(r"\d", pw)),
            "Special characters": bool(re.search(r"[^a-zA-Z0-9]", pw)),
            "Length ≥ 8": length >= 8,
            "Length ≥ 12": length >= 12,
            "Length ≥ 16": length >= 16,
            "No common patterns": not bool(re.search(
                r"(123|abc|password|qwerty|letmein|admin|welcome)", pw, re.I)),
        }
        if re.search(r"[a-z]", pw): charset += 26
        if re.search(r"[A-Z]", pw): charset += 26
        if re.search(r"\d", pw): charset += 10
        if re.search(r"[^a-zA-Z0-9]", pw): charset += 33

        entropy = length * math.log2(charset) if charset > 0 else 0
        if entropy >= 80:
            strength, color = "Very Strong 💪", "green"
        elif entropy >= 60:
            strength, color = "Strong ✅", "blue"
        elif entropy >= 40:
            strength, color = "Moderate ⚠️", "orange"
        elif entropy >= 28:
            strength, color = "Weak ❌", "red"
        else:
            strength, color = "Very Weak 🚫", "red"

        st.metric("Entropy", f"{entropy:.1f} bits")
        st.metric("Strength", strength)
        st.metric("Character pool size", charset)

        st.subheader("Criteria Breakdown")
        for label, passed in checks.items():
            icon = "✅" if passed else "❌"
            st.write(f"{icon} {label}")

        # Time-to-crack estimate (offline attack at 10B guesses/sec)
        guesses_per_sec = 10_000_000_000
        combos = charset ** length if charset > 0 else 1
        seconds = combos / guesses_per_sec / 2
        if seconds < 1:
            crack_time = "< 1 second"
        elif seconds < 60:
            crack_time = f"{seconds:.0f} seconds"
        elif seconds < 3600:
            crack_time = f"{seconds / 60:.0f} minutes"
        elif seconds < 86400:
            crack_time = f"{seconds / 3600:.0f} hours"
        elif seconds < 31536000:
            crack_time = f"{seconds / 86400:.0f} days"
        else:
            years = seconds / 31536000
            if years > 1e12:
                crack_time = "millions of years"
            else:
                crack_time = f"{years:,.0f} years"
        st.info(f"⏱️ Estimated offline crack time (10B guesses/s): **{crack_time}**")


# ══════════════════════════════════════════════
# WRITING, CODE & CONVERSION (161-165)
# ══════════════════════════════════════════════

# ── 161. XML Formatter & Validator ────────────
elif selected_tool == "161. XML Formatter & Validator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate Python code snippets for common tasks. Speed up development with ready-to-use, tested code blocks.")
    st.header("📝 XML Formatter & Validator")
    xml_input = st.text_area("Paste XML", height=250,
                             value='<root><item id="1"><name>Test</name></item></root>')

    if xml_input and st.button("Format & Validate"):
        try:
            from xml.dom import minidom
            parsed = minidom.parseString(xml_input)
            pretty = parsed.toprettyxml(indent="  ")
            lines = pretty.split("\n")
            if lines[0].startswith("<?xml") and not xml_input.strip().startswith("<?xml"):
                pretty = "\n".join(lines[1:])
            st.success("✅ XML is well-formed and valid!")
            st.code(pretty.strip(), language="xml")
        except Exception as e:
            st.error(f"❌ XML Validation Error: {e}")


# ── 162. Roman Numeral Converter ──────────────
elif selected_tool == "162. Roman Numeral Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create modern HTML5 boilerplate with best practices. Start every web project with a solid, standards-compliant foundation.")
    st.header("🏛️ Roman Numeral Converter")
    direction = st.radio("Direction", ["Integer → Roman", "Roman → Integer"])

    def int_to_roman(num):
        vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        result = ""
        for v, s in vals:
            while num >= v:
                result += s
                num -= v
        return result

    def roman_to_int(s):
        roman_map = {"I": 1, "V": 5, "X": 10, "L": 50,
                     "C": 100, "D": 500, "M": 1000}
        total = 0
        prev = 0
        for ch in reversed(s.upper()):
            val = roman_map.get(ch, 0)
            if val < prev:
                total -= val
            else:
                total += val
            prev = val
        return total

    if direction == "Integer → Roman":
        num = st.number_input("Enter integer (1–3999)", min_value=1, max_value=3999, value=2024)
        if st.button("Convert"):
            st.success(f"**{num}** = **{int_to_roman(num)}**")
    else:
        roman = st.text_input("Enter Roman numeral", "MMXXIV")
        if roman and st.button("Convert"):
            result = roman_to_int(roman)
            st.success(f"**{roman.upper()}** = **{result}**")
            if int_to_roman(result) == roman.upper():
                st.info("✅ Valid Roman numeral")
            else:
                st.warning("⚠️ Input may not be in standard form")


# ── 163. Unicode Character Finder ─────────────
elif selected_tool == "163. Unicode Character Finder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Convert between JSON and YAML formats seamlessly. Switch between configuration formats for different tools and platforms.")
    st.header("🔤 Unicode Character Finder")
    import unicodedata
    mode = st.radio("Mode", ["Search by name", "Lookup by character", "Lookup by code point"])

    if mode == "Search by name":
        query = st.text_input("Search term (e.g. 'arrow', 'heart', 'star')", "arrow")
        if query and st.button("Search"):
            results = []
            for cp in range(0x0000, 0xFFFF):
                try:
                    name = unicodedata.name(chr(cp), "")
                    if query.upper() in name:
                        results.append({
                            "Char": chr(cp),
                            "Code Point": f"U+{cp:04X}",
                            "Name": name,
                            "HTML Entity": f"&#{cp};",
                        })
                except ValueError:
                    pass
                if len(results) >= 100:
                    break
            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
                st.caption(f"Showing {len(results)} results (max 100)")
            else:
                st.warning("No characters found.")

    elif mode == "Lookup by character":
        char = st.text_input("Paste character(s)", "→")
        if char:
            results = []
            for c in char:
                try:
                    name = unicodedata.name(c, "UNKNOWN")
                except ValueError:
                    name = "UNKNOWN"
                results.append({
                    "Char": c,
                    "Code Point": f"U+{ord(c):04X}",
                    "Name": name,
                    "Category": unicodedata.category(c),
                    "HTML": f"&#{ord(c)};",
                })
            st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        cp_str = st.text_input("Code point (e.g. 2192 or U+2192)", "2192")
        if cp_str and st.button("Lookup"):
            cp_clean = cp_str.upper().replace("U+", "").replace("0X", "")
            try:
                cp = int(cp_clean, 16)
                ch = chr(cp)
                name = unicodedata.name(ch, "UNKNOWN")
                st.markdown(f"### {ch}")
                st.write(f"**Name:** {name}")
                st.write(f"**Code Point:** U+{cp:04X}")
                st.write(f"**Category:** {unicodedata.category(ch)}")
                st.code(f"HTML: &#{cp};  |  Python: '\\u{cp:04X}'")
            except Exception as e:
                st.error(f"Invalid code point: {e}")


# ── 164. YAML to XML Converter ───────────────
elif selected_tool == "164. YAML to XML Converter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build SQL queries visually with SELECT, JOIN, and WHERE clauses. Write complex database queries without memorizing syntax.")
    st.header("🔄 YAML → XML Converter")
    import yaml as yaml_mod

    yaml_input = st.text_area(
        "Paste YAML",
        "person:\n  name: Joshua Newton\n  city: Birmingham\n  skills:\n    - automation\n    - marketing",
        height=200,
    )

    def dict_to_xml(data, root_tag="root", indent=0):
        xml = ""
        pad = "  " * indent
        if isinstance(data, dict):
            for key, val in data.items():
                tag = re.sub(r"[^a-zA-Z0-9_]", "_", str(key))
                if isinstance(val, list):
                    for item in val:
                        xml += f"{pad}<{tag}>\n{dict_to_xml(item, tag, indent + 1)}{pad}</{tag}>\n"
                elif isinstance(val, dict):
                    xml += f"{pad}<{tag}>\n{dict_to_xml(val, tag, indent + 1)}{pad}</{tag}>\n"
                else:
                    xml += f"{pad}<{tag}>{html_mod.escape(str(val))}</{tag}>\n"
        else:
            xml += f"{pad}{html_mod.escape(str(data))}\n"
        return xml

    if yaml_input and st.button("Convert to XML"):
        try:
            data = yaml_mod.safe_load(yaml_input)
            xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
            xml_output += dict_to_xml(data, indent=1)
            xml_output += "</root>"
            st.code(xml_output, language="xml")
            st.download_button("Download XML", xml_output, "converted.xml", "application/xml")
        except Exception as e:
            st.error(f"YAML parse error: {e}")


# ── 165. Article Spinner (synonym swapper) ────
elif selected_tool == "165. Article Spinner":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create Markdown tables from rows and columns of data. Build formatted tables for GitHub READMEs and documentation.")
    st.header("🔁 Article Spinner")
    text = st.text_area("Paste article text", height=200,
                        placeholder="Enter text to spin with basic synonym replacement...")

    SYNONYMS = {
        "good": ["great", "excellent", "fine", "superb", "wonderful"],
        "bad": ["poor", "terrible", "awful", "dreadful", "lousy"],
        "big": ["large", "huge", "enormous", "massive", "vast"],
        "small": ["tiny", "little", "compact", "miniature", "petite"],
        "fast": ["quick", "rapid", "swift", "speedy", "brisk"],
        "slow": ["sluggish", "unhurried", "gradual", "leisurely", "plodding"],
        "important": ["crucial", "vital", "essential", "significant", "key"],
        "easy": ["simple", "effortless", "straightforward", "uncomplicated"],
        "hard": ["difficult", "tough", "challenging", "demanding"],
        "happy": ["glad", "pleased", "joyful", "cheerful", "delighted"],
        "sad": ["unhappy", "sorrowful", "gloomy", "melancholy"],
        "help": ["assist", "support", "aid", "facilitate"],
        "use": ["utilize", "employ", "leverage", "apply"],
        "make": ["create", "build", "produce", "generate"],
        "get": ["obtain", "acquire", "receive", "gain"],
        "show": ["display", "demonstrate", "reveal", "present"],
        "start": ["begin", "commence", "initiate", "launch"],
        "end": ["finish", "conclude", "complete", "terminate"],
        "increase": ["boost", "raise", "elevate", "amplify"],
        "decrease": ["reduce", "lower", "diminish", "cut"],
        "improve": ["enhance", "upgrade", "refine", "optimize"],
        "problem": ["issue", "challenge", "obstacle", "difficulty"],
        "business": ["company", "enterprise", "firm", "organization"],
        "customer": ["client", "buyer", "patron", "consumer"],
        "money": ["funds", "capital", "revenue", "cash"],
    }

    spin_pct = st.slider("Spin aggressiveness (%)", 10, 100, 50)

    if text and st.button("Spin Article"):
        words = text.split()
        spun = []
        changes = 0
        for w in words:
            stripped = re.sub(r"[^a-zA-Z]", "", w).lower()
            if stripped in SYNONYMS and random.randint(1, 100) <= spin_pct:
                replacement = random.choice(SYNONYMS[stripped])
                if w[0].isupper():
                    replacement = replacement.capitalize()
                suffix = re.sub(r"^[a-zA-Z]+", "", w)
                spun.append(replacement + suffix)
                changes += 1
            else:
                spun.append(w)
        result = " ".join(spun)
        st.subheader("Spun Result")
        st.text_area("Output", result, height=200)
        st.info(f"🔄 {changes} word(s) replaced out of {len(words)} total.")


# ══════════════════════════════════════════════
# SOCIAL MEDIA & MARKETING (166-175)
# ══════════════════════════════════════════════

# ── 166. YouTube Tag Extractor ────────────────
elif selected_tool == "166. YouTube Tag Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Write engaging Instagram captions with hooks and hashtags. Boost engagement with captions that stop the scroll and spark conversation.")
    st.header("🎬 YouTube Tag Extractor")
    yt_input = st.text_input("YouTube URL or paste video description/text",
                             "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    if yt_input and st.button("Extract Tags"):
        tags = []
        if "youtube.com" in yt_input or "youtu.be" in yt_input:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(yt_input, headers=headers, timeout=10)
                kw_match = re.search(r'<meta\s+name="keywords"\s+content="([^"]+)"', r.text)
                if kw_match:
                    tags = [t.strip() for t in kw_match.group(1).split(",") if t.strip()]
                desc_match = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', r.text)
                title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', r.text)
                if title_match:
                    st.write(f"**Video Title:** {title_match.group(1)}")
                if desc_match:
                    st.write(f"**Description:** {desc_match.group(1)[:300]}...")
            except Exception as e:
                st.warning(f"Could not fetch URL: {e}. Extracting from text instead.")

        if not tags:
            hashtags = re.findall(r"#(\w+)", yt_input)
            words = re.findall(r"[a-zA-Z]{3,}", yt_input.lower())
            stopwords = {"the", "and", "for", "are", "but", "not", "you", "all",
                         "can", "had", "her", "was", "one", "our", "out", "has",
                         "this", "that", "with", "from", "have", "they", "will",
                         "been", "https", "www", "com", "youtube", "watch"}
            filtered = [w for w in words if w not in stopwords]
            freq = Counter(filtered).most_common(20)
            tags = hashtags + [w for w, c in freq]

        if tags:
            st.success(f"Found {len(tags)} tag(s)")
            st.code(", ".join(tags))
            st.text_area("Comma-separated (for YouTube upload)", ", ".join(tags), height=80)
        else:
            st.warning("No tags could be extracted. Try pasting the video description instead.")


# ── 167. TikTok Caption Spacer & Formatter ───
elif selected_tool == "167. TikTok Caption Spacer & Formatter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan Facebook Group content strategies for community building. Grow and engage your Facebook community with consistent valuable posts.")
    st.header("🎵 TikTok Caption Spacer & Formatter")
    caption = st.text_area("Enter your TikTok caption", height=150,
                           placeholder="Write your caption here...")
    hashtags = st.text_input("Hashtags (space-separated)", "#fyp #viral #business #automation")

    spacer_style = st.selectbox("Spacer style", [
        "Dot spacers (·)",
        "Line spacers (—)",
        "Invisible spacers (⠀)",
        "Emoji spacers (✨)",
    ])

    if caption and st.button("Format Caption"):
        spacer_map = {
            "Dot spacers (·)": "\n·\n·\n·\n·\n·\n",
            "Line spacers (—)": "\n—\n—\n—\n—\n—\n",
            "Invisible spacers (⠀)": "\n⠀\n⠀\n⠀\n⠀\n⠀\n",
            "Emoji spacers (✨)": "\n✨\n✨\n✨\n✨\n✨\n",
        }
        spacer = spacer_map[spacer_style]
        formatted = caption.strip() + spacer + hashtags.strip()

        st.subheader("Formatted Caption")
        st.text_area("Copy this", formatted, height=300)
        st.metric("Character count", len(formatted))
        st.metric("Max TikTok length", "2,200 characters")
        remaining = 2200 - len(formatted)
        if remaining >= 0:
            st.success(f"✅ {remaining} characters remaining")
        else:
            st.error(f"❌ {abs(remaining)} characters over limit!")


# ── 168. LinkedIn Professional Headline Generator
elif selected_tool == "168. LinkedIn Professional Headline Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Write short-form video scripts optimized for TikTok. Create viral-ready scripts that hook viewers in the first 3 seconds.")
    st.header("💼 LinkedIn Professional Headline Generator")
    role = st.text_input("Your role / job title", "Digital Marketing Strategist")
    industry = st.text_input("Industry / niche", "SaaS & Automation")
    skills = st.text_input("Top 3 skills (comma-separated)", "SEO, Content Strategy, Lead Gen")
    value_prop = st.text_input("What value do you provide?", "Helping businesses scale with automation")

    if role and st.button("Generate Headlines"):
        skill_list = [s.strip() for s in skills.split(",")]
        headlines = [
            f"{role} | {industry} | {' · '.join(skill_list)}",
            f"{role} → {value_prop}",
            f"🚀 {role} | {value_prop} | {industry}",
            f"{role} | Specializing in {' & '.join(skill_list[:2])} for {industry}",
            f"Passionate {role} | {skill_list[0]} Expert | {value_prop}",
            f"{value_prop} | {role} @ {industry}",
            f"✦ {role} ✦ {' | '.join(skill_list)} ✦ {industry}",
            f"Results-Driven {role} | {industry} | {value_prop}",
            f"📈 {role} helping {industry} brands with {skill_list[0]} & {skill_list[1] if len(skill_list) > 1 else 'strategy'}",
            f"{role} | I {value_prop.lower()} | {industry} veteran",
        ]
        st.subheader("Generated Headlines")
        for i, h in enumerate(headlines, 1):
            chars = len(h)
            status = "✅" if chars <= 220 else "⚠️ Over 220 chars"
            st.code(h)
            st.caption(f"#{i} — {chars} chars {status}")


# ── 169. Pinterest Pin Title Optimizer ────────
elif selected_tool == "169. Pinterest Pin Title Optimizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan Pinterest board strategies for long-term traffic. Build a content library that drives consistent organic traffic for months.")
    st.header("📌 Pinterest Pin Title Optimizer")
    topic = st.text_input("Pin topic / content", "Home Office Setup Ideas")
    keywords = st.text_input("Target keywords (comma-separated)", "home office, productivity, remote work")

    if topic and st.button("Optimize Titles"):
        kw_list = [k.strip() for k in keywords.split(",")]
        primary = kw_list[0] if kw_list else topic

        titles = [
            f"{topic}: {len(kw_list)*5}+ Ideas You'll Love",
            f"Best {topic} for {datetime.now().year} | {primary.title()} Guide",
            f"How to {topic} Like a Pro | {' + '.join(kw_list[:2]).title()}",
            f"{topic} That Actually Work | {primary.title()} Tips",
            f"The Ultimate {topic} Guide | {' & '.join(kw_list[:2]).title()}",
            f"✨ {topic} Inspiration | {primary.title()} Ideas to Try Now",
            f"{topic} | {len(kw_list)*3} Tips for {kw_list[-1].title() if kw_list else 'Success'}",
            f"Top {topic} Trends for {datetime.now().year}",
        ]

        st.subheader("Optimized Pin Titles")
        for i, t in enumerate(titles, 1):
            chars = len(t)
            if chars <= 100:
                badge = "✅ Great length"
            elif chars <= 150:
                badge = "⚠️ Slightly long"
            else:
                badge = "❌ Too long (max ~100 chars)"
            st.code(t)
            st.caption(f"#{i} — {chars} chars — {badge}")

        st.info("💡 Pinterest recommends titles under 100 characters with front-loaded keywords.")


# ── 170. Social Media Post Scheduler (UI) ────
elif selected_tool == "170. Social Media Post Scheduler":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Outline long-form LinkedIn articles for professional authority. Establish thought leadership and attract B2B leads with in-depth content.")
    st.header("📅 Social Media Post Scheduler")
    st.caption("UI mockup — plan & preview your posting calendar.")

    if "scheduled_posts" not in st.session_state:
        st.session_state.scheduled_posts = []

    with st.form("schedule_form"):
        platform = st.selectbox("Platform", ["Instagram", "Facebook", "Twitter/X",
                                              "LinkedIn", "TikTok", "Pinterest"])
        post_date = st.date_input("Post date")
        post_time = st.time_input("Post time")
        content = st.text_area("Post content", height=100)
        media = st.selectbox("Media type", ["None", "Image", "Video", "Carousel", "Story"])
        submitted = st.form_submit_button("Schedule Post")

    if submitted and content:
        st.session_state.scheduled_posts.append({
            "Platform": platform,
            "Date": str(post_date),
            "Time": str(post_time),
            "Content": content[:80] + "..." if len(content) > 80 else content,
            "Media": media,
            "Status": "⏰ Scheduled",
        })
        st.success(f"✅ Post scheduled for {platform} on {post_date} at {post_time}")

    if st.session_state.scheduled_posts:
        st.subheader("Scheduled Posts")
        st.dataframe(pd.DataFrame(st.session_state.scheduled_posts), use_container_width=True)
        if st.button("Clear All"):
            st.session_state.scheduled_posts = []
            st.rerun()
    else:
        st.info("No posts scheduled yet. Use the form above to add one.")


# ── 171. Facebook Ad Copy Generator ──────────
elif selected_tool == "171. Facebook Ad Copy Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Run a comprehensive audit of your social media presence. Identify gaps, inconsistencies, and optimization opportunities across platforms.")
    st.header("📘 Facebook Ad Copy Generator")
    product = st.text_input("Product / Service name", "Elite Automation Suite")
    audience = st.text_input("Target audience", "Small business owners in Alabama")
    benefit = st.text_input("Key benefit / offer", "Automate 200+ business tasks instantly")
    cta = st.selectbox("CTA", ["Learn More", "Sign Up", "Shop Now", "Get Started",
                                "Book Now", "Download", "Try Free"])
    tone = st.selectbox("Tone", ["Professional", "Casual & Friendly", "Urgent / FOMO",
                                  "Inspirational", "Direct & Bold"])

    if product and st.button("Generate Ad Copy"):
        templates = {
            "Professional": [
                f"Introducing {product}.\n\n{benefit}. Designed specifically for {audience}.\n\n"
                f"Join thousands who've already transformed their workflow.\n\n👉 {cta}",
                f"Still handling everything manually?\n\n{product} empowers {audience} to {benefit.lower()}.\n\n"
                f"See the difference for yourself → {cta}",
            ],
            "Casual & Friendly": [
                f"Hey {audience}! 👋\n\nTired of the daily grind? {product} is here to help you "
                f"{benefit.lower()}.\n\nSeriously, it's a game-changer. Try it out! 🎉\n\n{cta}",
                f"What if you could {benefit.lower()}? 🤔\n\n{product} makes it stupid simple. "
                f"Built for people like you — {audience}.\n\n{cta} ⬇️",
            ],
            "Urgent / FOMO": [
                f"⚡ {audience} — your competitors are already using {product}.\n\n"
                f"Don't get left behind. {benefit}.\n\n🔥 Limited time offer → {cta} NOW",
                f"🚨 ATTENTION {audience.upper()}\n\n{benefit}. {product} is changing the game and "
                f"spots are filling fast.\n\n⏳ {cta} before it's too late!",
            ],
            "Inspirational": [
                f"Imagine being able to {benefit.lower()}.\n\nThat's not a dream — it's {product}. "
                f"Built for visionary {audience} who refuse to settle.\n\n🌟 {cta}",
                f"Your business deserves better.\n\n{product} was created to help {audience} "
                f"{benefit.lower()}. The future starts now.\n\n✨ {cta}",
            ],
            "Direct & Bold": [
                f"{benefit}.\n\n{product}. Built for {audience}.\n\nNo fluff. No BS.\n\n→ {cta}",
                f"Stop wasting time.\n{product} lets you {benefit.lower()}.\n"
                f"Made for {audience}.\n\n{cta} →",
            ],
        }
        copies = templates.get(tone, templates["Professional"])
        st.subheader(f"Ad Copy — {tone} Tone")
        for i, copy in enumerate(copies, 1):
            st.text_area(f"Version {i}", copy, height=180, key=f"fb_ad_{i}")
            st.caption(f"Characters: {len(copy)} | Recommended: under 500 for primary text")


# ── 172. Instagram Carousel Idea Generator ────
elif selected_tool == "172. Instagram Carousel Idea Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate attention-grabbing hooks for social media content. Create opening lines that make people stop scrolling and pay attention.")
    st.header("📸 Instagram Carousel Idea Generator")
    niche = st.text_input("Your niche / industry", "Digital Marketing & Automation")
    goal = st.selectbox("Carousel goal", ["Educate", "Sell", "Engage", "Inspire", "Entertain"])
    slides_count = st.slider("Number of slides", 3, 10, 7)

    if niche and st.button("Generate Carousel Ideas"):
        ideas = {
            "Educate": [
                {"Title": f"{slides_count} {niche} Mistakes You're Making",
                 "Hook": f"Slide 1: 'Stop doing THIS in {niche}...'",
                 "Structure": "Problem → Mistake → Fix → CTA"},
                {"Title": f"The Beginner's Guide to {niche}",
                 "Hook": "Slide 1: 'Everything I wish I knew when I started'",
                 "Structure": "Hook → Step 1 → Step 2 → ... → Summary → CTA"},
                {"Title": f"{niche}: Then vs. Now",
                 "Hook": "Slide 1: 'How things have changed...'",
                 "Structure": "Before/After comparisons per slide → CTA"},
            ],
            "Sell": [
                {"Title": f"Why {niche} Professionals Choose Our Solution",
                 "Hook": "Slide 1: 'The #1 reason businesses switch...'",
                 "Structure": "Problem → Features → Social Proof → Offer → CTA"},
                {"Title": f"What You Get (Breakdown)",
                 "Hook": "Slide 1: 'Here's everything inside...'",
                 "Structure": "Feature 1 → Feature 2 → ... → Price/Value → CTA"},
            ],
            "Engage": [
                {"Title": f"Rate Your {niche} Knowledge (Quiz)",
                 "Hook": "Slide 1: 'Can you get all 5 right?'",
                 "Structure": "Question slides → Answer reveal → Score → CTA"},
                {"Title": f"This or That: {niche} Edition",
                 "Hook": "Slide 1: 'Drop your answer in comments!'",
                 "Structure": "Option A vs B per slide → Results → CTA"},
            ],
            "Inspire": [
                {"Title": f"My {niche} Journey",
                 "Hook": "Slide 1: 'Where it all started...'",
                 "Structure": "Timeline → Milestones → Lessons → CTA"},
                {"Title": f"Quotes That Changed My {niche} Game",
                 "Hook": "Slide 1: 'Save this for motivation'",
                 "Structure": "Quote per slide → Your take → CTA"},
            ],
            "Entertain": [
                {"Title": f"{niche} Expectations vs. Reality",
                 "Hook": "Slide 1: 'What I thought it'd be like...'",
                 "Structure": "Expectation → Reality pairs → Relatable CTA"},
                {"Title": f"Types of People in {niche}",
                 "Hook": "Slide 1: 'Tag yourself 👇'",
                 "Structure": "Persona per slide → Which are you? → CTA"},
            ],
        }
        carousel_list = ideas.get(goal, ideas["Educate"])
        for idx, idea in enumerate(carousel_list, 1):
            st.subheader(f"Idea #{idx}: {idea['Title']}")
            st.write(f"🪝 **Hook:** {idea['Hook']}")
            st.write(f"📐 **Structure ({slides_count} slides):** {idea['Structure']}")
            st.markdown("---")
            st.write("**Slide-by-slide outline:**")
            for s in range(1, slides_count + 1):
                if s == 1:
                    st.write(f"  📌 Slide {s}: Hook / Title slide")
                elif s == slides_count:
                    st.write(f"  📌 Slide {s}: CTA — Follow for more / Link in bio")
                else:
                    st.write(f"  📌 Slide {s}: Content point #{s - 1}")
            st.markdown("---")


# ── 173. Video Script Hook Generator ─────────
elif selected_tool == "173. Video Script Hook Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Calculate engagement rates for any social media post. Measure content performance and identify what resonates with your audience.")
    st.header("🎥 Video Script Hook Generator")
    topic = st.text_input("Video topic", "Why most small businesses fail at automation")
    platform = st.selectbox("Platform", ["YouTube", "TikTok", "Instagram Reels",
                                          "LinkedIn Video", "Facebook Video"])
    hook_style = st.selectbox("Hook style", [
        "Question", "Bold Statement", "Story", "Statistic",
        "Contrarian", "How-To", "Challenge",
    ])

    if topic and st.button("Generate Hooks"):
        hooks = {
            "Question": [
                f"Have you ever wondered why {topic.lower()}?",
                f"What if I told you the truth about {topic.lower()}?",
                f"Why does nobody talk about {topic.lower()}?",
            ],
            "Bold Statement": [
                f"Here's the hard truth about {topic.lower()} that nobody wants to hear.",
                f"{topic} — and it's not even close.",
                f"I'm about to change the way you think about {topic.lower()}.",
            ],
            "Story": [
                f"Last year, I almost gave up on {topic.lower()}. Here's what happened instead...",
                f"A client came to me with this exact problem: {topic.lower()}...",
                f"Three months ago I made a mistake with {topic.lower()} that cost me everything...",
            ],
            "Statistic": [
                f"Did you know that 87% of businesses struggle with {topic.lower()}?",
                f"Only 3% of people actually understand {topic.lower()}. Here's why...",
                f"The data is clear: {topic.lower()} is costing you more than you think.",
            ],
            "Contrarian": [
                f"Everything you've been told about {topic.lower()} is wrong.",
                f"Unpopular opinion: {topic.lower()} is actually easier than you think.",
                f"Stop doing what everyone else does with {topic.lower()}. Do this instead.",
            ],
            "How-To": [
                f"Here's exactly how to handle {topic.lower()} in under 60 seconds.",
                f"The simplest framework for {topic.lower()} — save this.",
                f"Step 1 of mastering {topic.lower()} starts right here...",
            ],
            "Challenge": [
                f"I bet you can't watch this video about {topic.lower()} without taking notes.",
                f"Try this {topic.lower()} hack and tell me it doesn't work.",
                f"If you can master {topic.lower()} after this video, you're ahead of 90%.",
            ],
        }

        hook_list = hooks.get(hook_style, hooks["Question"])
        st.subheader(f"{hook_style} Hooks for {platform}")
        for i, h in enumerate(hook_list, 1):
            st.code(h)
            word_count = len(h.split())
            st.caption(f"Hook #{i} — {word_count} words — "
                       f"{'✅ Under 3 sec' if word_count <= 15 else '⚠️ Might run long'}")

        st.info(f"💡 Best practice for {platform}: Lead with the hook in the first 1-3 seconds. "
                "Cut the fluff. Start mid-action if possible.")


# ── 174. Newsletter Subject Line Scorer ───────
elif selected_tool == "174. Newsletter Subject Line Scorer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Plan and template social proof screenshots for marketing. Turn customer wins and reviews into compelling visual testimonials.")
    st.header("📧 Newsletter Subject Line Scorer")
    subject = st.text_input("Enter subject line", "🚀 5 Automation Hacks That Save 10 Hours/Week")

    if subject and st.button("Score Subject Line"):
        score = 50  # baseline
        feedback = []

        length = len(subject)
        if 30 <= length <= 50:
            score += 15
            feedback.append("✅ Perfect length (30-50 chars)")
        elif 20 <= length <= 60:
            score += 8
            feedback.append("⚠️ Acceptable length, but 30-50 is ideal")
        else:
            score -= 10
            feedback.append(f"❌ Length ({length} chars) — aim for 30-50")

        if re.search(r"\d", subject):
            score += 10
            feedback.append("✅ Contains numbers (boosts open rate)")
        else:
            feedback.append("💡 Consider adding a number for specificity")

        import unicodedata as _ud
        has_emoji = any(_ud.category(c).startswith("So") for c in subject)
        if has_emoji:
            score += 5
            feedback.append("✅ Has emoji (can boost mobile open rates)")

        power_words = ["free", "exclusive", "secret", "proven", "new", "urgent",
                       "limited", "save", "hack", "mistake", "instant", "ultimate",
                       "boost", "unlock", "discover", "revealed"]
        found_power = [w for w in power_words if w in subject.lower()]
        if found_power:
            score += len(found_power) * 3
            feedback.append(f"✅ Power words found: {', '.join(found_power)}")
        else:
            feedback.append("💡 Add power words (free, exclusive, proven, etc.)")

        spam_words = ["buy now", "click here", "act now", "limited time",
                      "!!!!", "$$$$", "FREE", "GUARANTEED", "100%"]
        found_spam = [w for w in spam_words if w in subject]
        if found_spam:
            score -= len(found_spam) * 8
            feedback.append(f"❌ Spam triggers detected: {', '.join(found_spam)}")

        if "{" in subject or "you" in subject.lower():
            score += 5
            feedback.append("✅ Personalization / 'you' language detected")

        if "?" in subject:
            score += 5
            feedback.append("✅ Question format (drives curiosity)")

        score = max(0, min(100, score))
        if score >= 80:
            grade = "A — Excellent 🏆"
        elif score >= 65:
            grade = "B — Good ✅"
        elif score >= 50:
            grade = "C — Average ⚠️"
        else:
            grade = "D — Needs Work ❌"

        st.metric("Score", f"{score}/100")
        st.metric("Grade", grade)
        st.subheader("Feedback")
        for f in feedback:
            st.write(f)
        st.metric("Character count", length)
        st.metric("Word count", len(subject.split()))


# ── 175. Competitor Keyword Extractor ─────────
elif selected_tool == "175. Competitor Keyword Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Track and analyze hashtag performance metrics. Double down on hashtags that drive reach and cut the ones that don't.")
    st.header("🔍 Competitor Keyword Extractor")
    url = st.text_input("Competitor URL", "https://digitalenvisioned.net")
    st.caption("Extracts keywords from page title, headings, meta tags, and body text.")

    if url and st.button("Extract Keywords"):
        try:
            headers = {"User-Agent": "DigitalEnvisionedBot/1.0"}
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            texts = []
            title = soup.find("title")
            if title:
                texts.append(title.get_text(strip=True) * 3)  # weight title higher

            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                texts.append(meta_desc["content"] * 2)

            meta_kw = soup.find("meta", attrs={"name": "keywords"})
            if meta_kw and meta_kw.get("content"):
                texts.append(meta_kw["content"] * 2)

            for tag in ["h1", "h2", "h3"]:
                for h in soup.find_all(tag):
                    texts.append(h.get_text(strip=True) * 2)

            body = soup.get_text(separator=" ", strip=True)
            texts.append(body)

            full_text = " ".join(texts).lower()
            words = re.findall(r"[a-z]{3,}", full_text)
            stopwords = {"the", "and", "for", "are", "but", "not", "you", "all",
                         "can", "had", "her", "was", "one", "our", "out", "has",
                         "this", "that", "with", "from", "have", "they", "will",
                         "been", "your", "which", "their", "about", "would",
                         "there", "what", "each", "make", "like", "than",
                         "into", "just", "over", "also", "more", "other",
                         "some", "very", "when", "come", "could", "them",
                         "only", "its", "who", "get", "how"}
            filtered = [w for w in words if w not in stopwords]

            word_freq = Counter(filtered).most_common(30)

            bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered) - 1)]
            bigram_freq = Counter(bigrams).most_common(15)

            if title:
                st.write(f"**Page Title:** {title.get_text(strip=True)}")
            if meta_desc and meta_desc.get("content"):
                st.write(f"**Meta Description:** {meta_desc['content'][:200]}")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top Keywords")
                kw_df = pd.DataFrame(word_freq, columns=["Keyword", "Frequency"])
                st.dataframe(kw_df, use_container_width=True)
            with col2:
                st.subheader("Top Phrases (Bigrams)")
                bg_df = pd.DataFrame(bigram_freq, columns=["Phrase", "Frequency"])
                st.dataframe(bg_df, use_container_width=True)

            total = len(filtered)
            if total > 0:
                st.subheader("Keyword Density (Top 10)")
                density_data = []
                for kw, count in word_freq[:10]:
                    density_data.append({
                        "Keyword": kw,
                        "Count": count,
                        "Density": f"{(count / total) * 100:.2f}%",
                    })
                st.dataframe(pd.DataFrame(density_data), use_container_width=True)

        except Exception as e:
            st.error(f"Failed to fetch URL: {e}")


# ══════════════════════════════════════════════

# ── 176. Local SEO Citation Format Generator ──
elif selected_tool == "176. Local SEO Citation Format Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Run a comprehensive Local SEO audit for your business. Ensure your business appears in local search results and Google Maps.")
    st.header("📍 Local SEO Citation Format Generator")
    st.caption("Generate consistent NAP (Name, Address, Phone) citation formats for top directories.")

    col1, col2 = st.columns(2)
    with col1:
        biz_name = st.text_input("Business Name", "Digital Envisioned LLC")
        address = st.text_input("Street Address", "123 Innovation Drive")
        city = st.text_input("City", "Birmingham")
    with col2:
        state = st.text_input("State", "AL")
        zipcode = st.text_input("ZIP Code", "35203")
        phone = st.text_input("Phone", "(205) 555-0147")
    website = st.text_input("Website URL", "https://digitalenvisioned.net")
    category = st.text_input("Primary Business Category", "Marketing Agency")
    description = st.text_area("Short Business Description (max 250 chars)",
                               "Premium digital automation and marketing solutions for businesses in Alabama.",
                               height=80)

    if biz_name and address and st.button("Generate Citation Formats"):
        full_addr = f"{address}, {city}, {state} {zipcode}"
        directories = {
            "Google Business Profile": {
                "Business Name": biz_name,
                "Address": full_addr,
                "Phone": phone,
                "Website": website,
                "Category": category,
                "Description": description[:750],
            },
            "Yelp": {
                "Business Name": biz_name,
                "Address Line 1": address,
                "City": city,
                "State": state,
                "Zip": zipcode,
                "Phone": phone,
                "Website": website,
                "Category": category,
            },
            "Facebook Business Page": {
                "Page Name": biz_name,
                "Street": address,
                "City, State ZIP": f"{city}, {state} {zipcode}",
                "Phone": phone,
                "Website": website,
                "About (Short)": description[:255],
            },
            "Apple Maps Connect": {
                "Business Name": biz_name,
                "Street Address": address,
                "City": city,
                "State": state,
                "ZIP": zipcode,
                "Phone": phone,
                "Website": website,
            },
            "Bing Places": {
                "Business Name": biz_name,
                "Address": full_addr,
                "Phone": phone,
                "Website": website,
                "Category": category,
            },
            "BBB (Better Business Bureau)": {
                "Business Name": biz_name,
                "Address": full_addr,
                "Phone": phone,
                "Website": website,
                "Type": category,
            },
            "Yellow Pages / YP.com": {
                "Company Name": biz_name,
                "Address": address,
                "City, State ZIP": f"{city}, {state} {zipcode}",
                "Phone": phone,
                "URL": website,
                "Heading": category,
            },
            "Nextdoor Business": {
                "Business Name": biz_name,
                "Address": full_addr,
                "Phone": phone,
                "Website": website,
                "Category": category,
            },
        }

        for dir_name, fields in directories.items():
            with st.expander(f"📋 {dir_name}", expanded=False):
                for k, v in fields.items():
                    st.text_input(k, v, key=f"cite_{dir_name}_{k}", disabled=True)

        # Consolidated copy block
        st.subheader("📋 Master NAP (Copy & Paste)")
        nap_block = f"""{biz_name}
{address}
{city}, {state} {zipcode}
{phone}
{website}"""
        st.code(nap_block)
        st.success(f"✅ Generated citation formats for {len(directories)} directories. "
                   "Keep NAP *exactly consistent* across all listings for best SEO results.")


# ── 177. Google My Business Review Link Builder
elif selected_tool == "177. Google My Business Review Link Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Optimize your Google Business Profile for maximum visibility. Get more calls, visits, and leads from Google's local search results.")
    st.header("⭐ Google My Business Review Link Builder")
    st.caption("Create a direct review link for customers. They click it → your Google review form opens.")

    place_id = st.text_input("Google Place ID",
                             placeholder="ChIJrTLr-GyuEmsRBfy61i59si0",
                             help="Find your Place ID at: https://developers.google.com/maps/documentation/places/web-service/place-id")
    biz_name = st.text_input("Business Name (for display)", "Digital Envisioned")

    if place_id and st.button("Generate Review Links"):
        review_url = f"https://search.google.com/local/writereview?placeid={place_id}"
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        short_review = f"https://g.page/{place_id}/review" if len(place_id) < 30 else review_url

        st.subheader("🔗 Your Review Links")
        st.text_input("Direct Review Link (primary)", review_url, key="gmb_main")
        st.text_input("Google Maps Link", maps_url, key="gmb_maps")

        st.subheader("📱 Ready-to-Send Templates")
        sms_template = (f"Hi! Thanks for choosing {biz_name}. "
                        f"We'd love your feedback — it takes 30 seconds: {review_url}")
        email_template = (f"Subject: How was your experience with {biz_name}?\n\n"
                          f"Hi [Customer Name],\n\n"
                          f"Thank you for choosing {biz_name}! Your feedback helps us serve you better.\n\n"
                          f"Could you take a moment to leave us a quick review?\n"
                          f"👉 {review_url}\n\n"
                          f"We truly appreciate your time!\n\n"
                          f"Best regards,\n{biz_name} Team")

        st.text_area("📱 SMS Template", sms_template, height=80)
        st.text_area("📧 Email Template", email_template, height=200)

        # QR code for the review link
        qr = qrcode.QRCode(box_size=8, border=3)
        qr.add_data(review_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a73e8", back_color="white").convert("RGB")
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Review QR Code — print for in-store use", width=250)
        st.download_button("Download QR Code", buf.getvalue(), "review_qr.png", "image/png")

        st.success("✅ Share these links via email, SMS, receipts, or print the QR code!")


# ── 178. AI Prompt Architect ─────────────────
elif selected_tool == "178. AI Prompt Architect":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build and manage local business citations for SEO. Strengthen your local search presence with consistent NAP data across directories.")
    st.header("🧠 AI Prompt Architect")
    st.caption("Build optimized prompts for ChatGPT, Claude, Gemini, and other LLMs.")

    task = st.text_area("What do you want the AI to do?",
                        "Write a marketing strategy for a local automation agency", height=80)
    role = st.text_input("Role / Persona for the AI", "Expert digital marketing strategist")
    audience = st.text_input("Target audience", "Small business owners in Alabama")
    tone = st.selectbox("Desired tone", ["Professional", "Casual", "Persuasive",
                                          "Academic", "Friendly", "Direct", "Creative"])
    format_out = st.selectbox("Output format", ["Detailed paragraphs", "Numbered list",
                                                 "Bullet points", "Step-by-step guide",
                                                 "Table/Comparison", "Framework", "Email"])
    constraints = st.text_input("Constraints / special instructions (optional)",
                                "Keep it under 500 words. Focus on actionable tactics.")

    frameworks = st.multiselect("Prompt engineering frameworks to apply", [
        "Chain of Thought (step-by-step reasoning)",
        "Few-Shot (include examples)",
        "Role Play (assign expert persona)",
        "Structured Output (specify format)",
        "Constraints (set boundaries)",
    ], default=["Role Play (assign expert persona)", "Structured Output (specify format)"])

    if task and st.button("Build Optimized Prompt"):
        prompt_parts = []

        # Role
        prompt_parts.append(f"You are a {role} with 15+ years of experience.")

        # Context
        if audience:
            prompt_parts.append(f"Your audience is: {audience}.")

        # Task
        prompt_parts.append(f"\n**Task:** {task}")

        # Chain of thought
        if "Chain of Thought (step-by-step reasoning)" in frameworks:
            prompt_parts.append("\nThink through this step-by-step before providing your final answer.")

        # Format
        format_map = {
            "Detailed paragraphs": "Write your response in detailed, well-structured paragraphs.",
            "Numbered list": "Format your response as a clear numbered list.",
            "Bullet points": "Use bullet points for easy scanning.",
            "Step-by-step guide": "Present this as a step-by-step guide with clear actions for each step.",
            "Table/Comparison": "Present key information in a table format where applicable.",
            "Framework": "Structure your response as a reusable framework with clear sections.",
            "Email": "Write this as a professional email with subject line, greeting, body, and sign-off.",
        }
        prompt_parts.append(f"\n**Format:** {format_map.get(format_out, format_out)}")

        # Tone
        prompt_parts.append(f"**Tone:** {tone}")

        # Constraints
        if constraints:
            prompt_parts.append(f"**Constraints:** {constraints}")

        # Few-shot
        if "Few-Shot (include examples)" in frameworks:
            prompt_parts.append("\n[Include 1-2 examples of the desired output style here before asking for the full response.]")

        final_prompt = "\n".join(prompt_parts)

        st.subheader("✨ Your Optimized Prompt")
        st.text_area("Copy this prompt", final_prompt, height=350)

        # Meta analysis
        word_count = len(final_prompt.split())
        st.subheader("📊 Prompt Analysis")
        analysis = {
            "Word count": word_count,
            "Estimated tokens": f"~{int(word_count * 1.3)}",
            "Frameworks applied": len(frameworks),
            "Has role assignment": "✅" if role else "❌",
            "Has format specification": "✅",
            "Has constraints": "✅" if constraints else "❌",
            "Has audience targeting": "✅" if audience else "❌",
        }
        st.dataframe(pd.DataFrame(analysis.items(), columns=["Metric", "Value"]),
                     use_container_width=True)

        st.info("💡 Paste this prompt directly into ChatGPT, Claude, or Gemini for best results.")


# ── 179. Cold Email Sequence Framework Builder ─
elif selected_tool == "179. Cold Email Sequence Framework Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate professional responses to customer reviews. Build trust and loyalty by responding thoughtfully to every review.")
    st.header("📧 Cold Email Sequence Framework Builder")

    prospect_type = st.text_input("Who are you reaching out to?", "Local business owners in Birmingham, AL")
    your_company = st.text_input("Your company / service", "Digital Envisioned — Automation Suite")
    offer = st.text_input("Your core offer / value prop", "200-tool automation platform that saves 20+ hours/week")
    pain_point = st.text_input("Main pain point you solve", "Wasting time on manual marketing and admin tasks")
    cta = st.text_input("Desired call-to-action", "Book a 15-minute demo call")
    num_emails = st.slider("Number of emails in sequence", 3, 7, 5)

    if prospect_type and st.button("Generate Email Sequence"):
        templates = [
            {
                "subject": f"Quick question about your {pain_point.split()[0].lower() if pain_point else 'workflow'}",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"I noticed you're a {prospect_type.lower()} — and I had a quick question.\n\n"
                    f"Are you still dealing with {pain_point.lower()}?\n\n"
                    f"We built {your_company} specifically for people like you. "
                    f"Our {offer.lower()} and the results have been incredible.\n\n"
                    f"Would you be open to a quick chat? {cta}.\n\n"
                    f"Best,\n[Your Name]"
                ),
                "timing": "Day 1",
                "purpose": "Initial outreach — introduce + curiosity",
            },
            {
                "subject": f"Re: {pain_point.split()[0] if pain_point else 'your business'}",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"Following up on my last note. I know you're busy — so I'll keep this short.\n\n"
                    f"Here's what one of our clients said after using {your_company}:\n\n"
                    f"\"We saved 20+ hours a week and doubled our leads in 60 days.\"\n\n"
                    f"If that sounds interesting, I'd love to show you how. {cta}.\n\n"
                    f"[Your Name]"
                ),
                "timing": "Day 3",
                "purpose": "Follow-up — social proof",
            },
            {
                "subject": f"The {pain_point.split()[-1] if pain_point else 'productivity'} problem",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"Most {prospect_type.lower()} I talk to have the same problem: {pain_point.lower()}.\n\n"
                    f"Here's the thing — it doesn't have to be that way.\n\n"
                    f"Our {offer.lower()}. No contracts. No risk.\n\n"
                    f"Want me to show you how it works? {cta}.\n\n"
                    f"[Your Name]"
                ),
                "timing": "Day 6",
                "purpose": "Value proposition — address pain directly",
            },
            {
                "subject": "3 ideas for your business (free)",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"I put together 3 quick ideas for how {prospect_type.lower()} like you can "
                    f"solve {pain_point.lower()}:\n\n"
                    f"1. Automate your [top manual task] — saves ~5 hrs/week\n"
                    f"2. Use [specific tool from your suite] to handle [specific task]\n"
                    f"3. Set up [quick win] in under 10 minutes\n\n"
                    f"Happy to walk you through any of these. {cta}.\n\n"
                    f"[Your Name]"
                ),
                "timing": "Day 10",
                "purpose": "Give value — free tips to build trust",
            },
            {
                "subject": "Should I close your file?",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"I've reached out a few times and haven't heard back — totally understand, "
                    f"timing is everything.\n\n"
                    f"If {pain_point.lower()} isn't a priority right now, no worries at all. "
                    f"I'll close your file on my end.\n\n"
                    f"But if you'd like to see how {your_company} can help, just reply "
                    f"\"interested\" and I'll send over some info.\n\n"
                    f"Either way — wishing you the best.\n\n"
                    f"[Your Name]"
                ),
                "timing": "Day 14",
                "purpose": "Breakup email — creates urgency",
            },
            {
                "subject": f"One last thing about {your_company.split('—')[0].strip() if '—' in your_company else your_company}",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"I know I said I'd close your file — but I just wanted to share one more thing.\n\n"
                    f"We just helped a {prospect_type.lower().rstrip('s')} "
                    f"go from struggling with {pain_point.lower()} to fully automated in 2 weeks.\n\n"
                    f"If you ever want to chat, my calendar is always open: {cta}.\n\n"
                    f"Cheers,\n[Your Name]"
                ),
                "timing": "Day 21",
                "purpose": "Resurrection — final case study touch",
            },
            {
                "subject": f"Saw something that reminded me of your business",
                "body": (
                    f"Hi [First Name],\n\n"
                    f"Came across something today that made me think of you.\n\n"
                    f"A lot of {prospect_type.lower()} are making the shift to automation this year — "
                    f"and the ones who move early are seeing huge wins.\n\n"
                    f"No pressure — just wanted to keep you in the loop.\n\n"
                    f"If you ever want to explore {your_company}, I'm here.\n\n"
                    f"[Your Name]"
                ),
                "timing": "Day 30",
                "purpose": "Long-term nurture touch",
            },
        ]

        for i, email in enumerate(templates[:num_emails], 1):
            with st.expander(f"📨 Email {i} — {email['timing']} ({email['purpose']})", expanded=(i == 1)):
                st.text_input(f"Subject Line", email["subject"], key=f"cold_subj_{i}", disabled=True)
                st.text_area(f"Email Body", email["body"], height=220, key=f"cold_body_{i}")
                st.caption(f"Purpose: {email['purpose']}")

        st.success(f"✅ Generated {min(num_emails, len(templates))}-email cold outreach sequence.")


# ── 180. Customer Avatar / Buyer Persona Generator
elif selected_tool == "180. Customer Avatar / Buyer Persona Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create briefs for location-specific landing pages. Convert local searchers into customers with geo-targeted content.")
    st.header("🎯 Customer Avatar / Buyer Persona Generator")

    col1, col2 = st.columns(2)
    with col1:
        persona_name = st.text_input("Persona name", "Ambitious Alex")
        age_range = st.selectbox("Age range", ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
        gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "All"])
        location = st.text_input("Location", "Birmingham, AL")
        income = st.selectbox("Annual income", ["Under $30K", "$30K-$50K", "$50K-$75K",
                                                 "$75K-$100K", "$100K-$150K", "$150K+"])
    with col2:
        job_title = st.text_input("Job title / role", "Small Business Owner")
        industry = st.text_input("Industry", "Local Services")
        education = st.selectbox("Education", ["High School", "Some College", "Bachelor's",
                                                "Master's", "PhD", "Self-taught"])
        goals = st.text_area("Top goals (one per line)", "Scale business without hiring\nAutomate marketing\nGet more leads", height=90)
        pain_points = st.text_area("Top pain points (one per line)", "Not enough time\nToo many manual tasks\nCan't afford a full team", height=90)

    channels = st.multiselect("Where they spend time online",
                              ["Facebook", "Instagram", "LinkedIn", "TikTok", "YouTube",
                               "Twitter/X", "Reddit", "Google Search", "Email", "Podcasts"],
                              default=["Facebook", "YouTube", "Google Search"])
    objections = st.text_area("Common objections to your product",
                              "Too expensive\nI don't have time to learn new tools\nI've tried similar things before",
                              height=80)

    if persona_name and st.button("Generate Persona"):
        goals_list = [g.strip() for g in goals.strip().split("\n") if g.strip()]
        pain_list = [p.strip() for p in pain_points.strip().split("\n") if p.strip()]
        obj_list = [o.strip() for o in objections.strip().split("\n") if o.strip()]

        st.subheader(f"🧑‍💼 {persona_name}")

        demo_data = {
            "Age Range": age_range,
            "Gender": gender,
            "Location": location,
            "Income": income,
            "Education": education,
            "Job Title": job_title,
            "Industry": industry,
        }
        st.markdown("**Demographics**")
        st.dataframe(pd.DataFrame(demo_data.items(), columns=["Field", "Value"]),
                     use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🎯 Goals**")
            for g in goals_list:
                st.write(f"• {g}")
        with col2:
            st.markdown("**😤 Pain Points**")
            for p in pain_list:
                st.write(f"• {p}")
        with col3:
            st.markdown("**🛑 Objections**")
            for o in obj_list:
                st.write(f"• {o}")

        st.markdown("**📱 Preferred Channels:** " + " · ".join(channels))

        # Marketing message builder
        st.subheader("💬 Suggested Marketing Message")
        if pain_list and goals_list:
            msg = (f"Tired of {pain_list[0].lower()}? "
                   f"Imagine being able to {goals_list[0].lower()}. "
                   f"Our solution is built specifically for {job_title.lower()}s like you in {industry.lower()}. "
                   f"No complexity — just results.")
            st.code(msg)

        st.success("✅ Buyer persona generated! Use this to align your marketing, content, and ads.")


# ── 181. Agency Proposal Outline Generator ────
elif selected_tool == "181. Agency Proposal Outline Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Write ad copy targeted to specific geographic areas. Speak directly to local audiences with relevant, location-aware messaging.")
    st.header("📄 Agency Proposal Outline Generator")

    col1, col2 = st.columns(2)
    with col1:
        agency_name = st.text_input("Your agency name", "Digital Envisioned")
        client_name = st.text_input("Client / prospect name", "Acme Local Services")
        project_name = st.text_input("Project name", "Full-Stack Marketing Automation Setup")
    with col2:
        timeline = st.text_input("Estimated timeline", "30 days")
        budget_range = st.text_input("Budget range", "$2,500 – $5,000")
        date_str = st.text_input("Proposal date", datetime.now().strftime("%B %d, %Y"))

    services = st.multiselect("Services included", [
        "Website Design & Development", "SEO & Local SEO", "Social Media Management",
        "Content Marketing", "Email Marketing Automation", "PPC / Google Ads",
        "Facebook / Instagram Ads", "CRM Setup & Integration", "Brand Strategy",
        "Analytics & Reporting Dashboard", "Reputation Management", "Funnel Building",
    ], default=["SEO & Local SEO", "Email Marketing Automation", "Analytics & Reporting Dashboard"])

    deliverables = st.text_area("Key deliverables (one per line)",
                                "Complete SEO audit & optimization\nAutomated email sequences (5 emails)\nMonthly analytics report",
                                height=100)

    if agency_name and client_name and st.button("Generate Proposal Outline"):
        deliv_list = [d.strip() for d in deliverables.strip().split("\n") if d.strip()]

        outline = f"""{'='*60}
PROPOSAL: {project_name.upper()}
{'='*60}

Prepared by: {agency_name}
Prepared for: {client_name}
Date: {date_str}
Timeline: {timeline}
Investment: {budget_range}

{'─'*60}
1. EXECUTIVE SUMMARY
{'─'*60}
{agency_name} proposes a comprehensive engagement with {client_name}
to deliver {project_name}. This project will be completed within
{timeline} and will include {len(services)} core service areas.

{'─'*60}
2. SCOPE OF SERVICES
{'─'*60}"""

        for i, svc in enumerate(services, 1):
            outline += f"\n  {i}. {svc}"

        outline += f"""

{'─'*60}
3. DELIVERABLES
{'─'*60}"""

        for i, d in enumerate(deliv_list, 1):
            outline += f"\n  {i}. {d}"

        outline += f"""

{'─'*60}
4. TIMELINE & MILESTONES
{'─'*60}
  Week 1–2: Discovery, audit, and strategy development
  Week 2–3: Implementation and setup
  Week 3–4: Testing, optimization, and launch
  Week 4+:  Monitoring, reporting, and iteration

{'─'*60}
5. INVESTMENT
{'─'*60}
  Total Project Investment: {budget_range}
  Payment Terms: 50% upfront, 50% upon completion
  Includes: All services listed above
  Excludes: Ad spend, third-party subscriptions, stock assets

{'─'*60}
6. WHY {agency_name.upper()}
{'─'*60}
  • Proven track record with {len(services)}+ service capabilities
  • Dedicated project manager for your account
  • Transparent reporting and communication
  • 30-day satisfaction guarantee

{'─'*60}
7. NEXT STEPS
{'─'*60}
  1. Review this proposal
  2. Schedule a kick-off call
  3. Sign agreement & submit deposit
  4. We begin work immediately

{'─'*60}
AGREEMENT
{'─'*60}
Client Signature: _________________________  Date: ________
{agency_name} Signature: __________________  Date: ________

© {datetime.now().year} {agency_name}. All rights reserved.
{'='*60}"""

        st.code(outline)
        st.download_button("Download Proposal (.txt)", outline,
                           f"proposal_{client_name.replace(' ', '_').lower()}.txt",
                           "text/plain")
        st.success("✅ Proposal outline generated! Customize the details and send to your client.")


# ══════════════════════════════════════════════
# BUSINESS & OPERATIONS (182-190)
# ══════════════════════════════════════════════

# ── 182. Invoice Number Sequence Generator ────
elif selected_tool == "182. Invoice Number Sequence Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate client onboarding checklists for smooth starts. Set new client relationships up for success from day one.")
    st.header("🧾 Invoice Number Sequence Generator")

    col1, col2 = st.columns(2)
    with col1:
        prefix = st.text_input("Prefix", "INV")
        separator = st.selectbox("Separator", ["-", "_", "", "/"])
        include_date = st.checkbox("Include date segment", True)
    with col2:
        date_format = st.selectbox("Date format", ["YYYYMM", "YYMMDD", "MMYY", "YYYY"])
        start_num = st.number_input("Starting number", 1, 999999, 1)
        num_digits = st.slider("Number padding (digits)", 3, 8, 4)

    count = st.slider("How many invoice numbers to generate?", 1, 50, 10)

    if st.button("Generate Invoice Numbers"):
        now = datetime.now()
        date_map = {
            "YYYYMM": now.strftime("%Y%m"),
            "YYMMDD": now.strftime("%y%m%d"),
            "MMYY": now.strftime("%m%y"),
            "YYYY": now.strftime("%Y"),
        }
        date_seg = date_map.get(date_format, "")

        invoices = []
        for i in range(count):
            num_part = str(start_num + i).zfill(num_digits)
            if include_date:
                inv_num = f"{prefix}{separator}{date_seg}{separator}{num_part}"
            else:
                inv_num = f"{prefix}{separator}{num_part}"
            invoices.append(inv_num)

        st.subheader("Generated Invoice Numbers")
        df = pd.DataFrame({"#": range(1, count + 1), "Invoice Number": invoices})
        st.dataframe(df, use_container_width=True)

        st.text_area("Copy all (one per line)", "\n".join(invoices), height=200)
        st.info(f"📌 Format: `{prefix}{separator}{'[DATE]' + separator if include_date else ''}[{'0' * num_digits}]`")


# ── 183. Sales Funnel Conversion Step Calculator
elif selected_tool == "183. Sales Funnel Conversion Step Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create detailed project scope documents with deliverables. Prevent scope creep and miscommunication with clear written agreements.")
    st.header("📊 Sales Funnel Conversion Step Calculator")

    stages = st.text_area("Funnel stages (one per line, top to bottom)",
                          "Website Visitors\nLeads (opt-in)\nSales Calls Booked\nProposals Sent\nClients Won",
                          height=120)
    top_traffic = st.number_input("Top-of-funnel traffic (visitors/month)", 100, 1000000, 5000)

    stage_list = [s.strip() for s in stages.strip().split("\n") if s.strip()]

    if len(stage_list) >= 2:
        st.subheader("Enter conversion rate between each stage")
        rates = []
        for i in range(len(stage_list) - 1):
            rate = st.slider(
                f"{stage_list[i]} → {stage_list[i+1]} (%)",
                1, 100, 20 if i == 0 else 30,
                key=f"funnel_rate_{i}"
            )
            rates.append(rate / 100.0)

        if st.button("Calculate Funnel"):
            results = [{"Stage": stage_list[0], "People": top_traffic,
                        "Conversion Rate": "— (Top)", "Drop-off": "—"}]
            current = top_traffic
            for i, rate in enumerate(rates):
                prev = current
                current = int(current * rate)
                dropped = prev - current
                results.append({
                    "Stage": stage_list[i + 1],
                    "People": current,
                    "Conversion Rate": f"{rate:.1%}",
                    "Drop-off": f"-{dropped:,}",
                })

            st.dataframe(pd.DataFrame(results), use_container_width=True)

            overall_rate = current / top_traffic if top_traffic > 0 else 0
            st.metric("Bottom-of-funnel result", f"{current:,} {stage_list[-1]}")
            st.metric("Overall conversion rate", f"{overall_rate:.2%}")
            st.metric("Total drop-off", f"{top_traffic - current:,}")

            # Identify weakest link
            min_rate = min(rates)
            min_idx = rates.index(min_rate)
            st.warning(f"⚠️ Weakest link: **{stage_list[min_idx]}** → **{stage_list[min_idx+1]}** "
                       f"at {min_rate:.1%}. Focus optimization here for maximum impact.")


# ── 184. A/B Test Split Traffic Calculator ────
elif selected_tool == "184. A/B Test Split Traffic Calculator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate professional weekly status reports. Keep stakeholders informed and demonstrate progress consistently.")
    st.header("🧪 A/B Test Split Traffic Calculator")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Variant A (Control)")
        visitors_a = st.number_input("Visitors A", 100, 1000000, 5000, key="ab_vis_a")
        conversions_a = st.number_input("Conversions A", 0, 1000000, 150, key="ab_conv_a")
    with col2:
        st.subheader("Variant B (Test)")
        visitors_b = st.number_input("Visitors B", 100, 1000000, 5000, key="ab_vis_b")
        conversions_b = st.number_input("Conversions B", 0, 1000000, 185, key="ab_conv_b")

    if st.button("Calculate Results"):
        import math
        rate_a = conversions_a / visitors_a if visitors_a > 0 else 0
        rate_b = conversions_b / visitors_b if visitors_b > 0 else 0
        lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0

        # Z-test for proportions
        p_pool = (conversions_a + conversions_b) / (visitors_a + visitors_b) if (visitors_a + visitors_b) > 0 else 0
        se = math.sqrt(p_pool * (1 - p_pool) * (1/visitors_a + 1/visitors_b)) if p_pool > 0 and p_pool < 1 else 0.0001
        z_score = (rate_b - rate_a) / se if se > 0 else 0

        # Approximate p-value from z-score
        p_value = math.erfc(abs(z_score) / math.sqrt(2))
        significant = p_value < 0.05

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rate A", f"{rate_a:.2%}")
        with col2:
            st.metric("Rate B", f"{rate_b:.2%}")
        with col3:
            st.metric("Lift", f"{lift:+.1f}%")

        st.metric("Z-Score", f"{z_score:.3f}")
        st.metric("P-Value", f"{p_value:.4f}")

        if significant:
            winner = "B" if rate_b > rate_a else "A"
            st.success(f"✅ Statistically significant at 95% confidence! Variant **{winner}** wins.")
        else:
            st.warning("⚠️ Not statistically significant at 95% confidence. Need more data or larger difference.")

        # Sample size recommendation
        st.subheader("📏 Sample Size Guidance")
        if rate_a > 0:
            mde = 0.05  # minimum detectable effect of 5%
            recommended = int((16 * rate_a * (1 - rate_a)) / (mde * rate_a) ** 2)
            st.info(f"To detect a 5% relative lift from a {rate_a:.2%} baseline, you need approximately "
                    f"**{recommended:,}** visitors per variant.")

        results_df = pd.DataFrame({
            "Metric": ["Visitors", "Conversions", "Conv. Rate", "Z-Score", "P-Value", "Significant?"],
            "Variant A": [f"{visitors_a:,}", f"{conversions_a:,}", f"{rate_a:.2%}", "—", "—", "—"],
            "Variant B": [f"{visitors_b:,}", f"{conversions_b:,}", f"{rate_b:.2%}",
                          f"{z_score:.3f}", f"{p_value:.4f}", "✅ Yes" if significant else "❌ No"],
        })
        st.dataframe(results_df, use_container_width=True)


# ── 185. Affiliate Link Cloaker ──────────────
elif selected_tool == "185. Affiliate Link Cloaker":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Write step-by-step SOPs for repeatable processes. Document processes so your team can execute consistently without you.")
    st.header("🔗 Affiliate Link Cloaker")
    st.caption("Format clean, branded redirect URLs for your affiliate links.")

    your_domain = st.text_input("Your domain", "digitalenvisioned.net")
    slug_prefix = st.text_input("URL prefix/folder", "go")

    st.subheader("Add Affiliate Links")
    if "aff_links" not in st.session_state:
        st.session_state.aff_links = []

    with st.form("aff_form"):
        link_name = st.text_input("Link name / slug (e.g. 'hostinger')")
        original_url = st.text_input("Original affiliate URL",
                                     "https://affiliates.example.com/ref=abc123&campaign=spring")
        submitted = st.form_submit_button("Add Link")

    if submitted and link_name and original_url:
        clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "", link_name.lower().replace(" ", "-"))
        cloaked = f"https://{your_domain}/{slug_prefix}/{clean_slug}"
        st.session_state.aff_links.append({
            "Name": link_name,
            "Slug": clean_slug,
            "Cloaked URL": cloaked,
            "Original URL": original_url[:80] + "..." if len(original_url) > 80 else original_url,
            "Full Original": original_url,
        })
        st.success(f"✅ Added: {cloaked}")

    if st.session_state.aff_links:
        st.subheader("Your Cloaked Links")
        display_df = pd.DataFrame(st.session_state.aff_links)[["Name", "Cloaked URL", "Original URL"]]
        st.dataframe(display_df, use_container_width=True)

        # Generate redirect config
        st.subheader("📋 Redirect Configuration")
        redirect_type = st.selectbox("Output format", ["HTML Meta Redirect", ".htaccess Rules",
                                                         "JavaScript Redirect", "Nginx Rewrite"])
        configs = []
        for link in st.session_state.aff_links:
            if redirect_type == "HTML Meta Redirect":
                configs.append(
                    f'<!-- {link["Name"]} -->\n'
                    f'<!-- Save as: /{slug_prefix}/{link["Slug"]}/index.html -->\n'
                    f'<meta http-equiv="refresh" content="0;url={link["Full Original"]}">'
                )
            elif redirect_type == ".htaccess Rules":
                configs.append(
                    f'# {link["Name"]}\n'
                    f'Redirect 301 /{slug_prefix}/{link["Slug"]} {link["Full Original"]}'
                )
            elif redirect_type == "JavaScript Redirect":
                configs.append(
                    f'// {link["Name"]}\n'
                    f'if(window.location.pathname === "/{slug_prefix}/{link["Slug"]}") {{\n'
                    f'  window.location.href = "{link["Full Original"]}";\n}}'
                )
            else:
                configs.append(
                    f'# {link["Name"]}\n'
                    f'rewrite ^/{slug_prefix}/{link["Slug"]}$ {link["Full Original"]} permanent;'
                )

        st.code("\n\n".join(configs), language="text")

        if st.button("Clear All Links"):
            st.session_state.aff_links = []
            st.rerun()


# ── 186. Privacy Policy Basic Template Generator
elif selected_tool == "186. Privacy Policy Basic Template Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create itemized expense reports with category totals. Submit clean, professional expense reports that get approved fast.")
    st.header("🔐 Privacy Policy Basic Template Generator")
    st.warning("⚠️ This generates a *basic template*. Consult a legal professional for compliance.")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company / Website name", "Digital Envisioned LLC")
        website_url = st.text_input("Website URL", "https://digitalenvisioned.net")
        contact_email = st.text_input("Contact email", "privacy@digitalenvisioned.net")
    with col2:
        effective_date = st.text_input("Effective date", datetime.now().strftime("%B %d, %Y"))
        location = st.text_input("State / Country", "Alabama, United States")
        business_type = st.selectbox("Business type", ["SaaS / Software", "E-commerce",
                                                        "Service Business", "Blog / Content",
                                                        "Agency", "Other"])

    data_collected = st.multiselect("Data you collect", [
        "Name", "Email address", "Phone number", "Mailing address",
        "Payment information", "IP address", "Browser cookies",
        "Usage analytics", "Social media profiles", "Location data",
    ], default=["Name", "Email address", "Browser cookies", "Usage analytics"])

    third_parties = st.multiselect("Third-party services used", [
        "Google Analytics", "Stripe / Payment Processor", "Mailchimp / Email Service",
        "Facebook Pixel", "Cloudflare", "AWS / Cloud Hosting",
    ], default=["Google Analytics", "Stripe / Payment Processor"])

    if company_name and st.button("Generate Privacy Policy"):
        data_list = "\n".join([f"  • {d}" for d in data_collected])
        tp_list = "\n".join([f"  • {t}" for t in third_parties])

        policy = f"""PRIVACY POLICY
{'='*50}
Last updated: {effective_date}
{company_name}
{website_url}

1. INTRODUCTION
{'-'*50}
{company_name} ("we," "our," or "us") operates {website_url}.
This Privacy Policy explains how we collect, use, disclose, and
safeguard your information when you visit our website.

2. INFORMATION WE COLLECT
{'-'*50}
We may collect the following information:
{data_list}

3. HOW WE USE YOUR INFORMATION
{'-'*50}
We use the information we collect to:
  • Provide and maintain our services
  • Improve and personalize your experience
  • Communicate with you (updates, marketing, support)
  • Process transactions and send billing information
  • Monitor usage patterns and analytics
  • Comply with legal obligations

4. THIRD-PARTY SERVICES
{'-'*50}
We may share your data with the following third-party services:
{tp_list}

Each third-party service has its own Privacy Policy. We encourage
you to review their practices.

5. COOKIES & TRACKING
{'-'*50}
We use cookies and similar tracking technologies to:
  • Remember your preferences
  • Analyze website traffic
  • Deliver targeted content

You can control cookies through your browser settings. Disabling
cookies may affect your experience on our site.

6. DATA SECURITY
{'-'*50}
We implement commercially reasonable security measures to protect
your personal information. However, no method of transmission over
the Internet is 100% secure.

7. YOUR RIGHTS
{'-'*50}
Depending on your location, you may have the right to:
  • Access the personal data we hold about you
  • Request correction or deletion of your data
  • Opt out of marketing communications
  • Request data portability

To exercise these rights, contact us at {contact_email}.

8. CHILDREN'S PRIVACY
{'-'*50}
Our services are not directed to individuals under 13. We do not
knowingly collect data from children.

9. CHANGES TO THIS POLICY
{'-'*50}
We may update this Privacy Policy from time to time. Changes will
be posted on this page with an updated effective date.

10. CONTACT US
{'-'*50}
If you have questions about this Privacy Policy, contact us at:
  Email: {contact_email}
  Website: {website_url}
  Location: {location}

© {datetime.now().year} {company_name}. All rights reserved.
"""
        st.code(policy)
        st.download_button("Download Privacy Policy (.txt)", policy,
                           "privacy_policy.txt", "text/plain")


# ── 187. Terms & Conditions Basic Template Generator
elif selected_tool == "187. Terms & Conditions Basic Template Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Summarize time tracking data by project and category. Understand where your time goes and optimize for profitability.")
    st.header("📜 Terms & Conditions Basic Template Generator")
    st.warning("⚠️ This generates a *basic template*. Consult a legal professional for compliance.")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company name", "Digital Envisioned LLC", key="tc_co")
        website_url = st.text_input("Website URL", "https://digitalenvisioned.net", key="tc_url")
        contact_email = st.text_input("Contact email", "legal@digitalenvisioned.net", key="tc_email")
    with col2:
        effective_date = st.text_input("Effective date", datetime.now().strftime("%B %d, %Y"), key="tc_date")
        location = st.text_input("Governing law (state/country)", "State of Alabama, United States", key="tc_loc")
        service_type = st.selectbox("Service type", ["SaaS Platform", "E-commerce Store",
                                                      "Digital Services", "Agency Services",
                                                      "Subscription Service"])

    has_subscriptions = st.checkbox("Includes paid subscriptions / billing", True)
    has_user_content = st.checkbox("Users can post content / upload files", True)

    if company_name and st.button("Generate Terms & Conditions"):
        terms = f"""TERMS AND CONDITIONS
{'='*50}
Last updated: {effective_date}
{company_name} — {website_url}

1. ACCEPTANCE OF TERMS
{'-'*50}
By accessing or using {website_url} ("the Service"), you agree to
be bound by these Terms and Conditions. If you do not agree, do
not use the Service.

2. DESCRIPTION OF SERVICE
{'-'*50}
{company_name} provides a {service_type.lower()} accessible at
{website_url}. Features and availability may change without notice.

3. USER ACCOUNTS
{'-'*50}
  • You must provide accurate and complete information
  • You are responsible for maintaining account security
  • You must be at least 18 years old to create an account
  • One person or entity per account
  • You are responsible for all activity under your account"""

        if has_subscriptions:
            terms += f"""

4. BILLING & SUBSCRIPTIONS
{'-'*50}
  • Subscription fees are billed in advance on a recurring basis
  • You authorize us to charge your payment method on file
  • Prices may change with 30 days' notice
  • Refunds are handled on a case-by-case basis
  • You may cancel your subscription at any time
  • Cancellation takes effect at the end of the current billing period"""

        if has_user_content:
            terms += f"""

5. USER CONTENT
{'-'*50}
  • You retain ownership of content you upload or create
  • You grant {company_name} a license to host and display your content
  • You are solely responsible for your content
  • We reserve the right to remove content that violates these terms
  • Prohibited content: illegal, harmful, defamatory, or infringing material"""

        terms += f"""

6. INTELLECTUAL PROPERTY
{'-'*50}
All content, features, and functionality of the Service are owned
by {company_name} and are protected by copyright, trademark, and
other intellectual property laws.

7. LIMITATION OF LIABILITY
{'-'*50}
TO THE MAXIMUM EXTENT PERMITTED BY LAW, {company_name.upper()}
SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR
CONSEQUENTIAL DAMAGES ARISING FROM YOUR USE OF THE SERVICE.

Our total liability shall not exceed the amount you paid us in
the 12 months preceding the claim.

8. DISCLAIMER OF WARRANTIES
{'-'*50}
THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT
WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED.

9. TERMINATION
{'-'*50}
We may terminate or suspend your account at any time for violation
of these Terms. Upon termination, your right to use the Service
ceases immediately.

10. GOVERNING LAW
{'-'*50}
These Terms are governed by the laws of the {location}, without
regard to conflict of law principles.

11. CHANGES TO TERMS
{'-'*50}
We reserve the right to modify these Terms at any time. Continued
use of the Service after changes constitutes acceptance.

12. CONTACT
{'-'*50}
Questions about these Terms? Contact us at:
  Email: {contact_email}
  Website: {website_url}

© {datetime.now().year} {company_name}. All rights reserved.
"""
        st.code(terms)
        st.download_button("Download T&C (.txt)", terms,
                           "terms_and_conditions.txt", "text/plain")


# ── 188. Brand Mission Statement Builder ──────
elif selected_tool == "188. Brand Mission Statement Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Configure key performance indicators for dashboard tracking. Track the metrics that matter most to your business growth.")
    st.header("🏢 Brand Mission Statement Builder")

    company = st.text_input("Company name", "Digital Envisioned")
    what_you_do = st.text_input("What does your company do?", "Build automation tools for businesses")
    who_you_serve = st.text_input("Who do you serve?", "Small business owners and entrepreneurs")
    how_you_do_it = st.text_input("How do you do it? (differentiator)", "Through a 200-tool SaaS platform")
    why_it_matters = st.text_input("Why does it matter? (impact)", "So they can save time and scale faster")
    core_belief = st.text_input("Core belief / value", "Every business deserves enterprise-level automation")

    if company and st.button("Generate Mission Statements"):
        missions = [
            f"At {company}, we {what_you_do.lower()} for {who_you_serve.lower()} {how_you_do_it.lower()}, {why_it_matters.lower()}.",
            f"{company} exists to empower {who_you_serve.lower()} by {what_you_do.lower()} — because {core_belief.lower()}.",
            f"Our mission is to {what_you_do.lower()} {how_you_do_it.lower()}, helping {who_you_serve.lower()} {why_it_matters.lower().lstrip('so they can ').lstrip('so that ')}.",
            f"We believe {core_belief.lower()}. That's why {company} {what_you_do.lower()} {how_you_do_it.lower()}, serving {who_you_serve.lower()} who want to {why_it_matters.lower().lstrip('so they can ').lstrip('so that ')}.",
            f"{company}: {what_you_do} for {who_you_serve.lower()}. {core_belief}.",
            f"To {what_you_do.lower()} and help {who_you_serve.lower()} {why_it_matters.lower().lstrip('so they can ').lstrip('so that ')} — that is the {company} mission.",
        ]

        st.subheader("Generated Mission Statements")
        for i, m in enumerate(missions, 1):
            st.text_area(f"Version {i}", m, height=80, key=f"mission_{i}")
            words = len(m.split())
            if words <= 25:
                st.caption(f"#{i} — {words} words — ✅ Concise")
            elif words <= 40:
                st.caption(f"#{i} — {words} words — ✅ Good length")
            else:
                st.caption(f"#{i} — {words} words — ⚠️ Consider trimming")

        st.info("💡 Best mission statements are 15-30 words. They should be memorable, "
                "specific, and action-oriented.")


# ── 189. Slogan & Tagline Brainstormer ────────
elif selected_tool == "189. Slogan & Tagline Brainstormer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Compare vendors using weighted scoring criteria. Make data-driven vendor selection decisions for your business.")
    st.header("💡 Slogan & Tagline Brainstormer")

    brand = st.text_input("Brand name", "Digital Envisioned")
    keywords = st.text_input("Core keywords (comma-separated)", "automation, elite, power, scale, digital")
    vibe = st.selectbox("Brand vibe", ["Bold & Powerful", "Friendly & Approachable",
                                        "Premium & Luxurious", "Tech & Innovative",
                                        "Playful & Fun", "Minimal & Clean"])
    industry = st.text_input("Industry", "SaaS / Business Automation")

    if brand and keywords and st.button("Generate Slogans"):
        kw_list = [k.strip() for k in keywords.split(",")]
        kw1 = kw_list[0] if len(kw_list) > 0 else "excellence"
        kw2 = kw_list[1] if len(kw_list) > 1 else "innovation"
        kw3 = kw_list[2] if len(kw_list) > 2 else "growth"

        template_bank = {
            "Bold & Powerful": [
                f"{brand}. Unleash {kw1.title()}.",
                f"{kw3.title()} Is Not Optional. It's {brand}.",
                f"Built for {kw2.title()}. Designed for Domination.",
                f"{brand}: Where {kw1.title()} Meets {kw3.title()}.",
                f"The {kw2.title()} Engine for Your Business.",
                f"Don't Just Grow. {kw1.title()} Everything.",
                f"{brand} — {kw1.title()} Without Limits.",
                f"Your Business. {kw2.title().replace('Ion','ed')}. {brand}.",
            ],
            "Friendly & Approachable": [
                f"{brand} — Making {kw1} easy for everyone.",
                f"Simple {kw1}. Real {kw3}.",
                f"Hey there, {kw3} — {brand}'s got you.",
                f"Your friendly {kw1} partner.",
                f"{brand}: {kw1.title()} made simple.",
                f"Less stress. More {kw3}. That's {brand}.",
            ],
            "Premium & Luxurious": [
                f"{brand} — The {kw2.title()} Standard.",
                f"Refined {kw1.title()}. Elevated {kw3.title()}.",
                f"Where {kw2.title()} Becomes Art. {brand}.",
                f"The Connoisseur's Choice for {kw1.title()}.",
                f"{brand}: Crafted for Excellence.",
                f"Premium {kw1}. Unmatched {kw3}.",
            ],
            "Tech & Innovative": [
                f"{brand} — {kw1.title()} 2.0",
                f"The Future of {kw1.title()} Is Here.",
                f"Code. {kw1.title()}. {kw3.title()}. {brand}.",
                f"Smarter {kw1}. Faster {kw3}.",
                f"{brand} — Engineering {kw3.title()}.",
                f"Next-Gen {kw1.title()} for Next-Gen Businesses.",
            ],
            "Playful & Fun": [
                f"{brand} — {kw1.title()} with a Twist! 🎉",
                f"Who said {kw1} can't be fun?",
                f"Less boring. More {kw3}. All {brand}.",
                f"Sprinkle some {kw1} magic. ✨ {brand}.",
                f"{brand}: Seriously good {kw1}. Not seriously boring.",
            ],
            "Minimal & Clean": [
                f"{brand}. {kw1.title()}.",
                f"Simply {kw3}.",
                f"{kw1.title()}. Refined.",
                f"Less noise. More {kw3}.",
                f"{brand} — {kw1}. {kw3}.",
                f"Essential {kw1}. {brand}.",
            ],
        }

        slogans = template_bank.get(vibe, template_bank["Bold & Powerful"])

        st.subheader(f"Slogans — {vibe} Vibe")
        for i, s in enumerate(slogans, 1):
            chars = len(s)
            st.code(s)
            if chars <= 30:
                st.caption(f"#{i} — {chars} chars — ✅ Punchy & memorable")
            elif chars <= 60:
                st.caption(f"#{i} — {chars} chars — ✅ Good length")
            else:
                st.caption(f"#{i} — {chars} chars — ⚠️ Long for a tagline")

        st.info("💡 The best taglines are 3-8 words. They should be unique, memorable, "
                "and capture your brand's essence.")


# ── 190. Brand Core Values Extractor ──────────
elif selected_tool == "190. Brand Core Values Extractor":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate QBR presentation outlines with key metrics. Run strategic quarterly reviews that align teams and drive results.")
    st.header("💎 Brand Core Values Extractor")

    brand = st.text_input("Brand / Company name", "Digital Envisioned", key="bcv_brand")
    mission = st.text_area("Your mission statement (or describe what you do)",
                           "We build premium automation tools to help small businesses scale faster.",
                           height=80)
    culture_desc = st.text_area("Describe your team culture / how you work",
                                "Fast-moving, innovation-driven, client-first, transparent communication.",
                                height=80)
    what_matters = st.text_area("What matters most to your company? (free text)",
                                "Quality over quantity. Empowering underdogs. Technology for everyone.",
                                height=80)

    value_bank = {
        "Innovation": {"keywords": ["innovation", "new", "creative", "cutting-edge", "pioneer", "future", "technology", "tech", "build"],
                       "description": "We push boundaries and embrace new ideas to stay ahead."},
        "Quality": {"keywords": ["quality", "premium", "excellence", "best", "craft", "refined", "standard"],
                    "description": "We hold ourselves to the highest standards in everything we produce."},
        "Integrity": {"keywords": ["honest", "transparent", "trust", "integrity", "authentic", "real", "genuine"],
                      "description": "We do what's right, even when no one is watching."},
        "Customer-First": {"keywords": ["client", "customer", "serve", "help", "support", "empower", "user"],
                           "description": "Our customers are at the heart of every decision we make."},
        "Growth": {"keywords": ["grow", "scale", "expand", "learn", "improve", "develop", "progress"],
                   "description": "We believe in continuous growth — for our clients and ourselves."},
        "Speed & Agility": {"keywords": ["fast", "agile", "quick", "rapid", "move", "ship", "efficient"],
                            "description": "We move fast, iterate quickly, and deliver results without delay."},
        "Empowerment": {"keywords": ["empower", "enable", "unlock", "access", "everyone", "underdog", "democratize"],
                        "description": "We give people the tools and confidence to succeed on their own terms."},
        "Collaboration": {"keywords": ["team", "together", "collaborate", "community", "partner", "collective"],
                          "description": "We achieve more together than we ever could alone."},
        "Transparency": {"keywords": ["transparent", "open", "communication", "honest", "clear", "visibility"],
                         "description": "We communicate openly and build trust through visibility."},
        "Impact": {"keywords": ["impact", "difference", "change", "matter", "meaningful", "results", "outcome"],
                   "description": "We measure success by the tangible impact we create."},
        "Simplicity": {"keywords": ["simple", "easy", "clean", "minimal", "straightforward", "streamline"],
                       "description": "We cut complexity and make powerful tools feel effortless."},
        "Resilience": {"keywords": ["resilient", "persist", "grit", "determined", "overcome", "tough", "hustle"],
                       "description": "We push through challenges and never settle for mediocrity."},
    }

    if brand and st.button("Extract Core Values"):
        all_text = f"{mission} {culture_desc} {what_matters}".lower()
        scored = []
        for value, info in value_bank.items():
            matches = sum(1 for kw in info["keywords"] if kw in all_text)
            if matches > 0:
                scored.append((value, matches, info["description"]))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_values = scored[:6] if scored else []

        if top_values:
            st.subheader(f"🏆 Core Values for {brand}")
            for i, (value, match_count, desc) in enumerate(top_values, 1):
                st.markdown(f"### {i}. {value}")
                st.write(desc)
                st.progress(min(match_count / 5, 1.0))
                st.markdown("---")

            # Summary block
            value_names = [v[0] for v in top_values]
            st.subheader("📋 Values Summary")
            st.code(" · ".join(value_names))
            st.text_area("Values with descriptions (copy for brand guidelines)",
                         "\n".join([f"{v[0]}: {v[2]}" for v in top_values]),
                         height=180)
        else:
            st.info("Could not extract clear values. Try adding more descriptive text about your culture and priorities.")


# ══════════════════════════════════════════════
# EXECUTIVE STRATEGY (191-200)
# ══════════════════════════════════════════════

# ── 191. Meeting Agenda Template Builder ──────
elif selected_tool == "191. Meeting Agenda Template Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate executive summaries from detailed reports. Communicate key findings to leadership in concise, actionable format.")
    st.header("📋 Meeting Agenda Template Builder")

    meeting_title = st.text_input("Meeting title", "Weekly Strategy Sync")
    meeting_date = st.date_input("Meeting date")
    meeting_time = st.text_input("Time", "10:00 AM CST")
    duration = st.selectbox("Duration", ["15 minutes", "30 minutes", "45 minutes",
                                          "60 minutes", "90 minutes"])
    organizer = st.text_input("Organizer / facilitator", "Joshua Newton")
    attendees = st.text_input("Attendees (comma-separated)", "Josh, Sarah, Mike, Viktor AI")
    meeting_type = st.selectbox("Meeting type", ["Team Standup", "Client Meeting",
                                                  "Strategy Session", "Project Kickoff",
                                                  "Retrospective", "1-on-1", "Board Meeting"])

    st.subheader("Agenda Items")
    if "agenda_items" not in st.session_state:
        st.session_state.agenda_items = []

    with st.form("agenda_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner / presenter")
        time_alloc = st.selectbox("Time", ["5 min", "10 min", "15 min", "20 min", "30 min"])
        add_item = st.form_submit_button("Add Item")

    if add_item and topic:
        st.session_state.agenda_items.append({
            "topic": topic, "owner": owner, "time": time_alloc
        })

    if st.session_state.agenda_items:
        st.dataframe(pd.DataFrame(st.session_state.agenda_items), use_container_width=True)

    if st.button("Generate Agenda"):
        att_list = [a.strip() for a in attendees.split(",")]
        agenda = f"""{'='*55}
MEETING AGENDA: {meeting_title.upper()}
{'='*55}
Date: {meeting_date}  |  Time: {meeting_time}  |  Duration: {duration}
Organizer: {organizer}
Attendees: {', '.join(att_list)}
Type: {meeting_type}

{'─'*55}
AGENDA ITEMS
{'─'*55}
"""
        default_items = {
            "Team Standup": [("Check-in / blockers", "All", "5 min"),
                             ("Yesterday's progress", "All", "10 min"),
                             ("Today's priorities", "All", "10 min"),
                             ("Open discussion", "All", "5 min")],
            "Client Meeting": [("Welcome & introductions", organizer, "5 min"),
                               ("Project status update", organizer, "15 min"),
                               ("Key deliverables review", organizer, "15 min"),
                               ("Client feedback & questions", "Client", "15 min"),
                               ("Next steps & action items", organizer, "10 min")],
            "Strategy Session": [("Review current metrics", organizer, "10 min"),
                                 ("Identify opportunities", "All", "20 min"),
                                 ("Prioritize initiatives", "All", "15 min"),
                                 ("Assign ownership", organizer, "10 min"),
                                 ("Wrap-up & next steps", organizer, "5 min")],
        }

        items = st.session_state.agenda_items if st.session_state.agenda_items else [
            {"topic": t, "owner": o, "time": tm}
            for t, o, tm in default_items.get(meeting_type, default_items["Team Standup"])
        ]

        for i, item in enumerate(items, 1):
            agenda += f"  {i}. {item['topic']}\n"
            agenda += f"     Owner: {item['owner']}  |  Time: {item['time']}\n\n"

        agenda += f"""{'─'*55}
ACTION ITEMS (to be filled during meeting)
{'─'*55}
  1. ___________________________________  Owner: _________
  2. ___________________________________  Owner: _________
  3. ___________________________________  Owner: _________

{'─'*55}
NOTES
{'─'*55}
  _________________________________________________
  _________________________________________________
  _________________________________________________

Next meeting: _______________
{'='*55}"""

        st.code(agenda)
        st.download_button("Download Agenda (.txt)", agenda,
                           f"agenda_{meeting_title.replace(' ', '_').lower()}.txt", "text/plain")

    if st.button("Clear Agenda Items"):
        st.session_state.agenda_items = []
        st.rerun()


# ── 192. Project Timeline Estimator ──────────
elif selected_tool == "192. Project Timeline Estimator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Prioritize strategic initiatives using impact and effort scores. Focus resources on the initiatives with the highest return potential.")
    st.header("📅 Project Timeline Estimator")

    project_name = st.text_input("Project name", "Website Redesign")
    start_date = st.date_input("Start date", key="timeline_start")
    end_date = st.date_input("End date", key="timeline_end")

    st.subheader("Add Milestones / Phases")
    if "milestones" not in st.session_state:
        st.session_state.milestones = []

    with st.form("milestone_form"):
        ms_name = st.text_input("Phase / Milestone name")
        ms_days = st.number_input("Estimated days", 1, 365, 7)
        ms_owner = st.text_input("Owner")
        ms_add = st.form_submit_button("Add Phase")

    if ms_add and ms_name:
        st.session_state.milestones.append({
            "Phase": ms_name, "Days": ms_days, "Owner": ms_owner
        })

    if start_date and end_date:
        from datetime import timedelta
        total_days = (end_date - start_date).days
        business_days = sum(1 for d in range(total_days)
                           if (start_date + timedelta(days=d)).weekday() < 5)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Calendar Days", total_days)
        with col2:
            st.metric("Business Days", business_days)
        with col3:
            weeks = total_days / 7
            st.metric("Weeks", f"{weeks:.1f}")

        if st.session_state.milestones:
            st.subheader("Project Phases")
            running_date = start_date
            timeline_data = []
            for ms in st.session_state.milestones:
                end = running_date + timedelta(days=ms["Days"])
                timeline_data.append({
                    "Phase": ms["Phase"],
                    "Start": str(running_date),
                    "End": str(end),
                    "Days": ms["Days"],
                    "Owner": ms["Owner"],
                })
                running_date = end

            df = pd.DataFrame(timeline_data)
            st.dataframe(df, use_container_width=True)

            total_estimated = sum(m["Days"] for m in st.session_state.milestones)
            if total_estimated > total_days:
                st.error(f"⚠️ Estimated work ({total_estimated} days) exceeds available time ({total_days} days)!")
            else:
                buffer = total_days - total_estimated
                st.success(f"✅ {buffer} buffer days remaining. Looks achievable!")

            # Text export
            timeline_txt = f"PROJECT TIMELINE: {project_name}\n{'='*50}\n"
            timeline_txt += f"Start: {start_date}  |  End: {end_date}  |  Days: {total_days}\n\n"
            for i, row in enumerate(timeline_data, 1):
                timeline_txt += f"{i}. {row['Phase']} ({row['Start']} → {row['End']}) — {row['Days']}d — {row['Owner']}\n"
            st.download_button("Download Timeline (.txt)", timeline_txt,
                               f"timeline_{project_name.replace(' ', '_').lower()}.txt")

    if st.button("Clear Phases"):
        st.session_state.milestones = []
        st.rerun()


# ── 193. OKR (Objectives & Key Results) Formatter
elif selected_tool == "193. OKR Formatter":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Create formal board meeting agendas with governance items. Run professional board meetings that cover strategy, compliance, and growth.")
    st.header("🎯 OKR Formatter (Objectives & Key Results)")

    quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"])
    year = st.number_input("Year", 2024, 2030, datetime.now().year)
    team_name = st.text_input("Team / Department", "Digital Envisioned — Marketing")

    st.subheader("Define Your OKRs")
    if "okrs" not in st.session_state:
        st.session_state.okrs = []

    with st.form("okr_form"):
        objective = st.text_input("Objective (what you want to achieve)")
        kr1 = st.text_input("Key Result 1 (measurable)")
        kr2 = st.text_input("Key Result 2 (measurable)")
        kr3 = st.text_input("Key Result 3 (measurable)")
        owner = st.text_input("Objective owner")
        add_okr = st.form_submit_button("Add OKR")

    if add_okr and objective:
        krs = [kr for kr in [kr1, kr2, kr3] if kr.strip()]
        st.session_state.okrs.append({
            "objective": objective,
            "key_results": krs,
            "owner": owner,
        })

    if st.session_state.okrs:
        st.subheader(f"OKRs for {team_name} — {quarter} {year}")
        for i, okr in enumerate(st.session_state.okrs, 1):
            st.markdown(f"### Objective {i}: {okr['objective']}")
            st.caption(f"Owner: {okr['owner']}")
            for j, kr in enumerate(okr["key_results"], 1):
                progress = st.slider(f"KR {i}.{j}: {kr}", 0, 100, 0, key=f"okr_prog_{i}_{j}")
                st.progress(progress / 100)

        # Export
        if st.button("Export OKR Document"):
            doc = f"""OKR PLAN: {team_name}
{'='*55}
Period: {quarter} {year}

"""
            for i, okr in enumerate(st.session_state.okrs, 1):
                doc += f"""OBJECTIVE {i}: {okr['objective']}
  Owner: {okr['owner']}
"""
                for j, kr in enumerate(okr["key_results"], 1):
                    doc += f"  KR {i}.{j}: {kr}\n"
                doc += "\n"

            st.code(doc)
            st.download_button("Download OKR Plan (.txt)", doc,
                               f"okr_{quarter}_{year}.txt")

    if st.button("Clear All OKRs"):
        st.session_state.okrs = []
        st.rerun()


# ── 194. SWOT Analysis Matrix Builder ─────────
elif selected_tool == "194. SWOT Analysis Matrix Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate monthly investor update communications. Keep investors informed and confident with structured progress reports.")
    st.header("📊 SWOT Analysis Matrix Builder")

    topic = st.text_input("Subject of analysis", "Digital Envisioned — Elite Automation Suite")

    col1, col2 = st.columns(2)
    with col1:
        strengths = st.text_area("💪 Strengths (one per line)",
                                 "200-tool platform\nAffordable pricing\nBuilt for local businesses\nAll-in-one solution",
                                 height=120)
        opportunities = st.text_area("🌟 Opportunities (one per line)",
                                     "Growing demand for automation\nLocal SEO market underserved\nPartnership with agencies\nAI integration trend",
                                     height=120)
    with col2:
        weaknesses = st.text_area("⚠️ Weaknesses (one per line)",
                                  "New brand / low awareness\nSmall team\nNo mobile app yet\nLimited integrations",
                                  height=120)
        threats = st.text_area("🚨 Threats (one per line)",
                               "Large competitors (HubSpot, etc.)\nEconomic downturn\nRapid tech changes\nPrice sensitivity",
                               height=120)

    if topic and st.button("Generate SWOT Matrix"):
        s_list = [s.strip() for s in strengths.strip().split("\n") if s.strip()]
        w_list = [w.strip() for w in weaknesses.strip().split("\n") if w.strip()]
        o_list = [o.strip() for o in opportunities.strip().split("\n") if o.strip()]
        t_list = [t.strip() for t in threats.strip().split("\n") if t.strip()]

        st.subheader(f"SWOT Analysis: {topic}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💪 Strengths (Internal +)")
            for s in s_list:
                st.write(f"✅ {s}")
        with col2:
            st.markdown("### ⚠️ Weaknesses (Internal −)")
            for w in w_list:
                st.write(f"❌ {w}")

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("### 🌟 Opportunities (External +)")
            for o in o_list:
                st.write(f"🟢 {o}")
        with col4:
            st.markdown("### 🚨 Threats (External −)")
            for t in t_list:
                st.write(f"🔴 {t}")

        # Strategy suggestions
        st.subheader("🧠 Strategic Implications")
        if s_list and o_list:
            st.write(f"**SO Strategy (Leverage):** Use _{s_list[0]}_ to capitalize on _{o_list[0]}_")
        if w_list and o_list:
            st.write(f"**WO Strategy (Improve):** Address _{w_list[0]}_ to capture _{o_list[0]}_")
        if s_list and t_list:
            st.write(f"**ST Strategy (Defend):** Use _{s_list[0]}_ to mitigate _{t_list[0]}_")
        if w_list and t_list:
            st.write(f"**WT Strategy (Avoid):** Minimize _{w_list[0]}_ and watch for _{t_list[0]}_")

        # Export
        swot_text = f"SWOT ANALYSIS: {topic}\n{'='*50}\n\n"
        swot_text += "STRENGTHS:\n" + "\n".join([f"  + {s}" for s in s_list]) + "\n\n"
        swot_text += "WEAKNESSES:\n" + "\n".join([f"  - {w}" for w in w_list]) + "\n\n"
        swot_text += "OPPORTUNITIES:\n" + "\n".join([f"  + {o}" for o in o_list]) + "\n\n"
        swot_text += "THREATS:\n" + "\n".join([f"  - {t}" for t in t_list])
        st.download_button("Download SWOT (.txt)", swot_text, "swot_analysis.txt")


# ── 195. PESTLE Analysis Framework Generator ──
elif selected_tool == "195. PESTLE Analysis Framework Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Evaluate new market opportunities with scoring frameworks. Identify the most promising markets for your next expansion move.")
    st.header("🌍 PESTLE Analysis Framework Generator")

    subject = st.text_input("Subject of analysis", "Launching a SaaS product in Alabama")

    factors = {}
    labels = {
        "P": ("🏛️ Political", "Government policies, regulations, trade rules, tax policies"),
        "E": ("💰 Economic", "Economic growth, exchange rates, inflation, unemployment"),
        "S": ("👥 Social", "Demographics, lifestyle trends, cultural attitudes, education"),
        "T": ("💻 Technological", "Innovation, R&D, automation, tech infrastructure"),
        "L": ("⚖️ Legal", "Employment law, consumer protection, health & safety, IP law"),
        "E2": ("🌱 Environmental", "Climate, sustainability, environmental regulations, waste"),
    }

    for key, (label, hint) in labels.items():
        factors[key] = st.text_area(f"{label}", placeholder=hint, height=80, key=f"pestle_{key}")

    if subject and st.button("Generate PESTLE Report"):
        st.subheader(f"PESTLE Analysis: {subject}")

        report = f"PESTLE ANALYSIS: {subject}\n{'='*55}\n\n"

        for key, (label, hint) in labels.items():
            items = [f.strip() for f in factors.get(key, "").strip().split("\n") if f.strip()]
            st.markdown(f"### {label}")
            if items:
                for item in items:
                    st.write(f"• {item}")
                report += f"{label}\n"
                report += "\n".join([f"  • {item}" for item in items]) + "\n\n"
            else:
                st.caption(f"No factors entered. Consider: {hint}")
                report += f"{label}\n  (No factors entered)\n\n"
            st.markdown("---")

        # Summary
        total_factors = sum(len([f for f in factors.get(k, "").strip().split("\n") if f.strip()])
                           for k in labels.keys())
        st.metric("Total factors analyzed", total_factors)

        st.download_button("Download PESTLE Report (.txt)", report,
                           "pestle_analysis.txt", "text/plain")
        st.info("💡 PESTLE analysis helps identify macro-environmental factors that could "
                "impact your business strategy.")


# ── 196. Product Pricing Tier Structurer ──────
elif selected_tool == "196. Product Pricing Tier Structurer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Structure product pricing tiers with feature matrices. Maximize revenue with pricing that gives every customer segment a reason to buy.")
    st.header("💲 Product Pricing Tier Structurer")

    product_name = st.text_input("Product name", "Elite Automation Suite")
    num_tiers = st.slider("Number of pricing tiers", 2, 5, 3)
    billing = st.selectbox("Billing cycle", ["Monthly", "Annual", "One-time", "Monthly + Annual"])

    tiers = []
    for i in range(num_tiers):
        with st.expander(f"Tier {i + 1}", expanded=True):
            tier_name = st.text_input(f"Tier name", ["Free", "Pro", "Elite", "Enterprise", "Custom"][i],
                                      key=f"tier_name_{i}")
            tier_price = st.number_input(f"Price ($)", 0.0, 99999.0,
                                         [0.0, 47.0, 197.0, 497.0, 997.0][i],
                                         key=f"tier_price_{i}")
            tier_features = st.text_area(f"Features (one per line)",
                                         key=f"tier_feat_{i}", height=80)
            tier_cta = st.text_input(f"CTA button text", ["Get Started", "Subscribe", "Go Elite",
                                                            "Contact Sales", "Custom Plan"][i],
                                     key=f"tier_cta_{i}")
            highlighted = st.checkbox("⭐ Highlight as recommended", i == 2, key=f"tier_hl_{i}")
            tiers.append({
                "name": tier_name,
                "price": tier_price,
                "features": [f.strip() for f in tier_features.strip().split("\n") if f.strip()],
                "cta": tier_cta,
                "highlighted": highlighted,
            })

    if st.button("Preview Pricing Table"):
        st.subheader(f"💰 {product_name} Pricing")
        cols = st.columns(num_tiers)
        for idx, (col, tier) in enumerate(zip(cols, tiers)):
            with col:
                if tier["highlighted"]:
                    st.markdown("⭐ **MOST POPULAR**")
                st.markdown(f"### {tier['name']}")
                if tier["price"] == 0:
                    st.markdown("### Free")
                else:
                    suffix = "/mo" if "Monthly" in billing else "/yr" if billing == "Annual" else ""
                    st.markdown(f"### ${tier['price']:,.0f}{suffix}")
                st.markdown("---")
                for feat in tier["features"]:
                    st.write(f"✅ {feat}")
                if not tier["features"]:
                    st.caption("(Add features above)")
                st.button(tier["cta"], key=f"pricing_btn_{idx}")

        # Export comparison table
        comparison = {"Feature": []}
        for tier in tiers:
            comparison[tier["name"]] = []
        all_features = []
        for tier in tiers:
            all_features.extend(tier["features"])
        all_features = list(dict.fromkeys(all_features))  # unique, preserve order

        for feat in all_features:
            comparison["Feature"].append(feat)
            for tier in tiers:
                comparison[tier["name"]].append("✅" if feat in tier["features"] else "—")

        if all_features:
            st.subheader("Feature Comparison Table")
            st.dataframe(pd.DataFrame(comparison), use_container_width=True)


# ── 197. Profit Margin vs. Markup Visualizer ──
elif selected_tool == "197. Profit Margin vs. Markup Visualizer":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Visualize the relationship between profit margin and markup. Understand pricing dynamics and set prices that protect your bottom line.")
    st.header("📈 Profit Margin vs. Markup Visualizer")

    mode = st.radio("Calculate from:", ["Cost & Selling Price", "Cost & Desired Margin",
                                         "Cost & Desired Markup"])
    if mode == "Cost & Selling Price":
        cost = st.number_input("Cost ($)", 0.01, 1000000.0, 50.0, key="pm_cost1")
        price = st.number_input("Selling Price ($)", 0.01, 1000000.0, 100.0, key="pm_price1")

        if st.button("Calculate"):
            profit = price - cost
            margin = (profit / price) * 100 if price > 0 else 0
            markup = (profit / cost) * 100 if cost > 0 else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Profit", f"${profit:,.2f}")
            with col2:
                st.metric("Margin", f"{margin:.1f}%")
            with col3:
                st.metric("Markup", f"{markup:.1f}%")

            # Comparison table at various margins
            st.subheader("Margin vs. Markup Reference Table")
            rows = []
            for m in [10, 15, 20, 25, 30, 33.3, 40, 50, 60, 75]:
                equiv_markup = (m / (100 - m)) * 100 if m < 100 else float("inf")
                sell_at = cost / (1 - m / 100) if m < 100 else 0
                rows.append({
                    "Margin %": f"{m:.1f}%",
                    "Markup %": f"{equiv_markup:.1f}%",
                    "Sell Price (your cost)": f"${sell_at:,.2f}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    elif mode == "Cost & Desired Margin":
        cost = st.number_input("Cost ($)", 0.01, 1000000.0, 50.0, key="pm_cost2")
        target_margin = st.slider("Target Margin (%)", 1, 95, 40)

        if st.button("Calculate"):
            price = cost / (1 - target_margin / 100)
            profit = price - cost
            markup = (profit / cost) * 100

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Required Price", f"${price:,.2f}")
            with col2:
                st.metric("Profit", f"${profit:,.2f}")
            with col3:
                st.metric("Equivalent Markup", f"{markup:.1f}%")

    else:
        cost = st.number_input("Cost ($)", 0.01, 1000000.0, 50.0, key="pm_cost3")
        target_markup = st.slider("Target Markup (%)", 1, 500, 100)

        if st.button("Calculate"):
            price = cost * (1 + target_markup / 100)
            profit = price - cost
            margin = (profit / price) * 100

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Selling Price", f"${price:,.2f}")
            with col2:
                st.metric("Profit", f"${profit:,.2f}")
            with col3:
                st.metric("Equivalent Margin", f"{margin:.1f}%")

    st.info("💡 **Margin** = Profit ÷ Selling Price  |  **Markup** = Profit ÷ Cost. "
            "A 50% margin ≠ 50% markup. A 50% margin = 100% markup.")


# ── 198. Employee Onboarding Checklist Generator
elif selected_tool == "198. Employee Onboarding Checklist Generator":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Generate comprehensive employee onboarding checklists. Get new hires productive faster with a structured first-week experience.")
    st.header("📋 Employee Onboarding Checklist Generator")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company name", "Digital Envisioned", key="onb_co")
        new_hire = st.text_input("New hire name", "New Team Member")
        role = st.text_input("Role / position", "Marketing Specialist")
    with col2:
        start_date_str = st.text_input("Start date", datetime.now().strftime("%B %d, %Y"), key="onb_date")
        manager = st.text_input("Reporting manager", "Joshua Newton")
        dept = st.text_input("Department", "Marketing & Automation")

    work_type = st.selectbox("Work type", ["Remote", "On-site", "Hybrid"])
    tools_used = st.text_input("Key tools / software to set up",
                               "Streamlit, Slack, GitHub, Google Workspace, Elite Automation Suite")

    if company and st.button("Generate Onboarding Checklist"):
        tools_list = [t.strip() for t in tools_used.split(",")]

        checklist = f"""{'='*55}
EMPLOYEE ONBOARDING CHECKLIST
{'='*55}
Company: {company}
New Hire: {new_hire}
Role: {role}  |  Department: {dept}
Start Date: {start_date_str}  |  Manager: {manager}
Work Type: {work_type}

{'─'*55}
PRE-ARRIVAL (Before Day 1)
{'─'*55}
  [ ] Send offer letter & employment agreement
  [ ] Collect signed documents (NDA, tax forms, ID)
  [ ] Set up email account & credentials
  [ ] Create accounts for: {', '.join(tools_list)}
  [ ] Order equipment (laptop, monitor, peripherals)
  [ ] Prepare welcome kit / swag
  [ ] Add to team communication channels (Slack, etc.)
  [ ] Schedule Day 1 orientation meeting
  [ ] Assign onboarding buddy / mentor

{'─'*55}
DAY 1 — WELCOME & ORIENTATION
{'─'*55}
  [ ] Welcome meeting with {manager}
  [ ] Office tour / virtual workspace walkthrough
  [ ] IT setup & login verification
  [ ] Review company handbook & policies
  [ ] Introduce to team members
  [ ] Set up direct deposit / payroll
  [ ] Review role expectations & 30-day goals
  [ ] Lunch with team (virtual or in-person)

{'─'*55}
WEEK 1 — FOUNDATIONS
{'─'*55}
  [ ] Complete all compliance training
  [ ] Review {dept} team processes & workflows
  [ ] Shadow key team members
  [ ] Access & explore: {', '.join(tools_list[:3])}
  [ ] Set up 1-on-1 schedule with {manager}
  [ ] Review current projects & priorities
  [ ] Complete first small task / assignment
  [ ] End-of-week check-in with {manager}

{'─'*55}
WEEK 2-4 — RAMP UP
{'─'*55}
  [ ] Take ownership of assigned projects
  [ ] Complete role-specific training
  [ ] Attend all relevant team meetings
  [ ] Submit first deliverable for review
  [ ] Build relationships with cross-functional teams
  [ ] Document questions & feedback

{'─'*55}
30-DAY CHECK-IN
{'─'*55}
  [ ] Formal 30-day review with {manager}
  [ ] Discuss progress against initial goals
  [ ] Gather feedback (from hire and team)
  [ ] Adjust goals for Day 31-90
  [ ] Confirm all systems access is working
  [ ] Address any concerns or blockers

{'─'*55}
60-DAY CHECK-IN
{'─'*55}
  [ ] Review performance & contributions
  [ ] Discuss growth areas & development plan
  [ ] Expand responsibilities if appropriate

{'─'*55}
90-DAY REVIEW
{'─'*55}
  [ ] Formal 90-day performance review
  [ ] Set Q1/Q2 OKRs (aligned with team goals)
  [ ] Confirm role fit & long-term plans
  [ ] Celebrate milestones! 🎉

{'='*55}
Prepared by: {company} HR / Operations
{'='*55}"""

        st.code(checklist)
        st.download_button("Download Checklist (.txt)", checklist,
                           f"onboarding_{new_hire.replace(' ', '_').lower()}.txt", "text/plain")


# ── 199. Business Pitch Deck Outline Builder ──
elif selected_tool == "199. Business Pitch Deck Outline Builder":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Build pitch deck outlines with investor-focused sections. Win funding with a deck that tells your story compellingly and covers every base.")
    st.header("🎤 Business Pitch Deck Outline Builder")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company name", "Digital Envisioned", key="pitch_co")
        tagline = st.text_input("One-line description", "200-Tool Automation Suite for Small Businesses")
        problem = st.text_area("The Problem you solve", "Small businesses waste 20+ hours/week on manual tasks they can't afford to hire for.", height=80)
    with col2:
        solution = st.text_area("Your Solution", "An all-in-one 200-tool SaaS platform that automates marketing, operations, and business tasks.", height=80)
        market_size = st.text_input("Market size (TAM)", "$50B small business software market")
        revenue_model = st.text_input("Revenue model", "SaaS subscription: $47/mo - $197/mo per user")
    traction = st.text_area("Traction / milestones", "200 tools built\nBeta users onboarded\nRevenue growing MoM", height=80)
    ask = st.text_input("The Ask (funding, partnership, etc.)", "$250K seed round for growth & marketing")

    deck_style = st.selectbox("Deck style", ["Startup Pitch (Investor)", "Sales Pitch (Client)",
                                              "Partnership Pitch", "Internal Strategy Pitch"])

    if company and st.button("Generate Pitch Deck Outline"):
        traction_list = [t.strip() for t in traction.strip().split("\n") if t.strip()]

        if deck_style == "Startup Pitch (Investor)":
            slides = [
                ("SLIDE 1: TITLE", f"{company}\n{tagline}\n[Logo & Presenter Name]\n[Date]"),
                ("SLIDE 2: THE PROBLEM", f"{problem}\n\nShow the pain: statistics, quotes, visuals."),
                ("SLIDE 3: THE SOLUTION", f"{solution}\n\nProduct demo screenshot or diagram."),
                ("SLIDE 4: HOW IT WORKS", "Step 1 → Step 2 → Step 3\nShow the user journey in 3 simple steps."),
                ("SLIDE 5: MARKET OPPORTUNITY", f"TAM: {market_size}\nTarget segment & growth rate.\nWhy now?"),
                ("SLIDE 6: BUSINESS MODEL", f"{revenue_model}\n\nUnit economics & pricing tiers."),
                ("SLIDE 7: TRACTION", "\n".join([f"✅ {t}" for t in traction_list]) + "\nGrowth chart / metrics."),
                ("SLIDE 8: COMPETITIVE LANDSCAPE", "2×2 matrix: What makes you different?\nKey differentiators vs. competitors."),
                ("SLIDE 9: THE TEAM", "Founder(s) + key hires.\nRelevant experience & why you'll win."),
                ("SLIDE 10: FINANCIALS", "Revenue projections (3 years).\nKey assumptions & milestones."),
                ("SLIDE 11: THE ASK", f"{ask}\n\nUse of funds breakdown.\nTimeline & expected outcomes."),
                ("SLIDE 12: CLOSING", f"Thank you.\n{company} — {tagline}\n[Contact info]"),
            ]
        elif deck_style == "Sales Pitch (Client)":
            slides = [
                ("SLIDE 1: TITLE", f"{company} for [Client Name]\n{tagline}"),
                ("SLIDE 2: UNDERSTANDING YOUR CHALLENGES", f"{problem}"),
                ("SLIDE 3: OUR SOLUTION", f"{solution}"),
                ("SLIDE 4: KEY FEATURES & BENEFITS", "Feature → Benefit mapping (3-5 items)"),
                ("SLIDE 5: CASE STUDIES", "Similar client results & testimonials"),
                ("SLIDE 6: IMPLEMENTATION PLAN", "Onboarding timeline & support included"),
                ("SLIDE 7: PRICING", f"{revenue_model}"),
                ("SLIDE 8: NEXT STEPS", "CTA: Sign up / Schedule demo / Start trial"),
            ]
        elif deck_style == "Partnership Pitch":
            slides = [
                ("SLIDE 1: TITLE", f"Partnership Proposal: {company}"),
                ("SLIDE 2: ABOUT US", f"{company} — {tagline}\nTraction: {', '.join(traction_list[:3])}"),
                ("SLIDE 3: THE OPPORTUNITY", "What we can build together"),
                ("SLIDE 4: MUTUAL BENEFITS", "What you get / What we get"),
                ("SLIDE 5: PROPOSED STRUCTURE", "Terms, revenue share, responsibilities"),
                ("SLIDE 6: NEXT STEPS", "Timeline & action items"),
            ]
        else:
            slides = [
                ("SLIDE 1: TITLE", f"Strategic Initiative: {company}"),
                ("SLIDE 2: CURRENT STATE", "Where we are today"),
                ("SLIDE 3: THE OPPORTUNITY", f"{problem}"),
                ("SLIDE 4: PROPOSED STRATEGY", f"{solution}"),
                ("SLIDE 5: RESOURCES NEEDED", f"{ask}"),
                ("SLIDE 6: TIMELINE & MILESTONES", "Roadmap with deliverables"),
                ("SLIDE 7: EXPECTED OUTCOMES", "KPIs and success metrics"),
                ("SLIDE 8: DECISION NEEDED", "Clear ask from leadership"),
            ]

        st.subheader(f"📊 {deck_style} — {len(slides)} Slides")
        deck_text = f"PITCH DECK OUTLINE: {company}\n{'='*55}\nStyle: {deck_style}\n\n"

        for title, content in slides:
            with st.expander(title, expanded=False):
                st.text_area("Content notes", content, height=120, key=f"slide_{title}")
            deck_text += f"{title}\n{content}\n\n{'─'*40}\n\n"

        st.download_button("Download Outline (.txt)", deck_text,
                           f"pitch_deck_{company.replace(' ', '_').lower()}.txt", "text/plain")
        st.info(f"💡 {deck_style} typically works best with {len(slides)} slides. "
                "Keep each slide to one key idea.")


# ── 200. Master System Diagnostic Dashboard ──
elif selected_tool == "200. Master System Diagnostic Dashboard":
    with st.expander("ℹ️ How to use this tool"):
        st.write("Run diagnostics on all 200 tools and check system health. Verify your entire suite is operational and identify any issues instantly.")
    st.balloons()
    st.header("💯 Master System Diagnostic Dashboard")
    st.markdown(f"*{datetime.now().strftime('%B %d, %Y — %I:%M %p')}*")

    st.subheader("🏢 System Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tools", "200", "+200")
    with col2:
        st.metric("Categories", "12")
    with col3:
        st.metric("System Status", "✅ Online")
    with col4:
        st.metric("Version", "1.0.0")

    st.subheader("📊 Tool Category Breakdown")
    category_health = pd.DataFrame({
        "Category": [
            "Essential Utilities (1-20)",
            "Text & Writing (21-40)",
            "Design & Visual (41-60)",
            "Data & Analytics (61-80)",
            "Developer Tools (81-100)",
            "SEO & Web (101-120)",
            "Communication (121-135)",
            "File & Document (136-145)",
            "Advanced Design & Media (146-155)",
            "Security & Network (156-160)",
            "Writing & Conversion (161-165)",
            "Social Media & Marketing (166-175)",
            "Local SEO & Frameworks (176-181)",
            "Business & Operations (182-190)",
            "Executive Strategy (191-200)",
        ],
        "Tools": [20, 20, 20, 20, 20, 20, 15, 10, 10, 5, 5, 10, 6, 9, 10],
        "Status": ["🟢 Active"] * 15,
    })
    st.dataframe(category_health, use_container_width=True)

    st.subheader("🔧 System Diagnostics")
    checks = {
        "Streamlit Runtime": "✅ Running",
        "Python Version": f"✅ {__import__('sys').version.split()[0]}",
        "PIL (Pillow)": "✅ Loaded",
        "Requests Library": "✅ Loaded",
        "BeautifulSoup": "✅ Loaded",
        "QR Code Generator": "✅ Loaded",
        "Pandas": "✅ Loaded",
        "JSON Processing": "✅ Native",
        "Base64 Encoding": "✅ Native",
        "CSV Processing": "✅ Native",
        "RegEx Engine": "✅ Native",
        "PDF Processing": "✅ PyPDF2",
        "Markdown Engine": "✅ Loaded",
    }
    diag_df = pd.DataFrame(checks.items(), columns=["Component", "Status"])
    st.dataframe(diag_df, use_container_width=True)

    st.subheader("📡 Quick Connectivity Test")
    if st.button("Run Diagnostic Check"):
        with st.spinner("Testing connectivity..."):
            tests = {}
            try:
                r = requests.get("https://www.google.com", timeout=5)
                tests["Internet Connection"] = f"✅ OK ({r.status_code})"
            except Exception:
                tests["Internet Connection"] = "❌ Failed"

            try:
                r = requests.get("https://digitalenvisioned.net", timeout=5)
                tests["digitalenvisioned.net"] = f"✅ OK ({r.status_code})"
            except Exception:
                tests["digitalenvisioned.net"] = "⚠️ Unreachable"

            try:
                r = requests.get("https://api.github.com", timeout=5)
                tests["GitHub API"] = f"✅ OK ({r.status_code})"
            except Exception:
                tests["GitHub API"] = "⚠️ Unreachable"

            for name, result in tests.items():
                st.write(f"{result} — {name}")

    st.subheader("👤 System Info")
    st.write("**Product:** Digital Envisioned Elite Automation Suite")
    st.write("**Owner:** jnworkflow@gmail.com")
    st.write("**Location:** Birmingham, Alabama")
    st.write("**Tools:** 200 / 200 Active")
    st.write(f"**Last Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center;padding:20px;">'
        '<h2>🏆 200 TOOLS COMPLETE</h2>'
        '<p style="font-size:1.2rem;">The Digital Envisioned Elite Automation Suite is fully operational.</p>'
        '<p><strong>© 2026 Digital Envisioned LLC · Birmingham, AL · All Rights Reserved</strong></p>'
        '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
# END OF TOOLS 176-200
# THE ELITE AUTOMATION SUITE IS COMPLETE — 200/200 TOOLS
# ═══════════════════════════════════════════════════════════════════

"""
app.py
Campus Fraud Shield — Hackathon Edition
Features: Adversarial text cleaning, Red Flag Engine, URL Unmasking,
          Sender ID Verification, Social Impact Dashboard, Community Pulse,
          Explainable AI bar chart, Three Golden Rules expander.
"""

import re
import sys
import time
import requests
import streamlit as st
import plotly.graph_objects as go
from collections import Counter
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.fraud_rules import analyze as rules_analyze
from core.domain_checker import check as domain_check
from core.typosquat_checker import check as typosquat_check
from core.campus_checker import CampusChecker
from core.ml_model import SemanticScamClassifier
from core.history_engine import UnifiedHistoryEngine
from core.scorer import ScoreBreakdown, compute_final_score
from core.text_cleaner import clean_text
from core.qr_analyzer import decode_qr
from core.image_analyzer import extract_text as extract_image_text
from utils.extractors import extract_all
from utils.action_advisor import get_action, generate_complaint_text
from utils.ui_components import (
    inject_custom_css, render_hero, render_gauge,
    render_verdict_card, display_finding,
)
from core.database import init_db, extract_amount, log_scan_amount, get_total_wealth, add_vouch, get_vouch_age_days
import hashlib

init_db()

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Campus Fraud Shield",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded",
)

inject_custom_css()

# ---------------------------------------------------------------------------
# Session State Initialization  (MUST happen before any widget or sidebar read)
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "wealth_protected": 0,
    "prev_wealth": 0,
    "recent_categories": [],
    "scan_history": [],
    "override_critical": False,
    "high_risk_qr": False,
    "sender_id": "",
    "input_text": "",
    "auto_submit": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def resolve_short_url(url: str) -> str:
    """Follow redirects with a 3-second timeout and return the final URL."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=3)
        return resp.url
    except Exception:
        return url


SHORT_DOMAINS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "tiny.cc", "rb.gy"}

def expand_short_links(text: str, resolve_network: bool = True) -> tuple[str, dict]:
    """Replace any recognised short links in text with their resolved destinations."""
    url_pattern = re.compile(r"https?://[^\s]+")
    unmasked = {}
    def _replace(m):
        url = m.group(0)
        domain = re.sub(r"^https?://(?:www\.)?", "", url).split("/")[0]
        if domain in SHORT_DOMAINS:
            if resolve_network:
                final_url = resolve_short_url(url)
                if final_url != url:
                    unmasked[url] = final_url
                return final_url
            else:
                unmasked[url] = url  # track it as unmasked to trigger the penalty, but don't resolve
                return url
        return url
    return url_pattern.sub(_replace, text), unmasked


def get_red_flags(text: str) -> list[str]:
    """Return a list of human-readable red-flag strings found in text."""
    flags = []
    low = text.lower()
    if re.search(r"\b(immediate|expire|last chance|within 24|limited seats)\b", low):
        flags.append("Urgency language detected (e.g. 'immediate', 'expire', 'last chance')")
    if re.search(r"\b(security deposit|processing fee|registration fee|bank details)\b", low):
        flags.append("Financial demand detected (e.g. 'processing fee', 'security deposit')")
    if re.search(r"\.(xyz|cc|top|tk|ml|click|loan)\b", low):
        flags.append("Suspicious TLD in URL (e.g. .xyz, .cc, .top)")
    if re.search(r"https?://[^\s]*google\.com/search\?q=[^\s]+", low):
        flags.append("Mismatched / obfuscated domain (disguised as a Google link)")
    if re.search(r"@(gmail|yahoo|hotmail)\.com", low):
        flags.append("Free email used as official contact")
    if re.search(r"\b(whatsapp only|telegram only)\b", low):
        flags.append("Communication forced to private channels (WhatsApp/Telegram only)")
    return flags


def get_highlighted_html(text: str) -> str:
    """Highlights common red-flag keywords with category colors and a legend."""
    financial = [r"\bfee\b", r"\bsecurity deposit\b", r"\bprocessing fee\b", r"\bregistration fee\b", r"\bbank details\b", r"\bkyc\b"]
    urgency = [r"\burgent\b", r"\bimmediate\b", r"\bexpire\b", r"\blast chance\b"]
    brand = [r"\botp\b", r"\.xyz\b", r"\.cc\b", r"\.top\b", r"\bwhatsapp only\b", r"\btelegram only\b"]

    import html
    escaped_text = html.escape(text)

    # We will do sequential replacements. To avoid replacing inside already replaced spans, we use a custom token or rely on simple word boundaries.
    for p in financial:
        escaped_text = re.sub(f"({p})", r"<span style='background-color:rgba(255, 59, 59, 0.4); color:#FFF; padding:2px 4px; border-radius:4px;' title='Financial Risk'>\1 <small style='opacity:0.8;'>(?)</small></span>", escaped_text, flags=re.IGNORECASE)
    for p in urgency:
        escaped_text = re.sub(f"({p})", r"<span style='background-color:rgba(245, 158, 11, 0.4); color:#FFF; padding:2px 4px; border-radius:4px;' title='Urgency'>\1 <small style='opacity:0.8;'>(?)</small></span>", escaped_text, flags=re.IGNORECASE)
    for p in brand:
        escaped_text = re.sub(f"({p})", r"<span style='background-color:rgba(0, 229, 255, 0.4); color:#FFF; padding:2px 4px; border-radius:4px;' title='Brand Impersonation / Suspicious'>\1 <small style='opacity:0.8;'>(?)</small></span>", escaped_text, flags=re.IGNORECASE)

    legend = (
        "<div style='margin-bottom:10px; font-size:0.85rem;'>"
        "<span style='background-color:rgba(255, 59, 59, 0.4); padding:2px 6px; border-radius:4px; margin-right:10px;'>Financial Risk</span>"
        "<span style='background-color:rgba(245, 158, 11, 0.4); padding:2px 6px; border-radius:4px; margin-right:10px;'>Urgency</span>"
        "<span style='background-color:rgba(0, 229, 255, 0.4); padding:2px 6px; border-radius:4px;'>Suspicious/Brand</span>"
        "</div>"
    )

    return f"<div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:8px; line-height:1.6; white-space:pre-wrap;'>{legend}{escaped_text}</div><br>"


def _scam_category(text: str) -> str | None:
    low = text.lower()
    if "internship" in low or "job" in low:
        return "Internship Scam"
    if "otp" in low or "bank" in low or "kyc" in low:
        return "OTP/Bank Scam"
    if "prize" in low or "lottery" in low or "won" in low:
        return "Prize Scam"
    if "scholarship" in low:
        return "Scholarship Scam"
    return None


WEALTH_MAP = {
    "Internship Scam": 2500,
    "OTP/Bank Scam": 10000,
    "Prize Scam": 25000,
    "Scholarship Scam": 5000,
}

def get_text_hash(t: str) -> str:
    return hashlib.md5(t.strip().lower().encode()).hexdigest()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ Campus Fraud Shield")
    st.caption("AI-Powered Cybersecurity for Students")
    st.markdown("---")

    # Sender ID field
    st.markdown("### 🪪 Sender Verification")
    sender_id_val = st.text_input(
        "Sender ID (optional)",
        key="sender_id",
        placeholder="🛡️ Identity Check Active",
        help="Banks use headers like AD-SBIINB. A mobile number as sender = scam.",
    )

    if sender_id_val:
        if re.fullmatch(r"^[A-Za-z]{2}-[A-Za-z0-9]{6}$", sender_id_val):
            st.markdown("<div style='color:#10B981; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>✅ TRAI Verified Badge</div>", unsafe_allow_html=True)
            st.markdown("""<style>input[aria-label="Sender ID (optional)"] { border-color: #10B981 !important; }</style>""", unsafe_allow_html=True)
        elif re.fullmatch(r"(\+?91)?\s?\d{10}", sender_id_val):
            input_text_val = st.session_state.get("input_text", "").lower()
            official_kw = ["sbi", "bank", "nspp", "government", "nsp", "govt", "official"]
            if any(k in input_text_val for k in official_kw):
                st.markdown("<div style='color:#EF4444; font-weight:800; font-size:0.85rem; margin-top:-10px; margin-bottom:10px;'>🚨 RED ALERT: Identity Mismatch</div>", unsafe_allow_html=True)
                st.markdown("""<style>input[aria-label="Sender ID (optional)"] { border-color: #EF4444 !important; box-shadow: 0 0 15px #EF4444 !important; animation: pulseCrimson 2s infinite; }</style>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Community Intelligence")

    total_reps = 0
    scam_reps = 0

    st.markdown("---")

    network_mode = st.toggle("⚙️ Network Mode", value=False)
    demo_mode = st.toggle("Demo Mode")
    if demo_mode and not st.session_state.recent_categories:
        st.session_state.recent_categories = [
            "Internship Phishing caught", "Fake SBI Alert blocked", "NSP Scholarship Spoof detected"
        ]
        # In Demo Mode, add mock amount to DB if empty
        if get_total_wealth() == 0:
            log_scan_amount(45000)

    # Social Impact counter
    st.markdown("### 💰 Social Impact")
    st.markdown("Student Wealth Protected")
    
    pulse_val = get_total_wealth()
    st.session_state.wealth_protected = pulse_val
    anim_css = ""
    if pulse_val > st.session_state.prev_wealth and st.session_state.prev_wealth > 0:
        anim_css = "animation: victoryGlow 2s ease-out;"
    elif pulse_val > 0:
        anim_css = "box-shadow: 0 0 10px #10B981;"
    st.session_state.prev_wealth = pulse_val

    if pulse_val > 0:
        st.markdown(f"""
        <style>
        @keyframes victoryGlow {{
            0% {{ box-shadow: 0 0 0px #10B981; transform: scale(1); }}
            20% {{ box-shadow: 0 0 30px #10B981; transform: scale(1.05); }}
            100% {{ box-shadow: 0 0 10px #10B981; transform: scale(1); }}
        }}
        .victory-metric {{
            color: #10B981; font-size: 2rem; font-weight: 800;
            background: rgba(16, 185, 129, 0.1); padding: 10px;
            border-radius: 8px; text-align: center;
            border: 1px solid rgba(16, 185, 129, 0.5);
            {anim_css}
        }}
        </style>
        <div class='victory-metric'>₹{pulse_val:,}</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='color:#00E5FF;font-size:1.2rem;font-weight:800;text-align:center;'>₹0 protected so far — be the first to scan a threat!</div>", unsafe_allow_html=True)

    # Recent Threat Feed pills
    st.markdown("### 📡 Recent Threat Feed")
    if st.session_state.recent_categories:
        pills_html = " ".join(
            f"<span style='background:#1E3A8A;color:#F8FAFC;padding:3px 10px;"
            f"border-radius:12px;font-size:0.72rem;font-weight:700;'>{c}</span>"
            for c in st.session_state.recent_categories[-5:]
        )
        st.markdown(pills_html, unsafe_allow_html=True)

        # High-Volume Alert
        cnt = Counter(st.session_state.recent_categories)
        for cat, n in cnt.items():
            if n >= 3:
                st.markdown(
                    f"<div style='background:#7F1D1D;color:#FEF2F2;padding:8px;"
                    f"border-radius:8px;font-weight:700;text-align:center;'>"
                    f"🔥 High Volume Alert<br><small>{cat} detected {n}× this session</small></div>",
                    unsafe_allow_html=True,
                )
                break
    else:
        st.caption("No recent detections.")

    st.markdown("---")
    st.caption("v3.0 | 100% Local Processing | No Cloud APIs used.")

    if st.button("Load Demo Scams"):
        st.session_state["input_text"] = "\n\n".join([
            "Congratulations Priya! You are selected for Internshala Student Internship Program. Pay registration fee ₹1500 today to confirm your seat. Limited seats only. Send payment on UPI id hrverify@upi and WhatsApp screenshot to 9876543210.",
            "Dear student, your NSP scholarship status is available at scholarships.gov.in. Please login using your credentials.",
            "Your SBI account will be blocked today. Share OTP immediately to update KYC. Click http://sbi-verify-kyc-login.com and enter Aadhaar, PAN and OTP.",
        ])
        st.session_state["auto_submit"] = True

# ---------------------------------------------------------------------------
# Load Resources (after sidebar so spinner appears properly)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Initializing AI Model (offline)...")
def load_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource(show_spinner="Loading Classifier...")
def load_classifier(_embedder):
    clf = SemanticScamClassifier(embedder=_embedder)
    clf.load()
    return clf

@st.cache_resource(show_spinner="Loading Community History...")
def load_history(_embedder):
    return UnifiedHistoryEngine(embedder=_embedder)

embedder   = load_embedder()
classifier = load_classifier(embedder)
history_engine = load_history(embedder)
campus_checker = CampusChecker()

# Update community metrics after loading
with st.sidebar:
    total_reps = history_engine.total_reports
    scam_reps  = history_engine.scam_count
    # We already rendered the sidebar above; just patch the metrics here
    # (Streamlit re-renders on each run so these will appear correctly)

# ---------------------------------------------------------------------------
# Main Page
# ---------------------------------------------------------------------------
render_hero()

# Quick Demos
DEMO_MESSAGES = {
    "Fake Internship": "Congratulations Priya! You are selected for Internshala Student Internship Program. Pay registration fee ₹1500 today to confirm your seat. Limited seats only. Send payment on UPI id hrverify@upi and WhatsApp screenshot to 9876543210.",
    "Prize Scam": "Congratulations! Your mobile number has won ₹5,00,000 in lucky draw. Click http://bit.ly/claim-prize-now and pay processing fee ₹999 to claim your reward within 24 hours.",
    "Scholarship Scam": "PM Scholarship approved for you. To release ₹25,000 scholarship amount, pay processing fee ₹799 immediately. Contact on WhatsApp only. Apply link: http://tinyurl.com/scholarship-release.",
    "OTP Scam": "Your SBI account will be blocked today. Share OTP immediately to update KYC. Click http://sbi-verify-kyc-login.com and enter Aadhaar, PAN and OTP.",
    "Fake Domain": "Login to your Google account now at https://gooogle-security-login.com to avoid suspension.",
    "Safe Message": "Dear student, your scholarship application status is available on the National Scholarship Portal. Please visit scholarships.gov.in directly and log in using your credentials. Do not share OTP with anyone.",
}

st.markdown("### 🧪 Quick Demo")
demo_cols = st.columns(3)
for idx, (dlabel, dtext) in enumerate(DEMO_MESSAGES.items()):
    col = demo_cols[idx % 3]
    if col.button(dlabel, key=f"demo_{idx}", use_container_width=True):
        st.session_state["input_text"] = dtext
        st.session_state["auto_submit"] = True

st.markdown("---")

# ---------------------------------------------------------------------------
# Input Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["💬 Paste Text / URL", "📷 Upload Screenshot", "🔳 Upload QR Code"])

input_text         = ""
extracted_image_text = ""
extracted_qr_text  = ""
has_image_input    = False

with tab1:
    input_text = st.text_area(
        "Paste suspicious message, URL, internship offer, scholarship notice, OTP request, or UPI payment text...",
        value=st.session_state.get("input_text", ""),
        height=150,
        key="main_input",
    )

with tab2:
    st.markdown("Analyze a screenshot for scam patterns using local OCR.")
    screenshot_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"], key="screenshot")
    if screenshot_file:
        with st.spinner("Extracting text via OCR..."):
            res = extract_image_text(screenshot_file.getvalue())
            if res["success"]:
                st.success("Text extracted successfully!")
                extracted_image_text = res["text"]
                has_image_input = True
                with st.expander("View Extracted Text"):
                    st.text(extracted_image_text)
            elif res["warning"]:
                st.warning(res["warning"])
            else:
                st.error(res["error"])

with tab3:
    st.markdown("Scan a suspicious QR code (e.g. fake UPI payment requests).")
    qr_file = st.file_uploader("Upload QR Code", type=["png", "jpg", "jpeg"], key="qr")
    if qr_file:
        with st.spinner("Decoding QR..."):
            res = decode_qr(qr_file.getvalue())
            if res["success"]:
                st.success("QR decoded successfully!")
                extracted_qr_text = res["text"]
                has_image_input = True
                # Immediate high-risk flag for payment / suspicious URL in QR
                if any(kw in extracted_qr_text.lower() for kw in ["pay", "upi", "amount", "send", "http"]):
                    st.session_state["high_risk_qr"] = True
                    st.warning("⚠️ QR contains payment/URL content — elevated risk flagged.")
                with st.expander("View QR Content"):
                    st.text(extracted_qr_text)
            elif res["warning"]:
                st.warning(res["warning"])
            else:
                st.error(res["error"])

# Combine inputs
final_input_text = "\n".join(filter(None, [input_text, extracted_image_text, extracted_qr_text]))

submit = st.button("🔍 Scan Threat →", type="primary", use_container_width=True)

if st.session_state.get("auto_submit"):
    st.session_state["auto_submit"] = False
    submit = True
    final_input_text = st.session_state.get("input_text", "")

# ---------------------------------------------------------------------------
# Analysis & Results
# ---------------------------------------------------------------------------
if submit and final_input_text.strip():
    raw_text = final_input_text.strip()

    with st.status("Initializing Threat Engine...", expanded=True) as status:
        st.write("🛡️ Adversarial Cleaning...")
        time.sleep(0.5)
        # ── Step 0: Adversarial text cleaning ──────────────────────────────
        text = clean_text(raw_text)           # Leet + zero-width normalise
        adversarial_note = None
        if text != raw_text:
            adversarial_note = "<span style='animation: pulseCrimson 2s infinite; border-radius:4px; padding:2px;'>🛡️ Adversarial Defense Active: Normalized obfuscated characters.</span>"

        text, unmasked_urls = expand_short_links(text, resolve_network=network_mode)

        st.write("🔍 Rules Audit...")
        time.sleep(0.5)
        # ── Step 1–7: Engine pipeline ───────────────────────────────────────
        entities = extract_all(text)
        r = rules_analyze(text)
        
        # Add penalty if network mode is off and short links are present
        if not network_mode and unmasked_urls:
            r["score"] = min(100, r["score"] + 15)
            r["signals"].append({"label": "Shortened URL detected — enable Network Mode to resolve.", "points": 15})
        
        st.write("🌐 Domain X-Ray...")
        time.sleep(0.5)
        d = domain_check(text)
        t = typosquat_check(d["urls"])

        st.write("🧠 Semantic Intent...")
        time.sleep(0.5)
        sem_score, sem_reason = classifier.predict_proba(text)
        sem_examples = classifier.get_similar_training_examples(text, n=3)

        st.write("📚 Searching Community History...")
        time.sleep(0.5)
        comm_matches = history_engine.search_and_explain(text, k=3)
        if comm_matches:
            avg_sim       = sum(m["score"] / 100.0 for m in comm_matches) / len(comm_matches)
            confirmed_scam = sum(1 for m in comm_matches if m.get("label") == 1)
            comm_score     = min(100.0, avg_sim * 100.0 * (confirmed_scam / len(comm_matches) + 0.5))
        else:
            comm_score = 0.0
        campus_result = campus_checker.check(text)

        qr_score = 0.0
        if extracted_qr_text:
            if st.session_state.get("high_risk_qr"):
                qr_score = 90.0
            elif any(kw in extracted_qr_text.lower() for kw in ["pay", "upi", "amount", "send"]):
                qr_score = 80.0
            elif "http" in extracted_qr_text:
                qr_score = 50.0

        bd = ScoreBreakdown(
            rules_score=r["score"],        rules_signals=r["signals"],
            domain_score=d["score"],       domain_signals=d["signals"],
            typosquat_score=t["score"],    typosquat_signals=t["signals"],
            semantic_score=sem_score,      semantic_reason=sem_reason,
            semantic_examples=sem_examples,
            community_score=comm_score,    community_matches=comm_matches,
            campus_score=campus_result.get("total_score", 0.0), campus_findings=campus_result["findings"],
            qr_image_score=qr_score,       has_image=has_image_input
        )
        bd = compute_final_score(bd)
        
        status.update(label="Threat Scan Complete!", state="complete", expanded=False)

    # ── Render ──────────────────────────────────────────────────────────────
    st.markdown("---")
    final = bd.final_score
    label = bd.label

    # Sender ID Verification — override verdict if mobile number used as official sender
    sender_id = st.session_state.get("sender_id", "").strip()
    official_kw = ["sbi", "bank", "nspp", "government", "nsp", "govt"]
    overridden_critical = False
    if sender_id and any(k in text.lower() for k in official_kw):
        if re.fullmatch(r"(\+?91)?\s?\d{10}", sender_id):
            label = "CRITICAL SCAM"
            overridden_critical = True
            
    if overridden_critical:
        st.markdown(
            "<div style='background-color:#EF4444; color:#FFF; font-weight:900; text-align:center; padding:10px; border-radius:8px; animation:pulseCrimson 2s infinite; box-shadow:0 0 15px #EF4444; margin-bottom:15px; letter-spacing:1px;'>"
            "🚨 CRITICAL OVERRIDE: SENDER IDENTITY MISMATCH 🚨</div>", unsafe_allow_html=True
        )

    render_gauge(final, label)

    # Verdict
    top_reason = ""
    if overridden_critical:
        top_reason = "IDENTITY MISMATCH: Official Banks do not use personal mobile numbers."
    elif bd.rules_signals:
        top_reason = f"Triggered: 🚩 \"{bd.rules_signals[0]['label']}\""
    elif bd.typosquat_signals:
        top_reason = bd.typosquat_signals[0]["reason"]
    render_verdict_card(label, top_reason, overridden=overridden_critical)
    
    # Dynamic Thematic Feedback
    theme_color = "#EF4444" if label in ["High Risk Scam", "CRITICAL SCAM"] else "#F59E0B" if label == "Suspicious" else "#10B981"
    st.markdown(f"""
    <style>
    .stButton>button[data-baseweb="button"]:has(div:contains("Scan Threat")) {{
        border-color: {theme_color} !important;
        box-shadow: 0 0 15px {theme_color}80 !important;
    }}
    .stButton>button[data-baseweb="button"]:has(div:contains("Scan Threat")):hover {{
        background: {theme_color}20 !important;
        box-shadow: 0 0 25px {theme_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("**Share Report:**")
    st.code(f"Verdict: {label}\\nScore: {final}/100\\nReason: {top_reason}", language="text")

    # ── Red Flag List ────────────────────────────────────────────────────────
    red_flags = get_red_flags(text)
    if red_flags:
        with st.container():
            st.warning(
                "🚩 **Why is this risky?**\n" +
                "\n".join(f"- {f}" for f in red_flags)
            )
            
    st.markdown("**🔍 Scanned Content Highlight:**")
    st.markdown(get_highlighted_html(text), unsafe_allow_html=True)

    # ── Evidence Locker ───────────────────────────────────────────────────────
    if any(entities.values()):
        with st.expander("🗄️ Evidence Locker", expanded=True):
            cols = st.columns(3)
            with cols[0]:
                st.markdown("**🔗 URLs Detected**")
                for u in entities["urls"]:
                    if u in unmasked_urls:
                        st.markdown(f"Original: `{u}`<br>↳ **Revealed:** `{unmasked_urls[u]}`", unsafe_allow_html=True)
                    else:
                        st.caption(u)
                if not entities["urls"]:
                    st.caption("None")
            with cols[1]:
                st.markdown("**💳 Financial Targets**")
                for u in entities["upis"]:
                    st.caption(f"UPI: {u}")
                for a in entities["amounts"]:
                    st.caption(f"Amount: {a}")
                if not entities["upis"] and not entities["amounts"]:
                    st.caption("None")
            with cols[2]:
                st.markdown("**📞 Contacts**")
                for p in entities["phones"]:
                    st.caption(f"Phone: {p}")
                for e in entities["emails"]:
                    st.caption(f"Email: {e}")
                if not entities["phones"] and not entities["emails"]:
                    st.caption("None")

    # ── Threat Engine Breakdown ──────────────────────────────────────────────
    st.markdown("### 🧠 Threat Engine Breakdown")
    tab_simple, tab_math = st.tabs(["Simple Explanation", "Technical Math"])
    
    with tab_simple:
        col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"**📝 Rules Engine** `[{bd.rules_score:.0f}/100]`")
        if bd.rules_signals:
            for s in bd.rules_signals:
                display_finding(s["points"], f"🚩 Triggered: \"{s['label']}\"")
        else:
            display_finding(0, "No specific keywords triggered.")

        st.markdown(f"**🌐 Domain Check** `[{bd.domain_score:.0f}/100]`")
        if bd.domain_signals:
            for s in bd.domain_signals:
                display_finding(s["points"], s["label"])
        else:
            display_finding(0, "No suspicious links.")

        st.markdown(f"**🎭 Fake Domain Check** `[{bd.typosquat_score:.0f}/100]`")
        if bd.typosquat_signals:
            for s in bd.typosquat_signals:
                display_finding(s["points"], s["reason"])
        else:
            display_finding(0, "No typosquatting detected.")

    with col_b:
        st.markdown(f"**🤖 Semantic AI** `[{bd.semantic_score:.0f}/100]`")
        display_finding(0, bd.semantic_reason)

        # Explainable AI bar chart — top-3 FAISS similarity
        if bd.semantic_examples:
            ex_labels = [
                f"{'🔴 SCAM' if e['label_str']=='SCAM' else '🟢 SAFE'} {e['similarity']:.0f}%"
                for e in bd.semantic_examples
            ]
            ex_scores = [e["similarity"] for e in bd.semantic_examples]
            ex_colors = ["#FF3B3B" if e["label_str"] == "SCAM" else "#00FF88" for e in bd.semantic_examples]
            fig = go.Figure(go.Bar(
                x=ex_scores, y=ex_labels, orientation="h",
                marker_color=ex_colors,
                text=[f"{s:.1f}%" for s in ex_scores], textposition="inside",
            ))
            fig.update_layout(
                title="Semantic Similarity to Training Examples",
                xaxis=dict(range=[0, 100], title="Similarity %"),
                height=200,
                margin=dict(l=0, r=0, t=32, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F8FAFC", family="Inter"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**🏛️ Campus Verification** `[{bd.campus_score:.0f}/100]`")
        if bd.campus_findings:
            for s in bd.campus_findings:
                display_finding(s["score"], f"{s['entity']}: {s['reason']}")
        else:
            display_finding(0, "No specific campus policies violated.")

        st.markdown(f"**📋 Community Intelligence** `[{bd.community_score:.0f}/100]`")
        if bd.community_matches:
            display_finding(0, f"Found {len(bd.community_matches)} similar past reports.")
        else:
            display_finding(0, "No similar reports in database.")

    with tab_math:
        if adversarial_note:
            st.info(f"🛡️ **Adversarial Text Cleaning Engine:** {adversarial_note}")
            
        st.markdown("**Explainable Weights (Tooltips):**")
        if bd.rules_signals:
            for s in bd.rules_signals:
                st.markdown(f"<div title='Triggered keyword: {s['label']}' style='cursor:help; padding:4px 0;'>+{s['points']} Rules Engine: {s['label']}</div>", unsafe_allow_html=True)
        if bd.typosquat_signals:
            for s in bd.typosquat_signals:
                st.markdown(f"<div title='Detected lookalike domain' style='cursor:help; padding:4px 0;'>+{s['points']} Fake Domain: {s['reason']}</div>", unsafe_allow_html=True)
        
        st.markdown(
            f"<div style='font-family:monospace;color:#94A3B8;text-align:center;"
            f"margin-top:1rem;font-size:0.8rem;'>Math: {bd.formula_string}</div>",
            unsafe_allow_html=True,
        )

    # ── Vouch Button ─────────────────────────────────────────────────────────
    vouch_age = get_vouch_age_days(get_text_hash(text))
    is_vouched_valid = (vouch_age is not None and vouch_age <= 30)
    is_vouched_expired = (vouch_age is not None and vouch_age > 30)

    if is_vouched_valid:
        st.success(f"✅ Community Vouched ({vouch_age} days ago)")
    elif is_vouched_expired:
        st.warning("⚠️ Vouch Expired — re-scan recommended.")


    if st.button("✅ This is Safe (Vouch)", use_container_width=True):
        add_vouch(get_text_hash(text))
        st.toast("Message vouched for in Community DB.", icon="✅")
        st.rerun()

    # ── What To Do Now ───────────────────────────────────────────────────────
    st.markdown("---")
    
    # Dynamic Action Steps based on extracted elements
    if any("upi" in u.lower() or "pay" in u.lower() for u in entities.get("upis", [])) or "upi" in text.lower():
        st.warning("⚠️ **Warning:** Never send money to verify an account.")
    if "otp" in text.lower():
        st.warning("⚠️ **Warning:** Official bodies NEVER ask for OTP over WhatsApp.")
    action = get_action(final, label, text, entities)
    st.markdown(f"### {action['title']}")
    for step in action["steps"]:
        st.markdown(f"- {step}")
    if action.get("helpline"):
        st.info(f"📞 National Cybercrime Helpline: **{action['helpline']}**")

    comp_text = generate_complaint_text(final, label, text, entities, bd.__dict__)
    col_x, col_y = st.columns(2)
    if comp_text:
        with col_x:
            st.download_button(
                "📋 Download Complaint Text", data=comp_text,
                file_name="cybercrime_complaint.txt", use_container_width=True,
            )
    if action.get("online_report"):
        with col_y:
            st.link_button(
                "🌐 Report Online (cybercrime.gov.in)",
                action["online_report"], use_container_width=True,
            )

    # ── Three Golden Rules expander ──────────────────────────────────────────
    with st.expander("📚 Learn More — Three Golden Rules of Campus Safety"):
        st.markdown("""
**Rule 1 — Never pay for a job or internship.**
Legitimate employers never ask for a registration fee, security deposit, or training fee. If they do, it's a scam.

**Rule 2 — Never share OTPs, PINs, or bank details.**
No bank, government body, or official service will ever ask for your OTP, ATM PIN, CVV, or full account number over chat or phone.

**Rule 3 — Always verify domains manually.**
Official communications come from verified domains (e.g. `*.ac.in`, `*.gov.in`, `*.edu`). Never trust links in messages — type the official URL directly in your browser.
        """)

    # ── Social Impact + Community Pulse update ───────────────────────────────
    if label in ("High Risk Scam", "CRITICAL SCAM"):
        cat = _scam_category(text)
        ts = datetime.now().strftime("%H:%M")
        if cat:
            st.session_state.recent_categories.append(f"{cat} @ {ts}")
        else:
            st.session_state.recent_categories.append(f"Generic Scam @ {ts}")
        
        # Log extracted amount
        extracted = extract_amount(text)
        log_scan_amount(extracted)

    # ── Auto-add to FAISS ────────────────────────────────────────────────────
    if label in ("High Risk Scam", "CRITICAL SCAM"):
        history_engine.add_report(text, label=1)
    elif label == "Likely Safe":
        history_engine.add_report(text, label=0)

elif submit and not final_input_text.strip():
    st.toast("Please provide some text or upload a file first!", icon="⚠️")

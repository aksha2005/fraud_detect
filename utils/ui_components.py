"""
utils/ui_components.py
Reusable Streamlit UI components and CSS.
"""
import streamlit as st
import plotly.graph_objects as go

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #050B14;
            color: #F8FAFC;
        }

        /* Neon Primary Elements */
        .hook { font-size: 1.8rem; font-weight: 800; line-height: 1.3; color: #F8FAFC; margin-bottom: 0.5rem; text-align: center; }
        .hook span { color: #FF3B3B; text-shadow: 0 0 10px rgba(255, 59, 59, 0.5); }
        .sub-hook { text-align: center; color: #94A3B8; margin-bottom: 2rem; font-size: 1rem; }
        
        /* Glassmorphism Cards */
        .proof-box { 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 12px;
            padding: 1.5rem; 
            text-align: center; 
            height: 100%; 
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .proof-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .tag { font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5rem; }
        .scam-tag { color: #FF3B3B; text-shadow: 0 0 8px rgba(255,59,59,0.4); }
        .safe-tag { color: #00FF88; text-shadow: 0 0 8px rgba(0,255,136,0.4); }
        .stat-tag { color: #00E5FF; text-shadow: 0 0 8px rgba(0,229,255,0.4); }
        
        .value { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; color: #F8FAFC; }
        .sub { font-size: 0.8rem; color: #94A3B8; }
        
        /* Buttons */
        .stButton>button {
            border: 1px solid #00E5FF;
            color: #00E5FF;
            background: transparent;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: rgba(0, 229, 255, 0.1);
            box-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
            border-color: #00E5FF;
            color: #00E5FF;
        }

        /* Primary Button Override */
        .stButton>button[data-baseweb="button"]:has(div:contains("Scan Threat")) {
            background: #1E3A8A;
            color: #F8FAFC;
            box-shadow: 0 0 15px rgba(30, 58, 138, 0.4);
            border: 1px solid #3B82F6;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stButton>button[data-baseweb="button"]:has(div:contains("Scan Threat")):hover {
            background: #2563EB;
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.8);
            transform: translateY(-2px);
        }
        
        .score-chip { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 800; }
        .chip-scam { background: rgba(255,59,59,0.1); color: #FF3B3B; border: 1px solid rgba(255,59,59,0.3); }
        .chip-suspicious { background: rgba(245,158,11,0.1); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
        .chip-safe { background: rgba(0,255,136,0.1); color: #00FF88; border: 1px solid rgba(0,255,136,0.3); }
        
        .finding-row { padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: monospace; font-size: 0.9rem;}
        .finding-row:last-child { border-bottom: none; }
        
        hr { border-color: rgba(0, 229, 255, 0.2); }

/* Pulse animation for high risk gauge */
@keyframes pulseRed {
  0% { box-shadow: 0 0 10px #FF3B3B; }
  50% { box-shadow: 0 0 20px #FF3B3B; }
  100% { box-shadow: 0 0 10px #FF3B3B; }
}
.high-risk-gauge {
  animation: pulseRed 2s infinite;
  border-radius: 12px;
}

/* Glassmorphism Verdict Cards */
.verdict-card {
    padding: 1.5rem;
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.7);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    margin-bottom: 1rem;
    color: #F8FAFC;
    box-shadow: inset 0 0 20px rgba(255,255,255,0.02);
}
.verdict-scam {
    border: 1px solid rgba(239, 68, 68, 0.6);
    box-shadow: inset 0 0 20px rgba(239, 68, 68, 0.1), 0 0 15px rgba(239, 68, 68, 0.3);
}
.verdict-suspicious {
    border: 1px solid rgba(245, 158, 11, 0.6);
    box-shadow: inset 0 0 20px rgba(245, 158, 11, 0.1), 0 0 15px rgba(245, 158, 11, 0.3);
}
.verdict-safe {
    border: 1px solid rgba(16, 185, 129, 0.6);
    box-shadow: inset 0 0 20px rgba(16, 185, 129, 0.1), 0 0 15px rgba(16, 185, 129, 0.3);
}
.verdict-critical {
    border: 2px solid rgba(220, 20, 60, 0.8);
    box-shadow: 0 0 20px #DC143C;
    animation: pulseCrimson 2s infinite;
}
@keyframes pulseCrimson {
  0% { box-shadow: 0 0 10px #DC143C; }
  50% { box-shadow: 0 0 20px #DC143C; }
  100% { box-shadow: 0 0 10px #DC143C; }
}
.verdict-card h3 { margin-top: 0; margin-bottom: 0.5rem; }
.verdict-card p { margin: 0; color: #E2E8F0; }

/* Pulse animation for Wealth Counter */
@keyframes wealthPulse {
    0% { transform: scale(1); text-shadow: 0 0 5px rgba(0, 229, 255, 0.2); }
    50% { transform: scale(1.05); text-shadow: 0 0 20px rgba(0, 229, 255, 0.8); }
    100% { transform: scale(1); text-shadow: 0 0 5px rgba(0, 229, 255, 0.2); }
}
.pulse-metric {
    display: inline-block;
    animation: wealthPulse 2s infinite ease-in-out;
    color: #00E5FF;
    font-size: 2rem;
    font-weight: 800;
}


        </style>
    """, unsafe_allow_html=True)

def render_hero():
    st.markdown('<p class="hook">Stop Campus Scams Before They Steal Your Money</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-hook">Priya almost lost <span>₹15,000</span> to a fake internship. Campus Fraud Shield would have stopped it in 2 seconds.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="proof-box"><div class="tag scam-tag">Scam detected</div>'
            '<div class="value">Fake Internshala link</div>'
            '<div class="sub">94/100 threat score<br>Would have cost ₹1,500</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="proof-box"><div class="tag safe-tag">Safe verified</div>'
            '<div class="value">Real NSP scholarship</div>'
            '<div class="sub">8/100 risk score<br>Proceed with confidence</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="proof-box"><div class="tag stat-tag">Real Impact</div>'
            '<div class="value">₹1,776 crore</div>'
            '<div class="sub">Lost to cyber fraud<br>India cybercrime impact</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

def render_gauge(score: float, label: str):
    if label == "High Risk Scam":
        color = "#FF3B3B"
    elif label == "Suspicious":
        color = "#F59E0B"
    else:
        color = "#00FF88"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 42, "color": "#F8FAFC"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(255,255,255,0.05)",
            "borderwidth": 2,
            "bordercolor": "rgba(255,255,255,0.1)",
            "steps": [
                {"range": [0, 44], "color": "rgba(0,255,136,0.1)"},
                {"range": [45, 74], "color": "rgba(245,158,11,0.1)"},
                {"range": [75, 100], "color": "rgba(255,59,59,0.1)"},
            ],
            "threshold": {"line": {"color": color, "width": 4}, "value": score},
        },
        title={"text": f'<span style="color:{color}; font-size:24px; font-weight:800; letter-spacing:1px;">{label.upper()}</span>'},
    ))
    fig.update_layout(height=300, margin=dict(t=50, b=0, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Inter"})
    st.plotly_chart(fig, use_container_width=True)

def render_verdict_card(label: str, top_reason: str, overridden: bool = False):
    emoji = "🚨" if label in ["High Risk Scam", "CRITICAL SCAM"] else "⚠️" if label == "Suspicious" else "✅"
    css_class = "verdict-critical" if overridden else "verdict-scam" if label in ["High Risk Scam", "CRITICAL SCAM"] else "verdict-suspicious" if label == "Suspicious" else "verdict-safe"
    
    html = f'''
    <div class="verdict-card {css_class}">
        <h3>{emoji} Verdict: {label}</h3>
        <p>{top_reason if top_reason else "Analysis complete."}</p>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def display_finding(points: float, reason: str):
    if points > 0:
        st.markdown(f'<div class="finding-row"><span style="color:#FF3B3B">+{points}</span> — {reason}</div>', unsafe_allow_html=True)
    else:
        st.caption(reason)

"""
Q-PORT — Quantum Portfolio Intelligence & Optimisation Platform
================================================================

Main Streamlit application entry point.
UC-018 · Asset Manager Portfolio Optimisation

Hybrid quantum-classical optimization using quantum simulation.
"""
from __future__ import annotations

import streamlit as st

from config.settings import (
    APP_TITLE,
    APP_SUBTITLE,
    APP_CHALLENGE,
    APP_TAGLINE,
    DISCLAIMER,
    PAGES,
)

# Page imports
from ui.dashboard import render_dashboard_page
from ui.data_page import render_data_page
from ui.constraints_page import render_constraints_page
from ui.qubo_page import render_qubo_page
from ui.quantum_engine_page import render_quantum_engine_page
from ui.benchmark_page import render_benchmark_page
from ui.quantum_advantage_page import render_quantum_advantage_page
from ui.noise_page import render_noise_page
from ui.backtest_page import render_backtest_page
from ui.explainability_page import render_explainability_page
from ui.methodology_page import render_methodology_page
from ui.reproducibility_page import render_reproducibility_page

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for professional appearance
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d0d3d 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(100, 100, 255, 0.15);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #7c8cf5;
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 3px;
    }
    .main-header .subtitle {
        color: #b0b8e8;
        font-size: 1.1rem;
        margin-top: 0.3rem;
        font-weight: 400;
    }
    .main-header .challenge {
        color: #8890c0;
        font-size: 0.85rem;
        margin-top: 0.2rem;
        font-style: italic;
    }
    .main-header .tagline {
        color: #9098d0;
        font-size: 0.9rem;
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(100, 100, 255, 0.15);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a2e 0%, #12123a 100%);
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #c0c8f0 !important;
    }

    /* Status indicators */
    .status-live { color: #4ade80; font-weight: 600; }
    .status-bundled { color: #facc15; font-weight: 600; }
    .status-error { color: #f87171; font-weight: 600; }

    /* Disclaimer */
    .disclaimer-box {
        background: rgba(251, 191, 36, 0.08);
        border-left: 3px solid #fbbf24;
        padding: 0.8rem 1rem;
        border-radius: 0 6px 6px 0;
        margin-top: 2rem;
        font-size: 0.82rem;
        color: #a0a0b0;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: rgba(20, 20, 60, 0.5);
        border: 1px solid rgba(100, 100, 255, 0.12);
        border-radius: 8px;
        padding: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Routing map
# ---------------------------------------------------------------------------
PAGE_RENDERERS = {
    "dashboard": render_dashboard_page,
    "data": render_data_page,
    "constraints": render_constraints_page,
    "qubo": render_qubo_page,
    "quantum": render_quantum_engine_page,
    "benchmark": render_benchmark_page,
    "quantum_advantage": render_quantum_advantage_page,
    "noise": render_noise_page,
    "backtest": render_backtest_page,
    "explainability": render_explainability_page,
    "methodology": render_methodology_page,
    "reproducibility": render_reproducibility_page,
}

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"### ⚛️ {APP_TITLE}\n"
        f"<span style='color:#8890c0;font-size:0.8rem'>{APP_CHALLENGE}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Navigation radio
    page_options = [f"{p['icon']} {p['title']}" for p in PAGES]
    selected_label = st.radio(
        "Navigation",
        options=page_options,
        index=0,
        label_visibility="collapsed",
    )

    # Resolve selection to page id
    selected_index = page_options.index(selected_label)
    selected_page_id = PAGES[selected_index]["id"]

    st.markdown("---")
    st.markdown(
        "<span style='color:#6068a0;font-size:0.75rem'>"
        "Quantum simulation on ordinary CPU.<br>"
        "No physical quantum hardware.</span>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main content area
# ---------------------------------------------------------------------------

# Header (shown on all pages)
st.markdown(
    f"""
    <div class="main-header">
        <h1>{APP_TITLE}</h1>
        <div class="subtitle">{APP_SUBTITLE}</div>
        <div class="challenge">{APP_CHALLENGE}</div>
        <div class="tagline">{APP_TAGLINE}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Route to the selected page
renderer = PAGE_RENDERERS.get(selected_page_id)
if renderer:
    renderer()
else:
    st.error(f"Unknown page: {selected_page_id}")

# ---------------------------------------------------------------------------
# Footer disclaimer (always visible)
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f'<div class="disclaimer-box">{DISCLAIMER}</div>',
    unsafe_allow_html=True,
)

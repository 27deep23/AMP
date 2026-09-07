"""
Reproducibility & Research Export Center UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import json

from utils.caching import get_cached_preprocessed_data
from core.research_summary import generate_research_summary
from config.settings import QPortConfig


def render_reproducibility_page():
    st.title("💾 Reproducibility & Research Export Center")
    st.caption("Export platform configurations, benchmark results, research reports, and portfolio weights.")

    config = QPortConfig()

    st.subheader("Current Platform Settings Dump")
    st.json(config.to_dict())

    st.divider()

    st.subheader("Data & Research Export")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### Benchmark Results CSV")
        if "benchmark_results" in st.session_state:
            results_df = st.session_state["benchmark_results"]
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                "📥 Download Benchmark CSV",
                data=csv_data,
                file_name="qport_benchmark_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Run benchmark first to enable CSV download.")

    with c2:
        st.markdown("#### Research Summary Markdown")
        if "benchmark_results" in st.session_state:
            results_df = st.session_state["benchmark_results"]
            bench_info = st.session_state["benchmark_info"]
            report_md = generate_research_summary(results_df, bench_info)
            st.download_button(
                "📥 Download Research Report MD",
                data=report_md,
                file_name="qport_research_summary.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.info("Run benchmark first to enable Research Report download.")

    with c3:
        st.markdown("#### Platform Configuration JSON")
        config_json = json.dumps(config.to_dict(), indent=2)
        st.download_button(
            "📥 Download Config JSON",
            data=config_json,
            file_name="qport_config.json",
            mime="application/json",
            use_container_width=True
        )

# charts.py — plots + tables with anchors for guided tour
import matplotlib
matplotlib.use("Agg")  # headless backend for Streamlit Cloud
import matplotlib.pyplot as plt

# import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import pandas as pd
import streamlit as st
import numpy as np

# Needed for validating uploads (Round ID + chart columns)
from constants import COLUMNS


def _apply_scientific(ax):
    """Scientific y-axis labels so numbers stay compact."""
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0), useMathText=True)
    sf = ScalarFormatter(useMathText=True)
    sf.set_scientific(True)
    sf.set_powerlimits((0, 0))
    ax.yaxis.set_major_formatter(sf)


def render_charts_and_tables(rounds_data_all: pd.DataFrame, latest_inputs_series, curr: int):
    if rounds_data_all.empty:
        st.info("Run a round to populate charts.")
        return

    rounds_data_all = rounds_data_all.sort_values("Round ID")

    # ---- Read display settings from the left “Display” panel ----
    show_2m = st.session_state.get("show_2m", True)
    show_1y = st.session_state.get("show_1y", True)
    show_5y = st.session_state.get("show_5y", True)
    hidden_set = set(st.session_state.get("hidden_rounds", []))

    # Apply hidden filter
    rounds_data = rounds_data_all[~rounds_data_all["Round ID"].astype(int).isin(hidden_set)].copy()
    if rounds_data.empty:
        st.info("All rounds are hidden. Unhide some rounds in the Display panel to see charts and outputs.")
        return

    # Convert columns
    rounds_data["Round ID"] = pd.to_numeric(rounds_data["Round ID"], errors="coerce")
    for c in [
        "Total_profit_two_months", "Total_profit_one_year", "Total_profit_five_year",
        "Total_emission_two_months", "Total_emission_one_year", "Total_emission_five_year",
    ]:
        if c in rounds_data:
            rounds_data[c] = pd.to_numeric(rounds_data[c], errors="coerce")

    # Prepare X
    X = rounds_data["Round ID"].astype(int).to_numpy()
    xticks_vals = sorted(rounds_data["Round ID"].astype(int).unique().tolist())

    # ----- Demand denominators (prefer period-specific; fall back to daily demand * days) -----
    def _den_or_none(colname_period: str, days: int):
        """Return a Series denominator if we can compute it, else None."""
        if colname_period in rounds_data:
            return pd.to_numeric(rounds_data[colname_period], errors="coerce")
        if "Total_demand" in rounds_data:
            return pd.to_numeric(rounds_data["Total_demand"], errors="coerce") * float(days)
        return None

    den_2m = _den_or_none("Total_demand_two_months", 60)
    den_1y = _den_or_none("Total_demand_one_year", 365)
    den_5y = _den_or_none("Total_demand_five_year", 1825)

    # We only switch to "per demand" mode if denominators exist for all displayed series
    need_2m = show_2m and "Total_profit_two_months" in rounds_data and "Total_emission_two_months" in rounds_data
    need_1y = show_1y and "Total_profit_one_year" in rounds_data and "Total_emission_one_year" in rounds_data
    need_5y = show_5y and "Total_profit_five_year" in rounds_data and "Total_emission_five_year" in rounds_data

    per_demand_ready = True
    if need_2m and den_2m is None: per_demand_ready = False
    if need_1y and den_1y is None: per_demand_ready = False
    if need_5y and den_5y is None: per_demand_ready = False

    # Top spacer (~1 cm)
    st.markdown('<div style="height:38px;"></div>', unsafe_allow_html=True)

    # ---- Charts row ----
    with plt.rc_context({
        # Fonts & sizes — Times New Roman everywhere
        "font.family": "Times New Roman",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        # Line aesthetics / resolution
        "lines.linewidth": 2.0,
        "lines.markersize": 4,
        "figure.dpi": 160,  # higher resolution
    }):
        # Slightly smaller than your original, crisp, with clear gaps
        fig, axes = plt.subplots(1, 2, figsize=(8.0, 2.6))

        def prettify(ax, title, ylab):
            ax.set_title(title)
            ax.set_xlabel("Round")
            ax.set_ylabel(ylab)
            ax.grid(True, which="major", linewidth=0.6, alpha=0.35)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.set_xticks(xticks_vals)
            if xticks_vals:
                ax.set_xlim(min(xticks_vals) - 0.5, max(xticks_vals) + 0.5)
            for spine in ax.spines.values():
                spine.set_linewidth(0.8)
                spine.set_alpha(0.6)
            _apply_scientific(ax)  # scientific y-axis

        # Helper: safe division (vectorized)
        def _div(numer, denom):
            if denom is None:
                return numer.to_numpy()
            d = np.maximum(denom.to_numpy().astype(float), 1e-9)
            return numer.to_numpy().astype(float) / d

        # ---------------- Profit (per demand if ready; else totals) ----------------
        axp = axes[0]
        if per_demand_ready:
            if show_2m and "Total_profit_two_months" in rounds_data:
                axp.plot(X, _div(rounds_data["Total_profit_two_months"], den_2m), marker="o", label="2M")
            if show_1y and "Total_profit_one_year" in rounds_data:
                axp.plot(X, _div(rounds_data["Total_profit_one_year"], den_1y), marker="s", label="1Y")
            if show_5y and "Total_profit_five_year" in rounds_data:
                axp.plot(X, _div(rounds_data["Total_profit_five_year"], den_5y), marker="D", label="5Y")
            prettify(axp, "Profit per demand", "AUD / parcel")
        else:
            if show_2m and "Total_profit_two_months" in rounds_data:
                axp.plot(X, rounds_data["Total_profit_two_months"].to_numpy(), marker="o", label="2M")
            if show_1y and "Total_profit_one_year" in rounds_data:
                axp.plot(X, rounds_data["Total_profit_one_year"].to_numpy(), marker="s", label="1Y")
            if show_5y and "Total_profit_five_year" in rounds_data:
                axp.plot(X, rounds_data["Total_profit_five_year"].to_numpy(), marker="D", label="5Y")
            prettify(axp, "Profit", "AUD")

        if any([show_2m, show_1y, show_5y]):
            axp.legend(loc="best", frameon=False)

        # ---------------- Emissions (per demand if ready; else totals) ----------------
        axe = axes[1]
        if per_demand_ready:
            if show_2m and "Total_emission_two_months" in rounds_data:
                axe.plot(X, _div(rounds_data["Total_emission_two_months"], den_2m), marker="o", label="2M")
            if show_1y and "Total_emission_one_year" in rounds_data:
                axe.plot(X, _div(rounds_data["Total_emission_one_year"], den_1y), marker="s", label="1Y")
            if show_5y and "Total_emission_five_year" in rounds_data:
                axe.plot(X, _div(rounds_data["Total_emission_five_year"], den_5y), marker="D", label="5Y")
            prettify(axe, "Emissions per demand", "Cost / parcel (proxy)")
        else:
            if show_2m and "Total_emission_two_months" in rounds_data:
                axe.plot(X, rounds_data["Total_emission_two_months"].to_numpy(), marker="o", label="2M")
            if show_1y and "Total_emission_one_year" in rounds_data:
                axe.plot(X, rounds_data["Total_emission_one_year"].to_numpy(), marker="s", label="1Y")
            if show_5y and "Total_emission_five_year" in rounds_data:
                axe.plot(X, rounds_data["Total_emission_five_year"].to_numpy(), marker="D", label="5Y")
            prettify(axe, "Emissions", "Cost (proxy)")

        if any([show_2m, show_1y, show_5y]):
            axe.legend(loc="best", frameon=False)

        # Clear 1cm gap between charts and to the right window edge
        fig.subplots_adjust(left=0.08, right=0.95, bottom=0.22, top=0.88, wspace=0.5)

        # Invisible anchors for the tour (near the figures)
        st.markdown('<div id="profit-chart"></div>', unsafe_allow_html=True)
        st.markdown('<div id="emissions-chart"></div>', unsafe_allow_html=True)
        try:
            st.pyplot(fig, clear_figure=True)
        finally:
            plt.close(fig)

    # If we had to fall back, tell the user why
    if not per_demand_ready:
        st.info(
            "Showing totals because per-demand denominators were not found. "
            "Add either period demand columns "
            "(`Total_demand_two_months`, `Total_demand_one_year`, `Total_demand_five_year`) "
            "or a daily `Total_demand` column so charts can display per-parcel values."
        )

    # Bottom spacer (~1 cm)
    st.markdown('<div style="height:38px;"></div>', unsafe_allow_html=True)

    # ---- Tables row ----
    t_l, t_r = st.columns([1, 2], gap="small")

    with t_l:
        # Inputs panel (translucent like home cards)
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div id="inputs-table"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Inputs (this round)</div>', unsafe_allow_html=True)
        if latest_inputs_series is not None:
            df_in = latest_inputs_series.to_frame(name=f"Round {curr}").reset_index()
            df_in.columns = ["Feature", "Value"]
            st.dataframe(df_in, hide_index=True, use_container_width=True, height=220)
        else:
            st.caption("After you run a round, inputs appear here.")
        st.markdown('</div>', unsafe_allow_html=True)

    with t_r:
        # Outputs + download + upload (all inside same panel)
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div id="outputs-table"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Outputs (displayed rounds)</div>', unsafe_allow_html=True)

        st.dataframe(rounds_data, use_container_width=True, height=220)

        # Download current view
        csv = rounds_data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV (displayed)",
            data=csv,
            file_name="carrier_game_results_display.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Upload previous rounds
        st.markdown("### 🔼 Upload previous rounds")
        uploaded_file = st.file_uploader(
            "Upload a CSV of previous rounds (exported earlier from this app)",
            type=["csv"],
            key="round_upload"
        )

        # Process the uploaded file exactly once per file content
        if uploaded_file is not None:
            try:
                # compute a stable hash for this file content
                import hashlib
                file_bytes = uploaded_file.getvalue()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                # guard: if we've already processed this exact file, skip
                last_hash = st.session_state.get("last_uploaded_rounds_hash")
                if last_hash != file_hash:
                    uploaded_df = pd.read_csv(uploaded_file)

                    required_for_charts = [
                        "Round ID",
                        "Total_profit_two_months", "Total_profit_one_year", "Total_profit_five_year",
                        "Total_emission_two_months", "Total_emission_one_year", "Total_emission_five_year",
                        # Note: we keep demand columns optional to support old CSVs.
                    ]
                    missing = [c for c in required_for_charts if c not in uploaded_df.columns]
                    if missing:
                        st.error(f"❌ Uploaded CSV is missing required columns for charts: {missing}")
                    else:
                        # Coerce numeric columns so plotting won't break
                        for c in required_for_charts:
                            uploaded_df[c] = pd.to_numeric(uploaded_df[c], errors="coerce")

                        # Merge into session results (de-dup by Round ID)
                        st.session_state.rounds_results = (
                            pd.concat([st.session_state.rounds_results, uploaded_df], ignore_index=True)
                              .drop_duplicates(subset=["Round ID"], keep="last")
                              .sort_values("Round ID", kind="stable")
                              .reset_index(drop=True)
                        )

                        # Advance current round to next integer
                        max_round = pd.to_numeric(
                            st.session_state.rounds_results["Round ID"], errors="coerce"
                        ).max()
                        if pd.notna(max_round):
                            st.session_state.current_round = int(max_round) + 1

                        # mark this file as processed
                        st.session_state["last_uploaded_rounds_hash"] = file_hash
                        st.success(f"✅ Imported {len(uploaded_df)} rows. Charts above are now using them.")
                else:
                    st.info("This file was already processed. Pick a different file to re-import.")
            except Exception as e:
                st.error(f"⚠️ Failed to read uploaded file: {e}")

        # Close the panel wrapper
        st.markdown('</div>', unsafe_allow_html=True)

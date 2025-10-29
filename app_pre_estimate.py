# app.py — Urban Freight Simulation Game
# Uses external styles.css and constants.py (COLUMNS + init_environment)

from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from base64 import b64encode

# ---------- Background helpers ----------
def _data_uri_for(name_no_ext: str) -> Optional[str]:
    """Return a data: URI for name_no_ext.(png|jpg|jpeg|webp) if present next to app.py."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = Path(__file__).with_name(f"{name_no_ext}.{ext}")
        if p.exists():
            data = p.read_bytes()
            b64 = b64encode(data).decode("ascii")
            mime = "jpeg" if ext == "jpg" else ext
            return f"data:image/{mime};base64,{b64}"
    return None

def _apply_home_background():
    uri = _data_uri_for("background1")
    if not uri:
        return
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
          background: url("{uri}") no-repeat center center fixed;
          background-size: cover;
        }}
        .block-container {{
          background: transparent !important;
          padding: 38px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _apply_carrier_background():
    """Use background2.* if available for Carrier page."""
    uri = _data_uri_for("background2")
    if not uri:
        st.markdown(
            """
            <style>
            [data-testid="stAppViewContainer"] {
              background: var(--background-color) !important;
              background-size: auto !important;
            }
            .block-container { background: transparent !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
          background: url("{uri}") no-repeat center center fixed !important;
          background-size: cover !important;
        }}
        .block-container {{ background: transparent !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _ensure_defaults():
    """Make sure all session_state keys exist before use."""
    ss = st.session_state
    # routing
    ss.setdefault("page", "home")
    # round/result state
    ss.setdefault("current_round", 1)
    ss.setdefault("rounds_results", pd.DataFrame())
    ss.setdefault("hidden_rounds", [])
    # panel selections
    ss.setdefault("top_panel", "strategic")   # 'strategic' | 'operational'
    ss.setdefault("bottom_panel", "service")  # 'service'   | 'display'
    # strategic & operational controls
    ss.setdefault("diesel_share", 60)
    ss.setdefault("microhub_enabled", False)
    ss.setdefault("fee_small", 7.0)
    ss.setdefault("fee_medium", 10.0)
    ss.setdefault("fee_large", 18.0)
    ss.setdefault("next_day_inc", 0.20)
    ss.setdefault("same_day_inc", 0.50)
    ss.setdefault("offpeak", False)
    ss.setdefault("redel", True)
    ss.setdefault("tracking", True)
    ss.setdefault("insurance", False)
    ss.setdefault("signature", False)
    # display options
    ss.setdefault("show_2m", True)
    ss.setdefault("show_1y", True)
    ss.setdefault("show_5y", True)
    # tour
    ss.setdefault("tour_step", 0)

# ---------- Models / modules ----------
from Ship_choice_pre_estimate import (
    run_shippers_choice_model,
    calculate_probability_of_selecting_by_shippers,
)
from Recip_choice_pre_estimate import (
    run_recipients_choice_model,
    calculate_probability_of_selecting_by_recipients,
)

from compute import compute_round_result
from charts import render_charts_and_tables
from constants import COLUMNS, init_environment

# ---------- Streamlit page & styles ----------
st.set_page_config(page_title="Urban Freight Simulation Game", layout="wide")

_css_path = Path(__file__).with_name("styles.css")
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
else:
    st.warning("styles.css not found; falling back to default Streamlit styles.")

# ---------- Router ----------
def go_home():
    st.session_state.page = "home"
    st.rerun()

def go_carrier():
    st.session_state.page = "carrier"
    st.rerun()

# ---------- Tour helpers ----------
def tour_on() -> bool:
    return st.session_state.get("tour_step", 0) > 0

def start_tour():
    st.session_state.tour_step = 1

def end_tour():
    st.session_state.tour_step = 0

def tour_step_is(n: int) -> bool:
    return st.session_state.get("tour_step", 0) == n

def tour_nav(prev_step: Optional[int], next_step: Optional[int]):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("End tour", key=f"tour_end_{st.session_state.get('tour_step',0)}", use_container_width=True):
            end_tour()
    with c2:
        if prev_step is not None:
            if st.button("◀ Back", key=f"tour_back_{prev_step}", use_container_width=True):
                st.session_state.tour_step = prev_step; st.rerun()
    with c3:
        if next_step is not None:
            if st.button("Next ▶", key=f"tour_next_{next_step}", use_container_width=True):
                st.session_state.tour_step = next_step; st.rerun()

def tour_tip(title: str, body: str, width_px: int = 320, anchor_id: Optional[str] = None):
    jump = f' <a href="#{anchor_id}">Jump ↘</a>' if anchor_id else ""
    st.markdown(
        f"""
        <div class="tour-tip" style="max-width:{width_px}px">
            <div class="tour-tip-title">{title}</div>
            <div class="tour-tip-body">{body}{jump}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Home ----------
def render_home():
    _ensure_defaults()
    _apply_home_background()
    st.markdown('<div class="home-top-gap"></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.markdown(
            """
            <div class="card home-left-info">
              <div class="pilltitle">📦 Project Overview</div>
              <div class="home-left-body">
                <p class="sub">
                  Use this space to describe your research project, goals,
                  data sources, stakeholders, and how to use the simulation in workshops.
                </p>
                <ul class="home-left-list">
                  <li>Context & motivation</li>
                  <li>Key research questions</li>
                  <li>Data & assumptions</li>
                  <li>How to interpret the outputs</li>
                </ul>
                <p class="sub">You can replace this text anytime.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="card home-hero">
              <h1 style="margin:0;">Multi-Agent Simulation Game for Urban Freight Transport</h1>
              <p class="home-hero-sub">
                Four stakeholder modules: <b>Parcel Recipient</b>, <b>Carrier</b>, <b>Shipper</b>, and <b>Government</b>.<br/>
                Explore strategies, adjust service levers, and observe system-wide trade-offs across profit and emissions.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        g1, g2 = st.columns(2, gap="large")
        with g1:
            st.markdown(
                """
                <div class="card module-card">
                  <div class="pilltitle">🎯 Parcel Recipient</div>
                  <div class="sub">Evaluate delivery preferences, WTP, and service trade-offs.</div>
                  <div class="module-card-actions">
                    <button class="btn btn-disabled" disabled>Under development</button>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with g2:
            st.markdown(
                """
                <div class="card module-card">
                  <div class="pilltitle">🚚 Carrier Game</div>
                  <div class="sub">Optimise fleet mix, service levels, and operations to maximise profit and minimise emissions.</div>
                  <div class="module-card-actions">
                """,
                unsafe_allow_html=True,
            )
            if st.button("Enter Carrier Game", key="btn_carrier", type="primary", use_container_width=True):
                go_carrier()
            st.markdown("</div></div>", unsafe_allow_html=True)

        r2c1, r2c2 = st.columns(2, gap="large")
        with r2c1:
            st.markdown(
                """
                <div class="card module-card">
                  <div class="pilltitle">🏪 Shipper</div>
                  <div class="sub">Choose carrier partnerships, pricing, and bundles to capture market share.</div>
                  <div class="module-card-actions">
                    <button class="btn btn-disabled" disabled>Under development</button>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r2c2:
            st.markdown(
                """
                <div class="card module-card">
                  <div class="pilltitle">🏛️ Government</div>
                  <div class="sub">Test policies (e.g., off-peak incentives, microhubs) and observe system-wide impacts.</div>
                  <div class="module-card-actions">
                    <button class="btn btn-disabled" disabled>Under development</button>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------- Carrier ----------
def render_carrier():
    _ensure_defaults()
    _apply_carrier_background()

    # CSS: give Streamlit containers a translucent white background when they contain a sentinel.
    # Also give H4/H5 headings a soft background so titles are readable over the image.
    st.markdown("""
    <style>
      /* Soft background behind H4/H5 titles (Inputs / Outputs etc.) */
      h4, h5 {
        display:inline-block;
        background: rgba(255,255,255,0.85);
        padding: 4px 8px;
        border-radius: 8px;
        margin-bottom: 8px;
      }
    
      /* ------------ Translucent card for the REAL Streamlit panel containers ------------ */
      /* Catch the VerticalBlock that CONTAINS the sentinel (no need to be a direct child) */
      [data-testid="stVerticalBlock"]:has(.panel-sentinel),
      /* Also catch a nested VerticalBlock/Container that contains the sentinel
         (Streamlit sometimes nests blocks differently between versions) */
      [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"]:has(.panel-sentinel),
      [data-testid="stContainer"]:has(.panel-sentinel) {
        background: rgba(255,255,255,0.80) !important;   /* <<< the white with 0.8 transparency */
        border: 1px solid rgba(148,163,184,.35) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 24px rgba(0,0,0,.08) !important;
        padding: 12px !important;
        /* give some breathing room so it doesn't sit right on the image */
        margin-bottom: 10px !important;
        backdrop-filter: saturate(120%) blur(2px);
      }
    
      /* Make the left-side UI a bit denser */
      #left-ui { font-size: 0.92rem; }
    
      /* Tighten page top spacing on Carrier only */
      .block-container { padding-top: 14px !important; }
    </style>
    """, unsafe_allow_html=True)


    st.button("← Back to main menu", on_click=go_home)

    # ----- Models & data (cached) -----
# ----- Models & data (cached) -----
    @st.cache_resource
    def load_models_static():
        # These functions now load from JSON files next to app.py
        from Ship_choice_pre_estimate import (
            run_shippers_choice_model,
            calculate_probability_of_selecting_by_shippers,
        )
        from Recip_choice_pre_estimate import (
            run_recipients_choice_model,
            calculate_probability_of_selecting_by_recipients,
        )
    
        try:
            # Path arg is ignored by your JSON-backed loaders
            ship = run_shippers_choice_model(None)   # reads shippers_betas.json
            recp = run_recipients_choice_model(None) # reads recipients_betas.json
        except FileNotFoundError:
            st.error("❌ Missing model files. Ensure **shippers_betas.json** and **recipients_betas.json** sit next to `app.py`.")
            st.stop()
        except Exception as e:
            st.error("Failed to load model parameters.")
            st.exception(e)
            st.stop()
    
        return {
            "shippers_beta_values": ship["beta_values"],
            "recipients_beta_values": recp["beta_values"],
            "calculate_probability_of_selecting_by_shippers": calculate_probability_of_selecting_by_shippers,
            "calculate_probability_of_selecting_by_recipients": calculate_probability_of_selecting_by_recipients,
        }
    
    @st.cache_resource
    def load_shippers_geo_static():
        csv_path = Path(__file__).with_name("shipper_data.csv")
        return pd.read_csv(csv_path, delimiter=",")
    
    models = load_models_static()
    st.caption(
        f"Models loaded ✓ — {len(models['shippers_beta_values'])} shipper betas, "
        f"{len(models['recipients_beta_values'])} recipient betas."
    )
    
    shippers_geo = load_shippers_geo_static()
    ctx = init_environment(shippers_geo)
    
    curr = st.session_state.current_round
    
    # Layout
    dashboard, main = st.columns([1.5, 4], gap="small")


    # ===== LEFT: stacked half-width panels =====
    with dashboard:
        st.markdown('<div id="left-ui">', unsafe_allow_html=True)

        # ---- Top tabs row (Strategic / Operational) ----
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("🎯 Strategic", use_container_width=True,
                         type=("primary" if st.session_state.top_panel == "strategic" else "secondary")):
                st.session_state.top_panel = "strategic"
        with c2:
            if st.button("🛠️ Operational", use_container_width=True,
                         type=("primary" if st.session_state.top_panel == "operational" else "secondary")):
                st.session_state.top_panel = "operational"

        # ---- Top panel content (sentinel makes the parent block get a white translucent background) ----
        top_panel = st.container()
        with top_panel:
            st.markdown('<div class="panel-sentinel"></div>', unsafe_allow_html=True)  # << sentinel
            st.markdown(f"#### {'Strategic' if st.session_state.top_panel=='strategic' else 'Operational'}")

            if st.session_state.top_panel == "strategic":
                colA, colB = st.columns(2, gap="small")
                with colA:
                    st.session_state.diesel_share = st.slider(
                        "Diesel share (%)", 0, 100, st.session_state.diesel_share, 1
                    )
                with colB:
                    st.session_state.microhub_enabled = st.checkbox(
                        "Microhub delivery ⓘ",
                        value=st.session_state.microhub_enabled,
                        help="Vans to a microhub area; final addresses by (e-)cargo bikes."
                    )
            else:
                r1c1, r1c2 = st.columns(2, gap="small")
                with r1c1:
                    st.session_state.fee_small = st.slider(
                        "Small (AUD)", 0.0, 20.0, st.session_state.fee_small, 0.5
                    )
                with r1c2:
                    st.session_state.fee_medium = st.slider(
                        "Medium (AUD)", 0.0, 20.0, st.session_state.fee_medium, 0.5
                    )

                r2c1, r2c2 = st.columns(2, gap="small")
                with r2c1:
                    st.session_state.fee_large = st.slider(
                        "Large (AUD)", 0.0, 20.0, st.session_state.fee_large, 0.5
                    )
                with r2c2:
                    st.session_state.next_day_inc = st.slider(
                        "Next-day (× vs standard)", 0.0, 10.0,
                        st.session_state.next_day_inc, 0.05
                    )

                r3c1, r3c2 = st.columns(2, gap="small")
                with r3c1:
                    st.session_state.same_day_inc = st.slider(
                        "Same-day (× vs standard)", 0.0, 10.0,
                        st.session_state.same_day_inc, 0.05
                    )
                with r3c2:
                    st.markdown("&nbsp;")

        # ---- Bottom tabs row (Service / Display) ----
        c3, c4 = st.columns(2, gap="small")
        with c3:
            if st.button("📦 Service", use_container_width=True,
                         type=("primary" if st.session_state.bottom_panel == "service" else "secondary")):
                st.session_state.bottom_panel = "service"
        with c4:
            if st.button("📊 Display", use_container_width=True,
                         type=("primary" if st.session_state.bottom_panel == "display" else "secondary")):
                st.session_state.bottom_panel = "display"

        # ---- Bottom panel content (sentinel again for background) ----
        bottom_panel = st.container()
        with bottom_panel:
            st.markdown('<div class="panel-sentinel"></div>', unsafe_allow_html=True)  # << sentinel
            st.markdown(f"#### {'Service' if st.session_state.bottom_panel=='service' else 'Display options'}")

            if st.session_state.bottom_panel == "service":
                s1, s2 = st.columns(2, gap="small")
                with s1:
                    st.session_state.offpeak   = st.toggle("Off-peak",   value=st.session_state.offpeak)
                with s2:
                    st.session_state.redel     = st.toggle("Redelivery", value=st.session_state.redel)

                s3, s4 = st.columns(2, gap="small")
                with s3:
                    st.session_state.tracking  = st.toggle("Tracking",   value=st.session_state.tracking)
                with s4:
                    st.session_state.insurance = st.toggle("Insurance",  value=st.session_state.insurance)

                s5, _ = st.columns(2, gap="small")
                with s5:
                    st.session_state.signature = st.toggle("Signature",  value=st.session_state.signature)
            else:
                d1, d2 = st.columns(2, gap="small")
                with d1:
                    st.session_state.show_2m = st.checkbox("2M (two months)", value=st.session_state.show_2m)
                with d2:
                    st.session_state.show_1y = st.checkbox("1Y (one year)",   value=st.session_state.show_1y)

                d3, _ = st.columns(2, gap="small")
                with d3:
                    st.session_state.show_5y = st.checkbox("5Y (five years)", value=st.session_state.show_5y)

                with st.expander("More display controls", expanded=False):
                    all_round_ids = (
                        st.session_state.rounds_results["Round ID"].astype(int).tolist()
                        if not st.session_state.rounds_results.empty else []
                    )
                    st.session_state.hidden_rounds = st.multiselect(
                        "Hide rounds from display (non-destructive)",
                        options=all_round_ids,
                        default=st.session_state.hidden_rounds,
                        placeholder="Select Round IDs to hide…",
                    )

        # ---- Reset / Run buttons (below panels) ----
        b1, b2 = st.columns(2, gap="small")
        reset_clicked = b1.button("Reset", use_container_width=True)
        run_clicked   = b2.button("Run this round", type="primary", use_container_width=True)

        # Tour button BELOW the panels (always active)
        tour_box = st.container()
        with tour_box:
            st.markdown('<div class="panel-sentinel"></div>', unsafe_allow_html=True)  # give it a card bg too
            if st.button("🎓 Start guided tour", use_container_width=True, key="tour_btn_below_panels_always"):
                start_tour()

        # Tour steps 1–2 (left side)
        if tour_step_is(1):
            tour_tip("Panels", "Use Strategic/Operational and Service/Display to configure your round.")
            tour_nav(prev_step=None, next_step=2)
        if tour_step_is(2):
            tour_tip("Run & Reset", "Click **Run this round** to append results; **Reset** clears history.")
            tour_nav(prev_step=1, next_step=3)

        st.markdown('</div>', unsafe_allow_html=True)  # end #left-ui

    # Read values from session
    diesel_share     = st.session_state.diesel_share
    microhub_enabled = st.session_state.microhub_enabled
    fee_small        = st.session_state.fee_small
    fee_medium       = st.session_state.fee_medium
    fee_large        = st.session_state.fee_large
    next_day_inc     = st.session_state.next_day_inc
    same_day_inc     = st.session_state.same_day_inc
    offpeak          = st.session_state.offpeak
    redel            = st.session_state.redel
    tracking         = st.session_state.tracking
    insurance        = st.session_state.insurance
    signature        = st.session_state.signature

    # ===== Reset / Run =====
    latest_inputs_series = None
    if reset_clicked:
        st.session_state.current_round = 1
        st.session_state.rounds_results = pd.DataFrame()
        st.session_state.hidden_rounds = []
        st.rerun()

    if run_clicked:
        latest_inputs_series = pd.Series({
            "Next_day_delivery_increase": float(next_day_inc),
            "Same_day_delivery_increase": float(same_day_inc),
            "Delivery_fee_small": float(fee_small),
            "Medium_parcels_delivery_fee": float(fee_medium),
            "Large_parcels_delivery_fee": float(fee_large),
            "Share_of_diesel_vans": float(diesel_share),
            "Share_of_electric_vans": float(100 - diesel_share),
            "Microhub_delivery": int(microhub_enabled),
            "Offpeak_delivery": int(offpeak),
            "Signature_required": int(signature),
            "Redelivery": int(redel),
            "Tracking": int(tracking),
            "Insurance": int(insurance),
        })[COLUMNS]
        try:
            row = compute_round_result(curr, latest_inputs_series, COLUMNS, models, ctx)
        except Exception as e:
            st.error(f"Round {curr} failed to compute.")
            st.exception(e); row = None

        if row is not None:
            st.session_state.rounds_results = pd.concat(
                [st.session_state.rounds_results, pd.DataFrame([row])],
                ignore_index=True
            )
            st.session_state.current_round = curr + 1
            st.success(f"Round {curr} appended.")

    # ===== RIGHT: charts + tables =====
    with main:
        render_charts_and_tables(st.session_state.rounds_results.copy(), latest_inputs_series, curr)

        # Tour steps 3–6 (right side)
        if not st.session_state.rounds_results.empty:
            if tour_step_is(3):
                tour_tip("Profit charts", "Compare profits over 2M / 1Y / 5Y horizons by round.", anchor_id="profit-chart")
                tour_nav(prev_step=2, next_step=4)
            if tour_step_is(4):
                tour_tip("Emissions chart", "Emissions cost proxy for your strategy and operational settings.", anchor_id="emissions-chart")
                tour_nav(prev_step=3, next_step=5)
            if tour_step_is(5):
                tour_tip("Inputs table", "Shows the exact inputs used for your most recent round.", anchor_id="inputs-table")
                tour_nav(prev_step=4, next_step=6)
            if tour_step_is(6):
                tour_tip("Outputs table", "Outputs for displayed rounds. Use the button below to download CSV.", anchor_id="outputs-table")
                tour_nav(prev_step=5, next_step=None)


# ---------- Seatbelt ----------
def safe_render(fn):
    try:
        fn()
    except Exception as e:
        import traceback
        st.error("⚠️ Something went wrong, but the app is still running.")
        st.exception(e)
        with open("streamlit_error.log", "a", encoding="utf-8") as f:
            f.write("\n\n" + traceback.format_exc())

# ---------- Render ----------
if st.session_state.get("page", "home") == "home":
    safe_render(render_home)
else:
    safe_render(render_carrier)


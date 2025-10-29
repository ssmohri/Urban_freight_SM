# Ship_choice.py — lightweight loader using pre-estimated betas (no Biogeme)
import json
import math
from pathlib import Path
import pandas as pd  # only for the type of observation passed in from compute.py

_JSON = Path(__file__).with_name("shippers_betas.json")

def run_shippers_choice_model(_data_path_ignored: str):
    """Load pre-estimated shipper betas from JSON and return the expected dict."""
    if not _JSON.exists():
        raise FileNotFoundError(f"Missing {_JSON.name}. Generate it with export_betas.py and commit it.")
    betas = json.loads(_JSON.read_text(encoding="utf-8"))
    return {
        "beta_values": betas,
        # keep keys the app expects, even if unused now:
        "database": None,
        "data": None,
        "pandasResults_shipper": None,
    }

def calculate_probability_of_selecting_by_shippers(beta_values, observation: pd.DataFrame) -> float:
    """Compute logistic(prob) using one-row DataFrame `observation` from compute.py."""
    row = observation.iloc[0]
    b = lambda k: float(beta_values.get(k, 0.0))
    x = (
        b("ASC_accept")
        + b("B_Next_vs_standard_increase") * float(row["Next_day_delivery_increase"])
        + b("B_Same_vs_standard_increase") * float(row["Same_day_delivery_increase"])
        + b("B_Delivery_fee_small")        * float(row["Delivery_fee_small"])
        + b("B_Delivery_fee_Medium")       * float(row["Medium_parcels_delivery_fee"])
        + b("B_Diesel_van")                * float(row["Share_of_diesel_vans"])
        + b("B_Micro_hub_with_bike")       * int(row["Microhub_delivery"])
        + b("B_Off_peak")                  * int(row["Offpeak_delivery"])
        + b("B_Insurance")                 * int(row["Insurance"])
        + b("B_Tracking")                  * int(row["Tracking"])
        + b("B_Redelivery")                * int(row["Redelivery"])
        + b("B_Signature")                 * int(row["Signature_required"])
    )
    return 1.0 / (1.0 + math.exp(-x))

# constants.py — shared constants and environment setup for the carrier game
import random
import math
import pandas as pd

# Column names used throughout the app and compute.py
COLUMNS = [
    "Next_day_delivery_increase","Same_day_delivery_increase",
    "Delivery_fee_small","Medium_parcels_delivery_fee","Large_parcels_delivery_fee",
    "Share_of_diesel_vans","Share_of_electric_vans","Microhub_delivery",
    "Offpeak_delivery","Signature_required","Redelivery","Tracking","Insurance",
]

def init_environment(shippers_geo: pd.DataFrame) -> dict:
    """
    Recreates the exact environment/constants block from the original app and
    returns a ctx dict with all names that compute_round_result() expects.
    """
    random.seed(42)

    # Areas & demand densities
    total_area = 900
    CBD_area_for_microhub = 25
    CBD_delivery_density = random.uniform(35, 43)
    non_CBD_delivery_density = random.uniform(4, 8)

    # Derived deliveries
    number_of_CBD_deliveries = CBD_delivery_density * CBD_area_for_microhub
    number_of_non_CBD_deliveries = (total_area - CBD_area_for_microhub) * non_CBD_delivery_density
    number_of_deliveries = number_of_CBD_deliveries + number_of_non_CBD_deliveries
    CDD_share = number_of_CBD_deliveries / max(1e-9, number_of_deliveries)
    failed_delivery_rate = random.uniform(0.45, 0.58)

    # Vehicle capacities/speeds and schedule
    diesel_van_cap = 10
    electric_van_cap = 8
    cargo_bike_cap = 0.5

    diesel_van_speed = 55
    electric_van_speed = 55
    cargo_bike_speed = 20

    loading_unloading_time = 0.02
    Vehicels_daily_operating_hours = 8

    # Parcel sizes/frequencies
    small_parcel_volume = 0.02
    medium_parcel_volume = 0.05
    large_parcel_volume = 0.145

    small_parcel_frequency = 0.53
    medium_parcel_frequency = 0.30
    large_parcel_frequency = 0.17

    # Costs (operational/external/fixed)
    diesel_van_operational_cost = 50
    electric_van_operational_cost = 45
    bike_operational_cost = 25

    diesel_van_external_cost = 1
    electric_van_external_cost = 0.1
    bike_external_cost = 0

    diesel_van_daily_fixed_cost = (50000 - 10000) / 10 / 365
    electric_van_daily_fixed_cost = (70000 - 15000) / 10 / 365
    bike_daily_fixed_cost = (10000 - 2000) / 5 / 365

    # Demand split (normalized)
    Share_of_standard = 0.7 + random.uniform(-0.15, 0.15)
    Share_of_next_day = 0.2 + random.uniform(-0.1, 0.1)
    Share_of_same_day = 0.1 + random.uniform(-0.05, 0.05)
    _t = Share_of_standard + Share_of_next_day + Share_of_same_day
    Share_of_standard /= _t
    Share_of_next_day /= _t
    Share_of_same_day /= _t

    # Geometry / volume factor (note: mutates shippers_geo just like original)
    shippers_geo['Shipper Volume'] = number_of_deliveries * shippers_geo['Shipper Volume_share']
    r2 = shippers_geo['Distance to Depot'].mean()
    NS = len(shippers_geo)
    E_vol = (small_parcel_volume * small_parcel_frequency +
             medium_parcel_volume * medium_parcel_frequency +
             large_parcel_volume  * large_parcel_frequency)

    # Pack context with *exact* keys used by compute.py
    ctx = dict(
        math=math,
        total_area=total_area, CBD_area_for_microhub=CBD_area_for_microhub,
        number_of_CBD_deliveries=number_of_CBD_deliveries,
        number_of_non_CBD_deliveries=number_of_non_CBD_deliveries,
        number_of_deliveries=number_of_deliveries,
        CDD_share=CDD_share, failed_delivery_rate=failed_delivery_rate,

        diesel_van_cap=diesel_van_cap, electric_van_cap=electric_van_cap, cargo_bike_cap=cargo_bike_cap,
        diesel_van_speed=diesel_van_speed, electric_van_speed=electric_van_speed, cargo_bike_speed=cargo_bike_speed,
        loading_unloading_time=loading_unloading_time, Vehicels_daily_operating_hours=Vehicels_daily_operating_hours,

        small_parcel_frequency=small_parcel_frequency, medium_parcel_frequency=medium_parcel_frequency, large_parcel_frequency=large_parcel_frequency,
        diesel_van_operational_cost=diesel_van_operational_cost, electric_van_operational_cost=electric_van_operational_cost, bike_operational_cost=bike_operational_cost,
        diesel_van_external_cost=diesel_van_external_cost, electric_van_external_cost=electric_van_external_cost, bike_external_cost=bike_external_cost,
        diesel_van_daily_fixed_cost=diesel_van_daily_fixed_cost, electric_van_daily_fixed_cost=electric_van_daily_fixed_cost, bike_daily_fixed_cost=bike_daily_fixed_cost,

        Share_of_standard=Share_of_standard, Share_of_next_day=Share_of_next_day, Share_of_same_day=Share_of_same_day,
        r2=r2, NS=NS, E_vol=E_vol,
    )
    return ctx

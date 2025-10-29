# compute.py — pure logic; mirrors original formulas (now with Total_demand keys)
import pandas as pd
import math as _math  # fallback if ctx doesn't include math

def compute_round_result(round_id: int, current_series: pd.Series, columns, models, ctx) -> dict:
    # ---- sanitize + binarize
    current = current_series.reindex(columns).astype(float).copy()
    current["Share_of_diesel_vans"]   = max(0.0, min(100.0, current["Share_of_diesel_vans"]))
    current["Share_of_electric_vans"] = max(0.0, min(100.0, current["Share_of_electric_vans"]))
    for b in ["Microhub_delivery","Offpeak_delivery","Signature_required","Redelivery","Tracking","Insurance"]:
        current[b] = int(round(current[b])) if not pd.isna(current[b]) else 0
        current[b] = 1 if current[b] > 0 else 0

    # ---- probabilities
    current_df = pd.DataFrame([current], columns=columns)
    shippers_probability = models["calculate_probability_of_selecting_by_shippers"](
        models["shippers_beta_values"], current_df
    )
    recipients_probability = models["calculate_probability_of_selecting_by_recipients"](
        models["recipients_beta_values"], current_df
    )

    # ---- unpack
    Next_vs_standard_increase = float(current['Next_day_delivery_increase'])
    Same_vs_standard_increase = float(current['Same_day_delivery_increase'])
    Delivery_fee_small  = float(current['Delivery_fee_small'])
    Delivery_fee_Medium = float(current['Medium_parcels_delivery_fee'])
    Delivery_fee_Large  = float(current['Large_parcels_delivery_fee'])
    share_of_diesel   = float(current['Share_of_diesel_vans']) / 100.0
    share_of_electric = float(current['Share_of_electric_vans']) / 100.0
    micro_hub_delivery = int(current['Microhub_delivery'])
    Off_peak  = int(current['Offpeak_delivery'])
    Signature = int(current['Signature_required'])
    redelivery = int(current['Redelivery'])
    Tracking = int(current['Tracking'])
    Insurance = int(current['Insurance'])

    # ---- ctx aliases
    m = ctx.get("math") or _math
    total_area = ctx["total_area"]; CBD_area_for_microhub = ctx["CBD_area_for_microhub"]
    number_of_deliveries = ctx["number_of_deliveries"]; CDD_share = ctx["CDD_share"]
    failed_delivery_rate = ctx["failed_delivery_rate"]
    diesel_van_cap = ctx["diesel_van_cap"]; electric_van_cap = ctx["electric_van_cap"]; cargo_bike_cap = ctx["cargo_bike_cap"]
    diesel_van_speed = ctx["diesel_van_speed"]; electric_van_speed = ctx["electric_van_speed"]; cargo_bike_speed = ctx["cargo_bike_speed"]
    loading_unloading_time = ctx["loading_unloading_time"]; Vehicels_daily_operating_hours = ctx["Vehicels_daily_operating_hours"]
    small_parcel_frequency = ctx["small_parcel_frequency"]; medium_parcel_frequency = ctx["medium_parcel_frequency"]; large_parcel_frequency = ctx["large_parcel_frequency"]
    diesel_van_operational_cost = ctx["diesel_van_operational_cost"]; electric_van_operational_cost = ctx["electric_van_operational_cost"]; bike_operational_cost = ctx["bike_operational_cost"]
    diesel_van_external_cost = ctx["diesel_van_external_cost"]; electric_van_external_cost = ctx["electric_van_external_cost"]; bike_external_cost = ctx["bike_external_cost"]
    diesel_van_daily_fixed_cost = ctx["diesel_van_daily_fixed_cost"]; electric_van_daily_fixed_cost = ctx["electric_van_daily_fixed_cost"]; bike_daily_fixed_cost = ctx["bike_daily_fixed_cost"]
    Share_of_standard = ctx["Share_of_standard"]; Share_of_next_day = ctx["Share_of_next_day"]; Share_of_same_day = ctx["Share_of_same_day"]
    r2 = ctx["r2"]; NS = ctx["NS"]; E_vol = ctx["E_vol"]
    number_of_non_CBD_deliveries = ctx["number_of_non_CBD_deliveries"]

    # ---- Demand attraction (daily)
    total_carrier_demand_attraction = number_of_deliveries * recipients_probability * shippers_probability
    total_carrier_demand_attraction_standard = total_carrier_demand_attraction * Share_of_standard
    total_carrier_demand_attraction_next = total_carrier_demand_attraction * Share_of_next_day
    total_carrier_demand_attraction_same = total_carrier_demand_attraction * Share_of_same_day

    # ---- Collection split
    total_carrier_demand_attraction_standard_diesel   = total_carrier_demand_attraction_standard * share_of_diesel
    total_carrier_demand_attraction_standard_electric = total_carrier_demand_attraction_standard * share_of_electric
    total_carrier_demand_attraction_next_diesel       = total_carrier_demand_attraction_next * share_of_diesel
    total_carrier_demand_attraction_next_electric     = total_carrier_demand_attraction_next * share_of_electric
    total_carrier_demand_attraction_same_diesel       = total_carrier_demand_attraction_same * share_of_diesel
    total_carrier_demand_attraction_same_electric     = total_carrier_demand_attraction_same * share_of_electric

    # ---- Delivery demand
    total_carrier_demand_delivery_standard_diesel = (1 + failed_delivery_rate) * total_carrier_demand_attraction_standard_diesel
    total_carrier_demand_delivery_standard_electric = (1 + failed_delivery_rate) * total_carrier_demand_attraction_standard_electric
    total_carrier_demand_delivery_next_diesel = (1 + failed_delivery_rate) * total_carrier_demand_attraction_next_diesel
    total_carrier_demand_delivery_next_electric = (1 + failed_delivery_rate) * total_carrier_demand_attraction_next_electric
    total_carrier_demand_delivery_same_diesel = (1 + failed_delivery_rate) * total_carrier_demand_attraction_same_diesel
    total_carrier_demand_delivery_same_electric = (1 + failed_delivery_rate) * total_carrier_demand_attraction_same_electric
    total_carrier_demand_delivery_standard_bike = (1 + failed_delivery_rate) * total_carrier_demand_attraction_standard * micro_hub_delivery * (number_of_non_CBD_deliveries / number_of_deliveries)
    total_carrier_demand_delivery_next_bike = (1 + failed_delivery_rate) * total_carrier_demand_attraction_next * micro_hub_delivery * (number_of_non_CBD_deliveries / number_of_deliveries)
    total_carrier_demand_delivery_same_bike = (1 + failed_delivery_rate) * total_carrier_demand_attraction_same * micro_hub_delivery * (number_of_non_CBD_deliveries / number_of_deliveries)

    # ---- Revenue
    average_fee_standard = (Delivery_fee_small * small_parcel_frequency +
                            Delivery_fee_Medium * medium_parcel_frequency +
                            Delivery_fee_Large * large_parcel_frequency)
    Total_revenue = (total_carrier_demand_attraction_standard * average_fee_standard +
                     total_carrier_demand_attraction_next * average_fee_standard * (1 + Next_vs_standard_increase) +
                     total_carrier_demand_attraction_same * average_fee_standard * (1 + Same_vs_standard_increase))

    # ---- VKT collection
    VKT_collection_diesel = (2 * r2 * E_vol * (total_carrier_demand_attraction * share_of_diesel) / max(1e-9, diesel_van_cap) +
                             0.57 * m.sqrt(NS * total_area))
    VKT_collection_electric = (2 * r2 * E_vol * (total_carrier_demand_attraction * share_of_electric) / max(1e-9, electric_van_cap) +
                               0.57 * m.sqrt(NS * total_area))

    Time_collection_diesel = (VKT_collection_diesel / diesel_van_speed +
                              2 * loading_unloading_time * (total_carrier_demand_attraction * share_of_diesel))
    Time_collection_electric = (VKT_collection_electric / electric_van_speed +
                                2 * loading_unloading_time * (total_carrier_demand_attraction * share_of_electric))

    Fleet_collection_diesel = m.ceil(Time_collection_diesel / max(1e-9, Vehicels_daily_operating_hours))
    Fleet_collection_electric = m.ceil(Time_collection_electric / max(1e-9, Vehicels_daily_operating_hours))

    # ---- VKT delivery
    VKT_LMD_delivery_diesel = (2 * r2 * E_vol * (1 - micro_hub_delivery * CDD_share) * (1 + failed_delivery_rate) *
                               (total_carrier_demand_attraction * share_of_diesel) / max(1e-9, diesel_van_cap) +
                               0.57 * m.sqrt((1 - micro_hub_delivery * CDD_share) * (1 + failed_delivery_rate) *
                                             total_carrier_demand_attraction * share_of_diesel *
                                             (total_area - CBD_area_for_microhub)))
    VKT_LHT_delivery_diesel = 2 * r2 * E_vol * micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) * \
                              (total_carrier_demand_attraction * share_of_diesel) / max(1e-9, diesel_van_cap)

    VKT_LMD_delivery_electric = (2 * r2 * E_vol * (1 - micro_hub_delivery * CDD_share) * (1 + failed_delivery_rate) *
                                 (total_carrier_demand_attraction * share_of_electric) / max(1e-9, electric_van_cap) +
                                 0.57 * m.sqrt((1 - micro_hub_delivery * CDD_share) * (1 + failed_delivery_rate) *
                                               total_carrier_demand_attraction * share_of_electric *
                                               (total_area - CBD_area_for_microhub)))
    VKT_LHT_delivery_electric = 2 * r2 * E_vol * micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) * \
                                (total_carrier_demand_attraction * share_of_electric) / max(1e-9, electric_van_cap)

    VKT_LMD_delivery_bike = (2 * r2 * E_vol * micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) *
                             (total_carrier_demand_attraction) / max(1e-9, cargo_bike_cap) +
                             0.57 * m.sqrt(micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) *
                                           total_carrier_demand_attraction * CBD_area_for_microhub))

    Time_delivery_LMD_diesel = (VKT_LMD_delivery_diesel / diesel_van_speed +
                                2 * loading_unloading_time * (1 - micro_hub_delivery * CDD_share) * (1 + failed_delivery_rate) *
                                (total_carrier_demand_attraction * share_of_diesel))
    Time_delivery_LMD_electric = (VKT_LMD_delivery_electric / electric_van_speed +
                                  2 * loading_unloading_time * (1 - micro_hub_delivery * CDD_share) * (1 + failed_delivery_rate) *
                                  (total_carrier_demand_attraction * share_of_electric))
    Time_delivery_LHT_diesel = (VKT_LHT_delivery_diesel / diesel_van_speed +
                                2 * loading_unloading_time * micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) *
                                (total_carrier_demand_attraction * share_of_diesel))
    Time_delivery_LHT_electric = (VKT_LHT_delivery_electric / electric_van_speed +
                                  2 * loading_unloading_time * micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) *
                                  (total_carrier_demand_attraction * share_of_electric))
    Time_delivery_LMD_bike = (VKT_LMD_delivery_bike / cargo_bike_speed +
                              2 * loading_unloading_time * micro_hub_delivery * CDD_share * (1 + failed_delivery_rate) *
                              total_carrier_demand_attraction)

    Fleet_delivery_diesel = m.ceil((Time_delivery_LMD_diesel + Time_delivery_LHT_diesel) / max(1e-9, Vehicels_daily_operating_hours))
    Fleet_delivery_electric = m.ceil((Time_delivery_LMD_electric + Time_delivery_LHT_electric) / max(1e-9, Vehicels_daily_operating_hours))
    Fleet_delivery_bike = m.ceil(Time_delivery_LMD_bike / max(1e-9, Vehicels_daily_operating_hours))

    Total_costs = (
        diesel_van_operational_cost * (Time_collection_diesel + Time_delivery_LMD_diesel + Time_delivery_LHT_diesel) +
        electric_van_operational_cost * (Time_collection_electric + Time_delivery_LMD_electric + Time_delivery_LHT_electric) +
        bike_operational_cost * Time_delivery_LMD_bike +
        diesel_van_daily_fixed_cost * (Fleet_collection_diesel + Fleet_delivery_diesel) +
        electric_van_daily_fixed_cost * (Fleet_collection_electric + Fleet_delivery_electric) +
        bike_daily_fixed_cost * Fleet_delivery_bike
    )

    Total_emission = (
        diesel_van_external_cost * (VKT_collection_diesel + VKT_LMD_delivery_diesel + VKT_LHT_delivery_diesel) +
        electric_van_external_cost * (VKT_collection_electric + VKT_LMD_delivery_electric + VKT_LHT_delivery_electric) +
        bike_external_cost * VKT_LMD_delivery_bike
    )

    Total_profit = Total_revenue - Total_costs

    # ---- Period scaling (and demand denominators)
    periods = {60:'two_months', 365:'one_year', 1825:'five_year'}

    per = {f"Total_costs_{lbl}": Total_costs*days for days, lbl in periods.items()}
    per.update({f"Total_revenue_{lbl}": Total_revenue*days for days, lbl in periods.items()})
    per.update({f"Total_emission_{lbl}": Total_emission*days for days, lbl in periods.items()})
    per.update({f"Total_profit_{lbl}": Total_profit*days for days, lbl in periods.items()})
    per.update({f"Total_demand_{lbl}": total_carrier_demand_attraction*days for days, lbl in periods.items()})

    # Optional daily value for convenience / exports
    Total_demand = total_carrier_demand_attraction

    return {
        'Round ID': round_id,
        'Next_vs_standard_increase': Next_vs_standard_increase,
        'Same_vs_standard_increase': Same_vs_standard_increase,
        'Delivery_fee_small': Delivery_fee_small,
        'Delivery_fee_Medium': Delivery_fee_Medium,
        'Delivery_fee_Large': Delivery_fee_Large,
        'Diesel_van_share': share_of_diesel,
        'Electic_van_share': share_of_electric,  # keep original key for backward compatibility
        'Micro_hub_with_bike': micro_hub_delivery,
        'Off_peak_delivery': Off_peak,
        'Signature': Signature,
        'redlivery': redelivery,
        'Tracking': Tracking,
        'Insurance': Insurance,
        'Shipper_Probability': shippers_probability,
        'Recipient_Probability': recipients_probability,
        'Micro Hub Delivery': micro_hub_delivery,
        'Redelivery': redelivery,
        'Total_costs': Total_costs,
        'Total_revenue': Total_revenue,
        'Total_emission': Total_emission,
        'Total_profit': Total_profit,
        'Total_demand': Total_demand,  # <- daily demand (optional convenience)
        **per
    }

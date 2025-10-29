
import math
import pandas as pd
import biogeme.database as db
import biogeme.biogeme as bio
from biogeme import models
from biogeme.expressions import Beta, DefineVariable, log
from pathlib import Path

def run_recipients_choice_model(data_path):

    # Read the data
    df = pd.read_csv(str(data_path), delimiter=",")
    database = db.Database('Shipper_selection', df)
    globals().update(database.variables)
    
    # Parameters to be estimated
    ASC_accept = Beta('ASC_accept', 0, None, None, 0)
    ASC_reject = Beta('ASC_reject', 0, None, None, 1)
    B_Next_vs_standard_increase = Beta('B_Next_vs_standard_increase', 0, None, None, 0)
    B_Same_vs_standard_increase = Beta('B_Same_vs_standard_increase', 0, None, None, 0)
    # B_same_day = Beta('B_same_day', 0, None, None, 0)
    # B_next_day = Beta('B_next_day', 0, None, None, 0)
    # B_standard = Beta('B_standard', 0, None, None, 0)
    B_Delivery_fee_small = Beta('B_Delivery_fee_small', 0, None, None, 0)
    B_Delivery_fee_Medium = Beta('B_Delivery_fee_Medium', 0, None, None, 0)
    B_Delivery_fee_Large = Beta('B_Delivery_fee_Large', 0, None, None, 0)
    B_Diesel_van = Beta('B_Diesel_van', 0, None, None, 0)
    B_Electic_van = Beta('B_Electic_van', 0, None, None, 0)
    B_Micro_hub_with_bike = Beta('B_Micro_hub_with_bike', 0, None, None, 0)
    B_Off_peak = Beta('B_Off_peak', 0, None, None, 0)
    B_Signature = Beta('B_Signature', 0, None, None, 0)
    B_Redelivery = Beta('B_Redelivery', 0, None, None, 0)
    B_Collection = Beta('B_Collection', 0, None, None, 0)
    B_Tracking = Beta('B_Tracking', 0, None, None, 0)
    B_Insurance = Beta('B_Insurance', 0, None, None, 0)
    
    # Definition of new variables
    Next_day_delivery_increase = DefineVariable('Next_day_delivery_increase', Next_vs_standard_increase, database)
    Same_day_delivery_increase = DefineVariable('Same_day_delivery_increase', Same_vs_standard_increase, database)
    # Standard_delivery = DefineVariable('Standard_delivery', Order_fulfillment_type ==3, database)
    Small_parcels_delivery_fee = DefineVariable('Small_parcels_delivery_fee', Delivery_fee_small, database)
    Medium_parcels_delivery_fee = DefineVariable('Medium_parcels_delivery_fee', Delivery_fee_Medium, database)
    Large_parcels_delivery_fee = DefineVariable('Large_parcels_delivery_fee', Delivery_fee_Large, database)
    Share_of_diesel_vans = DefineVariable('Share_of_diesel_vans', Diesel_van, database)
    Share_of_electric_vans = DefineVariable('Share_of_electric_vans', Electic_van, database)
    Microhub_delivery = DefineVariable('Microhub_delivery', Micro_hub_with_bike== 1, database)
    Offpeak_delivery = DefineVariable('Offpeak_delivery', Off_peak== 1, database)
    Signature_required = DefineVariable('Signature_required', Signature == 1, database)
    Redelivery = DefineVariable('Redelivery', Failed_approach== 1, database)
    Collection = DefineVariable('Collection', Failed_approach== 2, database)
    With_tracking = DefineVariable('With_tracking', Tracking== 1, database)
    With_insurance = DefineVariable('With_insurance', Insurance== 1, database)
    
    # Definition of the utility functions
    V1 = (ASC_accept
        + B_Next_vs_standard_increase * Next_day_delivery_increase
        + B_Same_vs_standard_increase * Same_day_delivery_increase 
        # + B_standard * Standard_delivery
        + B_Delivery_fee_small * Small_parcels_delivery_fee
        + B_Delivery_fee_Medium * Medium_parcels_delivery_fee
        # + B_Delivery_fee_Large * Large_parcels_delivery_fee
        + B_Diesel_van * Share_of_diesel_vans
        # + B_Electic_van * Share_of_electric_vans
        + B_Micro_hub_with_bike * Microhub_delivery
        + B_Off_peak * Offpeak_delivery
        + B_Signature * Signature_required
        + B_Redelivery * Redelivery
        # + B_Collection * Collection
        + B_Tracking * With_tracking
        + B_Insurance * With_insurance
        )
    
    V2 = ASC_reject
    
    # Associate utility functions with the numbering of alternatives
    V = {1: V1, 0: V2}
    
    # Associate the availability conditions with the alternatives
    av = {1: Option, 0: Option}
    
    # Definition of the model. This is the contribution of each
    # observation to the log likelihood function.
    prob = models.logit(V, av, Choice_recipient)
    logprob=log(prob)
    
    # Create the Biogeme object
    biogeme = bio.BIOGEME(database, logprob)
    biogeme.modelName = 'Shipper_selection'
    
    # Calculate the null log likelihood for reporting.
    biogeme.calculateNullLoglikelihood(av)
    
    # Estimate the parameters
    results = biogeme.estimate()
    
    # Return beta values and the database
    beta_values = results.getBetaValues()
    stats_logit_recipient = results.getGeneralStatistics()
    pandasResults_recipient = results.getEstimatedParameters()
    
    return {"beta_values": beta_values, "database": database, "data": df,"pandasResults_recipient":pandasResults_recipient}



def calculate_probability_of_selecting_by_recipients(beta_values, observation):

    utility_new = (
        beta_values['ASC_accept']
        + beta_values['B_Next_vs_standard_increase'] * int(observation['Next_day_delivery_increase'])
        + beta_values['B_Same_vs_standard_increase'] * int(observation['Same_day_delivery_increase'])

        + beta_values['B_Delivery_fee_small'] * float(observation['Delivery_fee_small'])
        + beta_values['B_Delivery_fee_Medium'] * float(observation['Medium_parcels_delivery_fee'])
        + beta_values['B_Diesel_van'] * observation['Share_of_diesel_vans']
        + beta_values['B_Micro_hub_with_bike'] * observation['Microhub_delivery']
        
        + beta_values['B_Off_peak'] * observation['Offpeak_delivery']
        + beta_values['B_Insurance'] * observation['Insurance']
        + beta_values['B_Tracking'] * observation['Tracking']
        + beta_values['B_Redelivery'] * observation['Redelivery']
        + beta_values['B_Signature'] * observation['Signature_required']
    )

    probability = 1 / (1 + math.exp(-utility_new))
    return probability
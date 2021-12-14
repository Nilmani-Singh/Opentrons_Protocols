import csv 
import os
import pandas as pd


metadata = {
    'protocolName': 'Primer dilution to 10uM',
    'author': 'Nilmani <nsingh16@illinois.edu>',
    'source': 'Protocol Library',
    'apiLevel': '2.8'
    }


def run(protocol_context):

    # Transfer the stock primers from IDT 384-well plate to Corning 384-well plate and dilute to 10uM.
    # The corning 384-well plate will be used in ECHO liquid handler as source plate.
    
    # primer_plate = protocol_context.load_labware("nest_96_wellplate_2ml_deep", '5', 'Primer')

    water_plate = protocol_context.load_labware("agilent_1_reservoir_290ml", '8', 'Water')
    primer_plate = protocol_context.load_labware("corning_384_wellplate_112ul_flat", '5', 'Primers')
    d_plate = protocol_context.load_labware("corning_384_wellplate_112ul_flat", '6', 'Destination')

    ################# Define Pipettes and Tip racks #############################
    slots2 = ["2", "3", "4"][:3]
    tipracks2 = [ protocol_context.load_labware("opentrons_96_tiprack_300ul", slot)  for slot in slots2  ]
    pipette_200 = protocol_context.load_instrument("p300_single_gen2", "right", tip_racks=tipracks2)
    ###################

    pipette_200.default_speed = 200


    # The picklist for adding water to DNA oligos, needs to be copied to Opentrons through SSH
    # The picklist contains "Source Well" "Destination Well" and "Volume" as column
    working_directory = "/data/user_storage"
    filename = working_directory + '/Picklist_primer_dilution.csv'
    picklist_df = pd.read_csv(filename)

    water_source = water_plate.wells_by_name()['A1'].bottom(5)
    water_volume = 54
    primer_volume = 6
    # The maximum volume of liquid in each well is 65ul for ECHO source plate

    pipette_200.pick_up_tip()
    protocol_context.max_speeds['Z'] = 30 

    # Adding water first to all wells 
    for index, row in picklist_df.iterrows():
        Water_dest = picklist_df["Destination Well"].loc[index]
        Water_dest_Well = d_plate.wells_by_name()[Water_dest].bottom(4)
        pipette_200.transfer(water_volume, water_source, Water_dest_Well, new_tip='never')

    pipette_200.drop_tip()
    
    protocol_context.pause("Centrifuge the corning 384 well plate")

    # Transfer primers  to corning 384 well plate
    for index, row in picklist_df.iterrows():
        Primer_dest = picklist_df["Destination Well"].loc[index]
        Primer_dest_well = d_plate.wells_by_name()[Primer_dest].bottom(2)

        Primer_source = picklist_df["Source Well"].loc[index]
        Primer_source_well = d_plate.wells_by_name()[Primer_source].bottom(2)

        pipette_200.transfer(primer_volume, Primer_source_well, Primer_dest_well, air_gap=10, new_tip='always', 
        blow_out=True, blowout_location='destination well')



import csv 
import os
import pandas as pd

metadata = {
    'protocolName': 'Dilute Primers in 384well and 96-well plate',
    'author': 'Nilmani <nsingh16@illinois.edu>',
    'source': 'Protocol Library',
    'apiLevel': '2.8'
    }


def run(protocol_context):

    # This protocols is for  diluting primers that were received in 384well plate and 96-well from IDT.
    # The Opentrons must contain the plate defintion for correct type of 384-well and 96-well plate.
    # This protocol can add different volumes of water to different wells of the plate

    # create labware
    s_plate = protocol_context.load_labware("agilent_1_reservoir_290ml", '8', 'Source')
    Oligos_plate_1 = protocol_context.load_labware("usascientific_96_wellplate_2.4ml_deep", '5', 'Oligos_1')
    Oligos_plate_2 = protocol_context.load_labware("corning_384_wellplate_112ul_flat", '6', 'Oligos_2')

    ################# Define Pipettes and Tip racks #############################

    slots2 = ["2", "3", "4"][:3]
    tipracks2 = [ protocol_context.load_labware("opentrons_96_tiprack_300ul", slot)  for slot in slots2  ]
    pipette_200 = protocol_context.load_instrument("p300_single_gen2", "right", tip_racks=tipracks2)
   
    ###################

    pipette_200.default_speed = 200
    
    # The picklist for adding water to DNA oligos, needs to be copied to Opentrons through SSH
    # The picklist contains "Destination Well" and "Volume" as column
    working_directory = "/data/user_storage"   # Copy the picklist here in Opentrons
    filename = working_directory + '/Picklist_Oligos_1.csv'
    picklist_oligos_1 = pd.read_csv(filename)

    # when diluting primers, get water from reservoir
    source = s_plate.wells_by_name()['A1'].bottom(6)
    
    # Adding water to 1st plate
    pipette_200.pick_up_tip()
    protocol_context.max_speeds['Z'] = 30 #Slow down the Z speed

    for index, row in picklist_oligos_1.iterrows():
        dest_well = picklist_oligos_1["Destination Well"].loc[index]
        d_well =    Oligos_plate_1.wells_by_name()[dest_well].top(-6)
        volume = float(picklist_oligos_1["Volume"].loc[index])
        
        pipette_200.transfer(volume, source, d_well, new_tip = 'never')
        # Not chnaging tips during adding water from top of the well

            
    del protocol_context.max_speeds['Z']

    pipette_200.drop_tip()
    del picklist_guide

    # Adding water to 2nd plate
    filename2 = working_directory + '/Picklist_Oligos_2.csv'
    picklist_oligos_2 = pd.read_csv(filename2)
    pipette_200.pick_up_tip()
    protocol_context.max_speeds['Z'] = 30

    for index, row in picklist_oligos_2.iterrows():
        dest_well = picklist_oligos_2["Destination Well"].loc[index]
        d_well =    Oligos_plate_2.wells_by_name()[dest_well].top(-6)
        volume = float(picklist_oligos_2["Volume"].loc[index])
        
        pipette_200.transfer(volume, source, d_well, new_tip = 'never')
            
    del protocol_context.max_speeds['Z']

    pipette_200.drop_tip()


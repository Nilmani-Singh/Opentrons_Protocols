import json
import math
from opentrons import protocol_api

metadata = {
    "protocolName": "PCR clean up using Omega magbind kit",
    "author": "Nilmani <nsingh16@illinois.edu>",
    "source": "Protocol Library",
    "apiLevel": "2.8",
}


def get_values(*names):

    dict1 = dict()

    dict1["sample_number"] = 8
    dict1["PCR_volume"] = 50
    dict1["bead_ratio"] = 1.8   # bead ration to PCR volume
    dict1["elution_vol"] = 50
    dict1["mag_delay"] = 6  # How long will the magnet be active

    _all_values = dict1

    return [_all_values[n] for n in names]


def run(protocol_context):

    # PCR clean up kit: Omega RxnPlus PCR clean up #M1386
    # This protocol is designed for running only 8 wells

    [sample_number, PCR_volume, bead_ratio, elution_vol, mag_delay] = get_values(
        "sample_number", "PCR_volume", "bead_ratio", "elution_vol", "mag_delay"
    )
    
    ######## Define Labware ###################

    mag_deck = protocol_context.load_module("magnetic module gen2", "1")
    mag_deck.disengage()

    temp_mod = protocol_context.load_module("temperature module gen2", "10")
    temp_mod.set_temperature(55)  # set the temperature to 55 C
 
    mag_plate = mag_deck.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    output_plate = protocol_context.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "2", "Output")
   
   
    ######## Define reagents and liquid waste   ########

    reagent_container = protocol_context.load_labware("usascientific_12_reservoir_22ml", "7", "reagent reservoir")
    #MagBeads = reagent_container.wells_by_name()["A1"] # Adding the magnetic beads manually on bench
    Ethanol   = reagent_container.wells_by_name()["A5"]
    Elution_buffer = reagent_container.wells_by_name()["A1"]

    w_container = protocol_context.load_labware("agilent_1_reservoir_290ml", "8", "Liquid Waste")
    Waste_container   =  w_container.wells_by_name()['A1']


    ################# Define Pipettes and Tip racks #############################
    tiprack_num = 2 
    slots = ["3", "4"][:tiprack_num]

    tipracks = [ protocol_context.load_labware("opentrons_96_filtertiprack_200ul", slot)  for slot in slots  ]
    pipette_200ul = protocol_context.load_instrument("p300_multi_gen2", "left", tip_racks=tipracks)

    ##################### WELLs TO PROCESS ###########################

    #col_num = math.ceil(sample_number / 8) 
    #samples = [col for col in mag_plate.rows()[0][:col_num]]
    samples = [mag_plate.wells_by_name()['A4']]  # Add the first well of the column you want to run PCR clean up
    #output = [col for col in output_plate.rows()[0][:col_num]]
    output =  [output_plate.wells_by_name()['A5']]
        
    ###################### DEFINE VOLUMES ##############################
    bead_vol = int(PCR_volume * bead_ratio)
    Mix_vol = (bead_vol + PCR_volume - 20)
    transfer1 = (PCR_volume + bead_vol) - 20
    zspeed = 25

    ############ LET'S BEGIN ################

    pipette_200ul.flow_rate.aspirate = 200
    pipette_200ul.flow_rate.dispense = 200
    pipette_200ul.pick_up_tip()

    for target in samples:

        protocol_context.max_speeds['Z'] = zspeed 

        pipette_200ul.flow_rate.aspirate = 100
        pipette_200ul.flow_rate.dispense = 100
        protocol_context.comment("Mix and Incubate for  5  minutes")

        for i in range(2):
            protocol_context.delay(minutes=1.5)  # Incubate for 1.5 minutes
            pipette_200ul.mix(20, Mix_vol, target.bottom(1.5)) # mix between the incubation
            pipette_200ul.move_to(target.top(10))

        del protocol_context.max_speeds['Z']
        protocol_context.delay(minutes=1.5)

        protocol_context.comment("Magnetic module turned on for  " + str(mag_delay) + " minutes" )
        mag_deck.engage()  # the height of magnetic module will be adjusted automatically
        protocol_context.delay(minutes=mag_delay)  # wait for mag_delay min
        
        ########### REMOVE SUPERNATANT ##################
        protocol_context.comment("Removing supernatant ")    
            
        pipette_200ul.flow_rate.aspirate = 50
        pipette_200ul.flow_rate.dispense = 200
                
        protocol_context.max_speeds['Z'] = zspeed
        pipette_200ul.transfer(transfer1, target.bottom(1.5), Waste_container.bottom(30), new_tip="never")
        del protocol_context.max_speeds['Z']

    pipette_200ul.drop_tip()

    protocol_context.comment("Wash with 150ul 70 Ethanol for 3 times ")

    for i in range(3):
        pipette_200ul.flow_rate.aspirate = 100
        pipette_200ul.flow_rate.dispense = 100
        pipette_200ul.pick_up_tip()

        protocol_context.max_speeds['Z'] = zspeed

        for target in samples:
            
            pipette_200ul.transfer(150, Ethanol.bottom(5), target.top(-1), new_tip="never", air_gap=5)
            protocol_context.delay(minutes=0.5)

            pipette_200ul.transfer(140, target.bottom(2), Waste_container.bottom(30), new_tip="never", air_gap=20)
            pipette_200ul.blow_out(Waste_container.bottom(30))

            if i == 2:
                pipette_200ul.transfer(50, target.bottom(1.5), Waste_container.bottom(30), new_tip="never", air_gap=20)
                pipette_200ul.transfer(20, target.bottom(0.5), Waste_container.bottom(30), new_tip="never", air_gap=20)

        pipette_200ul.drop_tip()
                       
        del protocol_context.max_speeds['Z']

    protocol_context.comment("let it dry at 55 C for >5 minutes " )
    
    mag_deck.disengage()
    protocol_context.comment('Move to 55C temp module for 5 minutes to dry off any residual ethanol')
    protocol_context.comment('Put it back to magnetic plate when finished')
    protocol_context.home()
    protocol_context.pause()
    
    protocol_context.comment("Add elution buffer and then incubate for 5 minutes ")

    for target in samples:
        pipette_200ul.flow_rate.aspirate = 50
        pipette_200ul.flow_rate.dispense = 80
        pipette_200ul.pick_up_tip()
        
        protocol_context.max_speeds['Z'] = zspeed

        pipette_200ul.transfer(elution_vol, Elution_buffer.bottom(6), target.bottom(2), new_tip="never")
        pipette_200ul.mix(15, 40, target.bottom(1.5))
        pipette_200ul.mix(15, 40, target.bottom())
        pipette_200ul.move_to(target.top(5))
        protocol_context.delay(minutes=2)
        pipette_200ul.mix(10, 40, target.bottom(1.5)) 
        pipette_200ul.mix(10, 40, target.bottom(1))   
        
        del protocol_context.max_speeds['Z']

        pipette_200ul.drop_tip()
    
    temp_mod.set_temperature(55)
    protocol_context.delay(minutes=0.5)
    
    protocol_context.comment("Transfer to heating plate at 55C for better yield")
    protocol_context.comment('Put it back to magnetic plate when finished')
    protocol_context.pause()

    protocol_context.comment("Turn on magnets, wait for beads to settle ")

    mag_deck.engage()
    mag_delay = mag_delay + 2
    protocol_context.delay(minutes = mag_delay)

    out_vol = (elution_vol - 5)
    for target, dest in zip(samples, output):
        pipette_200ul.flow_rate.aspirate = 50
        pipette_200ul.flow_rate.dispense = 50
        pipette_200ul.pick_up_tip()
        
        protocol_context.max_speeds['Z'] = zspeed
        pipette_200ul.transfer(out_vol, target.bottom(1), dest.bottom(5), new_tip="never", air_gap=2)
        pipette_200ul.blow_out(dest.top(-5))
        
        del protocol_context.max_speeds['Z']

        pipette_200ul.drop_tip()

        

    mag_deck.disengage()
    temp_mod.deactivate()
    protocol_context.home()
 
    protocol_context.comment("Finished")


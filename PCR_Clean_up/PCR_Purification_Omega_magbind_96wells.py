import json
import math
from opentrons import protocol_api

metadata = {
    "protocolName": "Omega RxnPlus PCR clean up M1386 ",
    "author": "Nilmani <nsingh16@illinois.edu>",
    "source": "Protocol Library",
    "apiLevel": "2.8",
}


def get_values(*names):

    dict1 = dict()

    dict1["sample_number"] = 96
    dict1["PCR_volume"] = 50
    dict1["bead_ratio"] = 1.8
    dict1["elution_vol"] = 50
    dict1["mag_delay"] = 6  # How long will the magnet be active
    dict1["Incubattion_time"] = 0.5

    _all_values = dict1

    return [_all_values[n] for n in names]


def run(protocol_context):

    # PCR clean up kit: Omega RxnPlus PCR clean up #M1386
    # This protocol is designed for all 96-wells of PCR plate
    # Runtime for this protocl is 2-3 hours

    [sample_number, PCR_volume, bead_ratio, elution_vol, mag_delay, Incubattion_time] = get_values(
        "sample_number", "PCR_volume", "bead_ratio", "elution_vol", "mag_delay", "Incubattion_time"
    )

    mag_deck = protocol_context.load_module("magnetic module gen2", "1")
    mag_deck.disengage()

    temp_mod = protocol_context.load_module("temperature module gen2", "10")
    temp_mod.set_temperature(55)  # set the temperature to 55 C
 
    mag_plate = mag_deck.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    output_plate = protocol_context.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "2", "Output")
   
   
    # Define reagents and liquid waste

    reagent_container = protocol_context.load_labware("usascientific_12_reservoir_22ml", "7", "reagent reservoir")
    MagBeads = reagent_container.wells_by_name()["A1"]
    Elution_buffer = reagent_container.wells_by_name()["A3"]


    E_container = protocol_context.load_labware("agilent_1_reservoir_290ml", "9", "Etahnol reservoir")
    Ethanol_container = E_container.wells_by_name()['A1']
    
    w_container = protocol_context.load_labware("agilent_1_reservoir_290ml", "8", "Liquid Waste")
    Waste_container   =  w_container.wells_by_name()['A1']


    ###############################################################################
    #tiprack_num = 4  # Number of tipracks being used
    #slots = ["3", "4", "5", "6"][:tiprack_num]
    # Since, I need to reset the tipracks in this run, declaring them this way is helpful later.

    tiprack_1 = protocol_context.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack_2 = protocol_context.load_labware('opentrons_96_tiprack_300ul', 4)
    tiprack_3 = protocol_context.load_labware('opentrons_96_tiprack_300ul', 5)
    tiprack_4 = protocol_context.load_labware('opentrons_96_tiprack_300ul', 6)
    tipracks = [tiprack_1, tiprack_2, tiprack_3, tiprack_4]

    # load pipette with tip racks
    pipette = protocol_context.load_instrument("p300_multi_gen2", "left", tip_racks=tipracks)

    col_num = math.ceil(sample_number / 8) 
    samples = [col for col in mag_plate.rows()[0][:col_num]]    
    samples_top = [well.top() for well in mag_plate.rows()[0][:col_num]]
    output = [col for col in output_plate.rows()[0][:col_num]]
    ##########################################################################################

    bead_vol = int(PCR_volume * bead_ratio)
    Mix_vol = (bead_vol + PCR_volume - 20)
    transfer1 = (PCR_volume + bead_vol)
    counter = 0
    zspeed = 25

    ##### REAGENTS AMOUNT REQUIRED #### 
    total_beads =  math.ceil((bead_vol * (sample_number+10))/1000) + 2
    Total_Ethanol = math.ceil((150 * (sample_number+10))/1000) + 2
    Total_Elution =  math.ceil((50 * (sample_number+10))/1000) + 2
    protocol_context.comment(' Make sure that you have filled more than the volume required for finishing all assays')
    protocol_context.comment(' Magnetic Beads buffer :-  ' +str(total_beads)+' ml')
    protocol_context.comment(' Total Ethanol :-  ' + str(Total_Ethanol)+' ml')
    protocol_context.comment(' Total Elution buffer :-  ' + str(Total_Elution)+ ' ml')

    protocol_context.pause()
    protocol_context.comment('Press resume if reagents volumes are enough for the assay')


    ############## ADD MAGNETIC BEADS ##########
    pipette.reset_tipracks()
    pipette.starting_tip = tiprack_1.well('A1')

    pipette.flow_rate.aspirate = 200
    pipette.flow_rate.dispense = 200
    pipette.pick_up_tip()
    protocol_context.comment("Adding magbeads to PCR ")

    for target in samples:

        if counter == 0:
            pipette.mix(10, 200, MagBeads.bottom(5))  # Mix the meagbead solution
        else:
            pipette.mix(1, 200, MagBeads.bottom(5))
        counter = counter + 1
        
        pipette.transfer(bead_vol, MagBeads.bottom(5), target.top(-1), new_tip="never")  # 1. Add magbead buffer to PC
        
    pipette.return_tip()  # return to original position
    #pipette.drop_tip()   # for testing no need to drop tip

    pipette.reset_tipracks()
    pipette.starting_tip = tiprack_1.well('A1')

    protocol_context.comment("Mixing magbeads with PCR ")

    for target in samples:

        pipette.flow_rate.aspirate = 100
        pipette.flow_rate.dispense = 100
        pipette.pick_up_tip()
        
        protocol_context.max_speeds['Z'] = zspeed
        pipette.mix(15, Mix_vol, target.bottom(1))  # Mix the resuspension soln
        del protocol_context.max_speeds['Z']

        pipette.return_tip()  # No need to discard these tips right now, these will be re-used
        #pipette.drop_tip()


    protocol_context.delay(minutes=Incubattion_time)  # Incubate for XX minutes
    protocol_context.comment("Incubating for  5  minutes")

    mag_deck.engage()  # the height of magnetic module is adjusted automatically

    protocol_context.delay(minutes=mag_delay)  # wait for 5 min then mix slowly
    protocol_context.comment("Magnetic module turned on and incubating for  " + str(mag_delay) + "   minutes  " )

    ############# REMOVE SUPERNATANT #################
    protocol_context.comment("  Removing supernatant ")
    pipette.reset_tipracks()
    pipette.starting_tip = tiprack_1.well('A1')

    for target in samples:
        pipette.flow_rate.aspirate = 50
        pipette.flow_rate.dispense = 200
        pipette.pick_up_tip()
        
        protocol_context.max_speeds['Z'] = zspeed
        pipette.aspirate((transfer1-5), target.bottom(1), rate = 1)        
        del protocol_context.max_speeds['Z']

        pipette.dispense(transfer1, Waste_container.bottom(30), rate = 1)
        pipette.blow_out(Waste_container)
        pipette.blow_out(Waste_container)

        pipette.return_tip()
        #pipette.drop_tip()

    #################### ETHANOL WASH #######################
    protocol_context.comment("Add 150ul 70ethanol twice and subsequently discard it ")
    

    for i in range(2):

        pipette.reset_tipracks()
        pipette.starting_tip = tiprack_2.well('A1')

        pipette.flow_rate.aspirate = 100
        pipette.flow_rate.dispense = 100
        pipette.pick_up_tip()

        counter2 = 0

        for target in samples:

            if (i == 1) and (counter2 == 0):
                for j in range(5):
                    pipette.transfer(200, Ethanol_container, Waste_container, new_tip='never', air_gap= 10)
                counter2 = counter2 + 1

            pipette.aspirate(150, Ethanol_container.bottom(4), rate = 1)

            protocol_context.max_speeds['Z'] = zspeed            
            pipette.dispense(150, target.top(-1), rate = 1)
            del protocol_context.max_speeds['Z']

        pipette.return_tip()

        pipette.reset_tipracks()
        pipette.starting_tip = tiprack_2.well('A1')
       
        for target in samples:            
            pipette.flow_rate.aspirate = 50
            pipette.flow_rate.dispense = 100
            pipette.pick_up_tip()

            protocol_context.max_speeds['Z'] = zspeed 
            pipette.aspirate(140, target.bottom(3), rate = 1)
            del protocol_context.max_speeds['Z']

            pipette.dispense(140, Waste_container.bottom(30), rate = 1)
            protocol_context.delay(minutes=0.02)
            pipette.blow_out(Waste_container)
            
            if i == 1:
                protocol_context.max_speeds['Z'] = zspeed 
                pipette.aspirate(30, target.bottom(0.5), rate = 0.5)
                del protocol_context.max_speeds['Z']

                pipette.dispense(30, Waste_container.bottom(30), rate = 1)
                protocol_context.delay(minutes=0.02)
                pipette.blow_out(Waste_container)
                                  
            pipette.return_tip()  # return to original position
            # pipette.drop_tip()  #for testing no need to drop tip
        

    protocol_context.comment("Advisable to let it dry at 55 C for >3 minutes " )
     
    mag_deck.disengage()

    protocol_context.comment('Move to 55 C temp module for 5 minutes to dry off any residual ethanol')
    protocol_context.comment('Put it back to magnetic plate when finished')
    protocol_context.pause()


    ############### ELUTION #####################
    protocol_context.comment("Add elution buffer and then incubate for 5 minutes ")
    
    pipette.reset_tipracks()
    pipette.starting_tip = tiprack_3.well('A1')
    pipette.flow_rate.aspirate = 50
    pipette.flow_rate.dispense = 100
    pipette.pick_up_tip()

    for target in samples:
        
        pipette.aspirate(50, Elution_buffer.bottom(5), rate = 1)
        protocol_context.max_speeds['Z'] = zspeed
        pipette.dispense(50, target.top(-2), rate=1)
        pipette.blow_out(target.top(-2))
        del protocol_context.max_speeds['Z']
    pipette.return_tip()

    pipette.reset_tipracks()
    pipette.starting_tip = tiprack_3.well('A1')
    pipette.flow_rate.aspirate = 100
    pipette.flow_rate.dispense = 100


    for target in samples:
        pipette.pick_up_tip()

        protocol_context.max_speeds['Z'] = zspeed
        pipette.mix(10, 40, target.bottom(1))
        pipette.mix(10, 45, target.bottom(0.5))

        del protocol_context.max_speeds['Z']

        pipette.return_tip()  # return to original position
        # pipette.drop_tip()  #for testing no need to drop tip


    protocol_context.delay(minutes=Incubattion_time)
    
    temp_mod.set_temperature(55)
    protocol_context.comment("Transfer to heating plate 55 C for ~2 min ")
    protocol_context.comment('Put it back to magnetic plate when finished')
    protocol_context.pause()

    protocol_context.comment("Turn on magnets, wait for beads to settle ")

    mag_deck.engage()
    mag_delay = mag_delay + 2
    protocol_context.delay(minutes = mag_delay)

    pipette.reset_tipracks()
    pipette.starting_tip = tiprack_4.well('A1')
    pipette.flow_rate.aspirate = 50
    pipette.flow_rate.dispense = 50
    
    out_vol = (elution_vol - 5)

    for target, dest in zip(samples, output):

        pipette.pick_up_tip()
        
        protocol_context.max_speeds['Z'] = zspeed
        pipette.transfer(out_vol, target.bottom(1), dest.bottom(5), new_tip="never", air_gap=10)   
        pipette.blow_out(dest.top(-5))     
        del protocol_context.max_speeds['Z']

        pipette.return_tip()
       

    mag_deck.disengage()
    temp_mod.deactivate()
    protocol_context.home() 
    protocol_context.comment("Finished")


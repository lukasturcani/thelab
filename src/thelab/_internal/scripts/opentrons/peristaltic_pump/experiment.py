# This Python script controls the movement of a Gen-2 pipette to aspirate and dispense sample.
# The tips are not physically picked-up by the pipette.
# The protocol includes sample aspiration, a simulated wash cycle and NMR analysis steps.

import sys
from opentrons import protocol_api

metadata = {
    'protocolName': 'Peristaltic Pump Experiment',
    'author': 'Vithusiga Maheswaran <vm1022@ic.ac.uk>',
    'description': '24-well plate using Opentrons',
    'apiLevel': '2.3'
}

# Functions of the protocol run.
def run(protocol: protocol_api.ProtocolContext):

    # Gantry speed setting
    protocol.max_speeds['X'] = 200                                                  # Slowing down the speed of gantry
    protocol.max_speeds['Y'] = 200
    protocol.max_speeds['Z'] = 200

    # Labware
    plate = protocol.load_labware('greenawaylab_24_wellplate_8000ul', 1)            # 24 well plate
    wash_station = protocol.load_labware('opentronspump_96_tiprack_300ul', 3)       # A mimic of a 96 tip rack for a wash plate
    pause = protocol.load_labware('opentronspump_96_tiprack_300ul', 2)

    # Single Gen-2 pipette
    pipette = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=[wash_station])

    # Positions of a 24 well plate
    wells_in_plate = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
                      'B1', 'B2', 'B3', 'B4', 'B5', 'B6',
                      'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
                      'D1', 'D2', 'D3', 'D4', 'D5', 'D6']

    # Commands in the protocol
    pipette.pick_up_tip()                                                           # The pipette picks up the tip and moves to the first well of the plate to aspirate sample. The tip is not physically picked up though.
    for well in wells_in_plate:
        pipette.aspirate(20, plate[well])                                           # Aspiration of sample
        protocol.delay(seconds = 22)                                                # Protocol paused for 21 seconds, allowing pump to finish its cycle
        pipette.dispense(20, pause['B2'])                                           # Protocol goes to slot 2 to dispense the remaining sample in the tube

        protocol.delay(seconds = 72)                                                # Dispense the remainder and the last 30 seconds used for NMR analysis

        pipette.aspirate(20, wash_station['B2'])                                    # Wash cycle commences
        protocol.delay(seconds=120)                                                 # Peristaltic pump solvent through 6 times at the wash station
        pipette.dispense(20, pause['B2'])                                           # Gantry moves away from the wash plate to slot 2
        protocol.delay(seconds = 60)                                                # Peristaltic pump dispenses the remaining solvent
    pipette.drop_tip()

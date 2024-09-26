# ruff: noqa: T201
# Code for the experimental procedure used when testing the magnetic stirrer
# module on the OT-2. The experiment involved mixing the isomer cages of CC3-R
# and CC3-S to form a racemic mixture

import serial
from opentrons import protocol_api

# metadata
metadata = {
    "protocolName": "Magnetic_Stirring_Experiment",
    "author": "Pratik Gor <pratik.gor21@imperial.ac.uk>",
    "description": "24 Well-plate of CC3-R and CC3-S cage mixing",
    "apiLevel": "2.12",
}

# connects the magnetic stirrer module via serial USB connection
try:
    ser = serial.Serial("/dev/ttyACM0", 115200)  # open serial port
except:
    ser = serial.Serial("/dev/ttyACM1", 115200)


# clears all previous serial data stored in the USB port
ser.flushInput()
ser.flushOutput()


# protocol run function. the part after the colon lets your editor know
# where to look for autocomplete suggestions
def run(protocol: protocol_api.ProtocolContext) -> None:  # noqa: PLR0915
    # set gantry speeds (default = 400 mm/s)
    protocol.max_speeds["X"] = 200
    protocol.max_speeds["Y"] = 200
    protocol.max_speeds["Z"] = 200

    # labware
    tiprack300 = protocol.load_labware("opentrons_96_tiprack_300ul", 11)
    stirrer = protocol.load_labware("magnetic_stirrer_24wellplate_8000ul", 2)
    stock = protocol.load_labware("fisher_6_wellplate_25000ul", 7)

    # pipettes
    right_pipette = protocol.load_instrument(
        "p300_single_gen2", "left", tip_racks=[tiprack300]
    )

    # commands
    right_pipette.flow_rate.aspirate = 70
    right_pipette.flow_rate.dispense = 70
    right_pipette.pick_up_tip()
    right_pipette.aspirate(100, stock["A1"])  # Dispensing CC3-R
    protocol.delay(seconds=10)  # let it swell
    right_pipette.move_to(stock["A1"].top())
    right_pipette.dispense(100, stock["A1"].top(z=2))
    # .top(z=2) allows the pipette to dispense from 2mm above the vial to avoid
    # cross-contamination

    # 225 ul from stock A1 (CC3-R) to each vial in plate
    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A1"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A2"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A3"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A4"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A5"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A6"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B1"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B2"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B3"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B4"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B5"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B6"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C1"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C2"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C3"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C4"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C5"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C6"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D1"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D2"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D3"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D4"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D5"].top(z=2))

    right_pipette.aspirate(225, stock["A1"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D6"].top(z=2))

    right_pipette.drop_tip()

    # flushes all serial data
    ser.flushInput()
    # input data to turn the magnetic stirrer on
    datatosend = "1\n"
    bytedata = datatosend.encode("utf-8")
    ser.write(bytedata)  # writes the encoded data to the serial port
    # stirring is now on

    right_pipette.flow_rate.aspirate = 70
    right_pipette.flow_rate.dispense = 70
    right_pipette.pick_up_tip()
    right_pipette.aspirate(100, stock["A2"])  # Dispensing CC3-S
    protocol.delay(seconds=10)  # let it swell
    right_pipette.move_to(stock["A2"].top())
    right_pipette.dispense(100, stock["A2"].top(z=2))
    # .top(z=2) allows the pipette to dispense from 2mm above the vial to avoid
    # cross-contamination

    # 225ul from stock A2 (CC3-S) into every vial in plate
    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A1"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A2"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A3"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A4"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A5"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["A6"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B1"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B2"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B3"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B4"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B5"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["B6"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C1"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C2"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C3"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C4"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C5"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["C6"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D1"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D2"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D3"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D4"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D5"].top(z=2))

    right_pipette.aspirate(225, stock["A2"])
    right_pipette.air_gap(15)
    right_pipette.dispense(240, stirrer["D6"].top(z=2))

    right_pipette.drop_tip()

    # resets the serial data to turn the magnets off at the end of protocol
    ser.flushInput()
    datatosend = "0\n"
    bytedata = datatosend.encode("utf-8")
    ser.write(bytedata)

    ser.close()  # closes the serial port

    for line in protocol.commands():
        print(line)

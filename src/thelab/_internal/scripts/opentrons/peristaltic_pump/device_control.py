# This Python script is for controlling a peristaltic pump via UART communication.
# This script receives volume data from a connected device, dispenses samples in calibrated volumes
# and includes steps for sample withdrawal, solvent dispensing, and NMR analysis delay.

from machine import Pin, UART
import time

# Configuration for the stepper motor driver
STEP_PIN = 11                                                                 # Step pin of A4988 driver
DIR_PIN = 10                                                                  # Direction pin of A4988 driver

# Calibration parameters
steps_per_volume = 1000                                                       # Number of steps required to dispense 1 mL

# Setting up the pins as output
step_pin = Pin(STEP_PIN, Pin.OUT)
dir_pin = Pin(DIR_PIN, Pin.OUT)

dir_pin.value(1)                                                              # Direction set to clockwise

# UART configuration for communication
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
uart.init(bits=8, parity=None, stop=1)

# Function to rotate the stepper motor to dispense the specified volume
def dispense_volume(volume):
    if volume == 0:                                                           # Pump is stopped if the volume is 0
        return

    num_steps = int(volume * steps_per_volume)                                # Calculates the number of steps required to dispense the specified volume

    step_interval = 1000                                                      # Dispense the volume at a default speed. Roughly 20 seconds is needed to dispense 1 mL

    # Dispense the volume at the desired speed
    for _ in range(num_steps):
        step_pin.value(1)
        time.sleep_us(step_interval)
        step_pin.value(0)
        time.sleep_us(step_interval)
num_iterations = 24                                                           # number of wells in the plate

while True:
    try:
        if uart.any():
            data = uart.read(5)
            if data is not None:                                              # Checks if data is not None
                data = data.decode('utf-8').strip()                           # Read 4 characters
                print("Received data:", data)                                 # For debugging
                volume = float(data)                                          # Convert the received data to the volume in mL
                print("Received volume:", volume, "mL")

                if volume == 0                                                # Stop the pump if the volume is 0
                    dispense_volume(volume)
                    print("Pump stopped.")
                else:                                                         # Perform the iteration for the non-zero volume
                    for i in range(num_iterations):
                        print("Iteration:", i + 1)
                        dispense_volume(volume)                               # Draws inserted volume
                        print("Received volume:", volume, "mL")
                        time.sleep(2.5)                                       # Time delayed to lift up the Gen-2 pipette
                        print("Dispensing volume: 1 mL")                      # Dispensing the remaining sample in the tube
                        dispense_volume(1)                                    # Roughly 20s to pump out the remaining
                        time.sleep(55)                                        # Allowing NMR to analyse
                        dispense_volume(6)                                    # Wash cycle is taking place
                        print("Dispensing volume of solvent: 6 mL")
                        time.sleep(10)                                        # Delay added to move the Gen-2 pipette to a different slot
                        dispense_volume(2)                                    # Takes 40s to wash out the remaining solvent
                        print("Dispensing remaining volume of solvent: 2 mL")
                        print("Completed iteration:", i + 1)                  # Loops continues until num_iteration reaches 24
                        time.sleep(17)                                        # Awaiting the next well

                    print("All iterations completed.")
                    break

    except ValueError:
        print("Invalid data format. Expected format: volume")

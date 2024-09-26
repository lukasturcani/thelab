# ruff: noqa: T201
# Code uploaded to the Raspberry Pi Pico in the magnetic stirrer module before
# commencing experiment protocol. Allows for serial USB connection between the
# Raspberry Pi Pico and OT-2 liquid handling platform. File must be uploaded to
# the Pi Pico with the name "main.py"

from _thread import start_new_thread
from sys import exit, stdin

import utime
from machine import I2C, PWM, Pin
from ssd1306 import SSD1306_I2C
from utime import sleep

ON = "1"
OFF = "0"
# Delay for switching between the magnetic poles on the electromagnets, greater
# delays = slower stirring speeds
DELAY = 0.03
# Connection for OLED screen
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
oled = SSD1306_I2C(128, 64, i2c)

# Pin connections, PWM treats the magnets akin to a motor
pin1 = PWM(Pin(3))
pin2 = PWM(Pin(4))
pin3 = PWM(Pin(5))
pin4 = PWM(Pin(6))

# Set the frequency and maximum duty of the motor
pin1.freq(1000)
pin2.freq(1000)
pin3.freq(1000)
pin4.freq(1000)

duty = 65535 * 0.75

# The step sequence corresponds to when each magnet is on or off,
# 1 = on, 0.7 = partial on, 0 = off
# Four numbers correspond to 4 magnets and so 8 steps for a full cycle
# (i.e. full rotation of magnetic stirrer bar)
full_step_sequence: list[list[float]] = [
    [1, 0, 0, 0],
    [0.7, 0, 0.7, 0],
    [0, 0, 1, 0],
    [0, 0.7, 0.7, 0],
    [0, 1, 0, 0],
    [0, 0.7, 0, 0.7],
    [0, 0, 0, 1],
    [0.7, 0, 0, 0.7],
]


# Stirring function
def stirring(data_input: str) -> None:
    if data_input == ON:  # If function is turned on, magnets turn on
        for step in full_step_sequence:
            # Multiplies each number in the step sequence to the maximum duty
            pin1.duty_u16(int(step[0] * duty))
            pin2.duty_u16(int(step[1] * duty))
            pin3.duty_u16(int(step[2] * duty))
            pin4.duty_u16(int(step[3] * duty))
            utime.sleep(DELAY)
    elif data_input == OFF:  # If function is turned off, magnets turn off
        pin1.duty_u16(0)
        pin2.duty_u16(0)
        pin3.duty_u16(0)
        pin4.duty_u16(0)


oled.fill(0)
oled.text("Ready", 30, 30)
oled.show()

# Online Reference
#
# USB serial communication for the Raspberry Pi Pico (RP2040) using the
# second RP2040 thread/processor (written by Dorian Wiskow - January 2021)
# https://forums.raspberrypi.com/viewtopic.php?t=302889
#

# Global variables to share between both threads/processors
buffer_size = 1024  # Size of circular buffer to allocate
buffer = [
    " "
] * buffer_size  # Circular incoming USB serial data buffer (pre-fill)
buffer_echo = False  # USB serial port echo incoming characters (True/False)
buffer_next_in, buffer_next_out = (
    0,
    0,
)  # Pointers to next in/out character in circular buffer
terminate_thread = (
    False  # Tell 'buffer_stdin' function to terminate (True/False)
)


# buffer_stdin() function to execute in parallel on second Pico RP2040
# thread/processor
def buffer_stdin() -> None:
    global buffer_next_in  # noqa: PLW0603

    while True:  # Endless loop
        if terminate_thread:  # If requested by main thread ...
            break  # ... exit loop
        buffer[buffer_next_in] = stdin.read(
            1
        )  # Wait for/store next byte from USB serial
        if buffer_echo:  # If echo is True ...
            print(
                buffer[buffer_next_in], end=""
            )  # ... output byte to USB serial
        buffer_next_in += 1  # Bump pointer
        if buffer_next_in == buffer_size:  # ... and wrap, if necessary
            buffer_next_in = 0


# Instantiate second 'background' thread on RP2040 dual processor to monitor
# and buffer incoming data from 'stdin' over USB serial port using
# buffer_stdin function (above)
buffer_stdin_thread = start_new_thread(buffer_stdin, ())


# Function to check if a byte is available in the buffer and if so, return it
def get_byte_buffer() -> str:
    global buffer_next_out  # noqa: PLW0603

    if buffer_next_out == buffer_next_in:  # If no unclaimed byte in buffer ...
        return ""  # ... return a null string
    n = buffer_next_out  # Save current pointer
    buffer_next_out += 1  # Bump pointer
    if buffer_next_out == buffer_size:  # ... wrap, if necessary
        buffer_next_out = 0
    return buffer[n]  # Return byte from buffer


# Function to check if a line is available in the buffer and if so, return it
# Otherwise, return a null string
def get_line_buffer() -> str:  # noqa: C901
    global buffer_next_out  # noqa: PLW0603

    if buffer_next_out == buffer_next_in:  # If no unclaimed byte in buffer ...
        return ""  # ... RETURN a null string

    n = buffer_next_out  # Search for a LF in unclaimed bytes
    while n != buffer_next_in:
        if buffer[n] == "\x0a":  # If a LF found ...
            break  # ... exit loop ('n' pointing to LF)
        n += 1  # Bump pointer
        if n == buffer_size:  # ... wrap, if necessary
            n = 0
    if n == buffer_next_in:  # If no LF found ...
        return ""  # ... RETURN a null string

    line = ""  # LF found in unclaimed bytes at pointer 'n'
    n += 1  # Bump pointer past LF
    if n == buffer_size:  # ... wrap, if necessary
        n = 0

    while (
        buffer_next_out != n
    ):  # Build line to RETURN until LF pointer 'n' hit
        if buffer[buffer_next_out] == "\x0d":  # If byte is CR
            buffer_next_out += 1  # Bump pointer
            if buffer_next_out == buffer_size:  # ... wrap, if necessary
                buffer_next_out = 0
            continue  # Ignore (strip) any CR (\x0d) bytes

        if buffer[buffer_next_out] == "\x0a":  # If current byte is LF ...
            buffer_next_out += 1  # Bump pointer
            if buffer_next_out == buffer_size:  # ... wrap, if necessary
                buffer_next_out = 0
            break  # Exit loop, ignoring (i.e. strip) LF byte
        line = line + buffer[buffer_next_out]  # Add byte to line
        buffer_next_out += 1  # Bump pointer
        if buffer_next_out == buffer_size:  # Wrap, if necessary
            buffer_next_out = 0
    return line  # RETURN unclaimed line of input


# Main program begins here ...
try:
    input_option = "LINE"  # Get input from buffer one BYTE or LINE at a time
    while True:
        if input_option == "BYTE":  # NON-BLOCKING input one byte at a time
            buff_ch = get_byte_buffer()  # Get a byte if it is available
            if buff_ch:
                print(
                    "received data = " + buff_ch
                )  # Print it out to the USB serial port
                if buff_ch == ON:
                    # Print it out to the USB serial port
                    print("one")
                    buff_ch = get_byte_buffer()
                    if buff_ch == OFF:
                        break
                elif buff_ch == OFF:
                    # Print it out to the USB serial port
                    print("zero")

        elif (
            input_option == "LINE"
        ):  # NON-BLOCKING input one line at a time (ending LF)
            buff_line = get_line_buffer()  # Get a line if it is available?
            if buff_line:  # If there is...
                print(buff_line)
                oled.fill(0)
                oled.text(buff_line, 0, 0)
                oled.show()
                if buff_line == ON:  # If the stirrer is on...
                    oled.text("Stirring in", 10, 20)
                    oled.text("Progress", 10, 30)
                    oled.show()
                    while True:
                        stirring(ON)  # Stirring function turns on
                        buff_line = get_line_buffer()
                        if buff_line == OFF:
                            # Repeatedly checks for a 0 value to break out of
                            # the loop and turn off the stirrer
                            stirring(OFF)
                            oled.fill(0)
                            oled.text("Off", 30, 30)
                            break
                elif buff_line == OFF:
                    stirring(OFF)
                    oled.fill(0)
                    oled.text("Off", 30, 30)
                else:
                    # Outputs an error message if a value other than 0 or 1 is
                    # received by the Pi Pico
                    oled.fill(0)
                    oled.text("Error", 30, 30)
                oled.show()

        sleep(0.1)

except KeyboardInterrupt:  # Trap Ctrl-C input
    terminate_thread = True  # Signal second 'background' thread to terminate
    exit()

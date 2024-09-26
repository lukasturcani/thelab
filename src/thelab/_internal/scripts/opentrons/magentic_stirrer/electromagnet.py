# Code developed when testing the control of the electromagnets to test
# stirring control of the module from its Raspberry Pi Pico

import utime from machine import I2C, PWM, Pin
from ssd1306 import SSD1306_I2C

ON = "1"
OFF = "0"
# Sets the initial timer
stop_time = 0
# Delay for switching between the magnetic poles on the electromagnets,
# greater delays = slower stirring speeds
DELAY = 0.03
# Time wanted to stir for in milliseconds
TIME_MS = 60000  # Time wanted to stir for
start = True
done_once = True
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

while True:
    if start:
        now_t = utime.ticks_ms()
        if done_once:
            stop_time = now_t + TIME_MS  # Sets the timer
            done_once = False
        for step in full_step_sequence:
            # Multiplies each number in the step sequence to the maximum duty
            pin1.duty_u16(int(step[0] * duty))
            pin2.duty_u16(int(step[1] * duty))
            pin3.duty_u16(int(step[2] * duty))
            pin4.duty_u16(int(step[3] * duty))
            utime.sleep(DELAY)
        if now_t >= stop_time:  # When timer reaches zero, all magnets turn off
            pin1.duty_u16(0)
            pin2.duty_u16(0)
            pin3.duty_u16(0)
            pin4.duty_u16(0)
            start = False
        sec_remaining = str((stop_time - now_t) / 1000)
        oled.fill(0)
        oled.text("Stirring in", 10, 10)
        oled.text("Progress", 10, 20)
        oled.text("Time Remaining", 10, 40)
        # Displays in real-time the time remaining for stirring on the OLED
        # screen
        oled.text(sec_remaining, 10, 50)
        oled.show()
    else:
        oled.fill(0)
        oled.text(
            "Complete", 0, 0
        )  # Screen displays message when timer reaches zero
        oled.show()

# Should there be any issue with the experiment protocol.py file, this code can
# be connected directly to the magnetic stirrer to run it without USB
# connection to the OT-2

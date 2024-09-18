import machine
import utime
from machine import I2C, Pin, PWM
from ssd1306 import SSD1306_I2C
from sys import stdin, exit
from _thread import start_new_thread

# Constants
ON = "1"
OFF = "0"
DELAY = 0.03  # Delay between magnetic pole switches; controls stirring speed
DUTY_CYCLE = 65535 * 0.75  # 75% duty cycle
BUFFER_SIZE = 1024  # Circular buffer size

# I2C OLED setup
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
oled = SSD1306_I2C(128, 64, i2c)

# PWM pin setup for electromagnets
pwm_pins = [PWM(Pin(pin)) for pin in range(3, 7)]
for pin in pwm_pins:
    pin.freq(1000)

# Full step sequence for stirring control
FULL_STEP_SEQUENCE = [
    [1, 0, 0, 0],
    [0.7, 0, 0.7, 0],
    [0, 0, 1, 0],
    [0, 0.7, 0.7, 0],
    [0, 1, 0, 0],
    [0, 0.7, 0, 0.7],
    [0, 0, 0, 1],
    [0.7, 0, 0, 0.7],
]

# Circular buffer variables
buffer = [" "] * BUFFER_SIZE
buffer_echo = False
buffer_next_in = 0
buffer_next_out = 0
terminate_thread = False


def init_oled_message(message="Ready"):
    """Initialize OLED screen with a message."""
    oled.fill(0)
    oled.text(message, 30, 30)
    oled.show()


def stirring(data_input):
    """Control the stirring mechanism based on input."""
    if data_input == ON:
        for step in FULL_STEP_SEQUENCE:
            for i, pin in enumerate(pwm_pins):
                pin.duty_u16(int(step[i] * DUTY_CYCLE))
            utime.sleep(DELAY)
    elif data_input == OFF:
        for pin in pwm_pins:
            pin.duty_u16(0)


def buffer_stdin():
    """Background function to read from stdin into a buffer."""
    global buffer_next_in, terminate_thread

    while not terminate_thread:
        buffer[buffer_next_in] = stdin.read(1)
        if buffer_echo:
            print(buffer[buffer_next_in], end="")
        buffer_next_in = (buffer_next_in + 1) % BUFFER_SIZE


def get_byte_buffer():
    """Return a byte from the buffer if available."""
    global buffer_next_out
    if buffer_next_out == buffer_next_in:
        return ""
    byte = buffer[buffer_next_out]
    buffer_next_out = (buffer_next_out + 1) % BUFFER_SIZE
    return byte


def get_line_buffer():
    """Return a line from the buffer if available."""
    global buffer_next_out
    n = buffer_next_out
    while n != buffer_next_in:
        if buffer[n] == "\x0a":
            break
        n = (n + 1) % BUFFER_SIZE

    if n == buffer_next_in:
        return ""

    line = ""
    n = (n + 1) % BUFFER_SIZE
    while buffer_next_out != n:
        if buffer[buffer_next_out] == "\x0d":
            buffer_next_out = (buffer_next_out + 1) % BUFFER_SIZE
            continue
        if buffer[buffer_next_out] == "\x0a":
            buffer_next_out = (buffer_next_out + 1) % BUFFER_SIZE
            break
        line += buffer[buffer_next_out]
        buffer_next_out = (buffer_next_out + 1) % BUFFER_SIZE
    return line


def process_input(input_option="LINE"):
    """Main loop to process input in either BYTE or LINE mode."""
    try:
        while True:
            if input_option == "BYTE":
                buff_ch = get_byte_buffer()
                if buff_ch:
                    handle_input(buff_ch)

            elif input_option == "LINE":
                buff_line = get_line_buffer()
                if buff_line:
                    handle_input(buff_line)

            utime.sleep(0.1)

    except KeyboardInterrupt:
        global terminate_thread
        terminate_thread = True
        exit()


def handle_input(input_data):
    """Handle the input and control stirring and OLED display."""
    print(input_data)
    oled.fill(0)
    oled.text(input_data, 0, 0)

    if input_data == ON:
        oled.text("Stirring in Progress", 10, 20)
        oled.show()
        stirring_loop()
    elif input_data == OFF:
        stirring(OFF)
        oled.text("Off", 30, 30)
    else:
        oled.text("Error", 30, 30)

    oled.show()


def stirring_loop():
    """Loop that controls stirring and checks for OFF signal."""
    while True:
        stirring(ON)
        if get_line_buffer() == OFF:
            stirring(OFF)
            break


if __name__ == "__main__":
    init_oled_message()
    start_new_thread(buffer_stdin, ())
    process_input()


# ruff: noqa: T201
from _thread import start_new_thread
from dataclasses import dataclass
from sys import exit, stdin

from machine import I2C, PWM, Pin
from ssd1306 import SSD1306_I2C
from utime import sleep

ON = "1"
OFF = "0"
DELAY = 0.03
DUTY = int(65535 * 0.75)

# OLED setup
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
oled = SSD1306_I2C(128, 64, i2c)

# Pin setup for PWM, treating the magnets as motors
pins = [PWM(Pin(i)) for i in range(3, 7)]
for pin in pins:
    pin.freq(1000)

# Step sequence for controlling the magnets
FULL_STEP_SEQUENCE: list[list[float]] = [
    [1, 0, 0, 0],
    [0.7, 0, 0.7, 0],
    [0, 0, 1, 0],
    [0, 0.7, 0.7, 0],
    [0, 1, 0, 0],
    [0, 0.7, 0, 0.7],
    [0, 0, 0, 1],
    [0.7, 0, 0, 0.7],
]

BUFFER_SIZE = 1024


@dataclass
class BufferState:
    buffer: list[str]
    next_in: int
    next_out: int
    echo: bool = False
    terminate_thread: bool = False

    def buffer_stdin(self) -> None:
        """Reads incoming USB serial data and stores it in a circular buffer.

        Runs in a separate thread to enable non-blocking input handling.
        """
        while not self.terminate_thread:
            self.buffer[self.next_in] = stdin.read(1)
            if self.echo:
                print(self.buffer[self.next_in], end="")
            self.next_in = (self.next_in + 1) % BUFFER_SIZE

    def get_byte(self) -> str:
        """Retrieve a byte from the circular buffer, if available.

        Returns:
            The next byte from the buffer, or an empty string if no data
            is available.
        """
        if self.next_out == self.next_in:
            return ""
        byte = self.buffer[self.next_out]
        self.next_out = (self.next_out + 1) % BUFFER_SIZE
        return byte

    def get_line(self) -> str:
        """Retrieve a line of text from the circular buffer, if available.

        A line is considered complete when a newline (LF) character is
        encountered.

        Returns:
            A line of text from the buffer, or an empty string if no complete
            line is available.
        """
        if self.next_out == self.next_in:
            return ""

        n = self.next_out
        while n != self.next_in:
            if self.buffer[n] == "\x0a":  # Look for LF
                break
            n = (n + 1) % BUFFER_SIZE

        if n == self.next_in:
            return ""

        line = ""
        while self.next_out != (n + 1) % BUFFER_SIZE:
            if self.buffer[self.next_out] == "\x0d":  # Ignore CR
                self.next_out = (self.next_out + 1) % BUFFER_SIZE
                continue
            line += self.buffer[self.next_out]
            self.next_out = (self.next_out + 1) % BUFFER_SIZE
        return line


def stirring(data_input: str) -> None:
    """Controle magnetic stirrer based on the input state.

    Args:
        data_input: '1' to turn the stirrer on, '0' to turn it off.
    """
    if data_input == ON:
        for step in FULL_STEP_SEQUENCE:
            for i, pin in enumerate(pins):
                pin.duty_u16(int(step[i] * DUTY))
            sleep(DELAY)
    elif data_input == OFF:
        for pin in pins:
            pin.duty_u16(0)


def display_message(message: str) -> None:
    """Display a message on the OLED screen.

    Args:
        message: The message to be displayed.
    """
    oled.fill(0)
    oled.text(message, 0, 0)
    oled.show()


def handle_stirring_commands(state: BufferState) -> None:
    """Handle the received commands for controlling the magnetic stirrer.

    Args:
        state: BufferState object containing buffer and pointers.
    """
    buff_line = state.get_line()

    if buff_line == ON:
        display_message("Stirring in\nProgress")
        while True:
            stirring(ON)
            buff_line = state.get_line()
            if buff_line == OFF:
                stirring(OFF)
                display_message("Off")
                break
    elif buff_line == OFF:
        stirring(OFF)
        display_message("Off")
    else:
        display_message("Error")


def main() -> None:
    state = BufferState(buffer=[" "] * BUFFER_SIZE, next_in=0, next_out=0)

    display_message("Ready")

    # Start the background thread for buffer management
    start_new_thread(state.buffer_stdin, ())

    input_option = "LINE"
    try:
        while True:
            if input_option == "BYTE":
                buff_ch = state.get_byte()
                if buff_ch:
                    print(f"Received data = {buff_ch}")
                    if buff_ch == ON:
                        stirring(ON)
                    elif buff_ch == OFF:
                        stirring(OFF)

            elif input_option == "LINE":
                handle_stirring_commands(state)

            sleep(0.1)

    except KeyboardInterrupt:
        state.terminate_thread = True
        exit()


if __name__ == "__main__":
    main()

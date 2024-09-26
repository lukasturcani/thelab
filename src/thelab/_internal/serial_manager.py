import time
import warnings
from threading import Lock

import serial
import serial.tools.list_ports


class SerialManager:
    def __init__(
        self,
        *,
        port: str | None = None,
        baudrate: int = 9600,
        timeout: int = 5,
        connect: bool = True,
    ) -> None:
        self._ser: None | serial.Serial = None
        if connect:
            self.connect(port, baudrate, timeout)

        self.lock = Lock()
        self._port = port

    @property
    def is_connected(self) -> bool:
        if self._ser is None:
            return False
        return self._ser.is_open

    @property
    def port(self) -> str | None:
        return self._port

    @staticmethod
    def _find_last_port() -> str:
        return serial.tools.list_ports.comports()[-1].device

    def connect(
        self,
        port: str | None = None,
        baudrate: int = 9600,
        timeout: int = 5,
    ) -> None:
        if self.is_connected:
            warnings.warn("Serial already connected")
            return
        try:
            if port is not None:
                self._port = port
            else:
                self._port = self._find_last_port()

            self._ser = serial.Serial(
                port=self.port, baudrate=baudrate, timeout=timeout
            )
            if not self._ser.is_open:
                self._ser.open()
            time.sleep(0.1)
            self._ser.reset_input_buffer()
        except serial.SerialException as e:
            msg = f"Failed opening serial port: {e}"
            raise RuntimeError(msg) from e

    def reset_buffer(self) -> None:
        if self.is_connected and self._ser is not None:
            self._ser.reset_input_buffer()

    def disconnect(self) -> None:
        if self.is_connected and self._ser is not None:
            self._ser.close()
        else:
            warnings.warn("Serial is not connected")

    def send_num_cmd(self, cmd: str, parameter: int = 0) -> str:
        assert (
            isinstance(cmd, str) and len(cmd) == 1
        ), "The command must be a single character"
        assert isinstance(parameter, int)
        send_str = f"/{cmd.upper()}{parameter!s}\r\n"
        with self.lock:
            self._ser.write(send_str.encode("utf-8"))
        time.sleep(0.1)
        return send_str

    def send_str_cmd(self, cmd: str, info: str = "") -> str:
        assert (
            isinstance(cmd, str) and len(cmd) == 1
        ), "The command must be a single character"
        assert isinstance(info, str)
        send_str = f"/{cmd.upper()}:{info}\r\n"
        with self.lock:
            self._ser.write(send_str.encode("utf-8"))
        time.sleep(0.1)
        return send_str

    def query_cmd(self, cmd: str) -> str:
        assert (
            isinstance(cmd, str) and len(cmd) == 1
        ), "The command must be a single character"
        send_str = f"/{cmd.upper()}?\r\n"
        with self.lock:
            self._ser.write(send_str.encode("utf-8"))
        time.sleep(0.1)
        return send_str

    @staticmethod
    def parse_response(response: str) -> (str, int | str | None, bool):
        # return a. the command, b. the content, c. whether it is a query
        if response[0] != "/":
            return "E", 0, False
        stripped_response = response.lstrip("/").rstrip("\r\n")
        if len(stripped_response) == 1:
            stripped_response += "?"
        cmd = stripped_response[0]
        key = stripped_response[1]
        if key == "?":  # this is a query
            return cmd, None, True

        if key == ":":  # this is a string info
            info: str = stripped_response[2:]
            return cmd, info, False

        info: str = stripped_response[1:]
        if not info.isdecimal():
            return "E", 0, False
        return cmd, int(info), False

    def read_response(self) -> (str, int | str | None, bool):
        try:
            with self.lock:
                raw_response = self._ser.readline().decode("utf-8")
                # print(raw_response)
                self.reset_buffer()
        except serial.Timeout:
            raise RuntimeError("No response received.")

        return self.parse_response(raw_response)

    def available(self) -> bool:  # check if response is available to receive
        return bool(self._ser.in_waiting)

    @staticmethod
    def check_error(cmd, info: int):
        if cmd == "E":
            if info == 1:
                raise RuntimeError("Cannot execute command")
            if info == 0:
                raise ValueError("Invalid command")

    def check_is_busy(self) -> bool:
        cmd, info, _ = self._send_and_read_no_busy_check("S", True)
        self.check_error(cmd, info)
        return info == 1

    def wait_busy(self, time_out: int = 5):
        timer_start = time.time()
        while self.check_is_busy() and time.time() - timer_start <= time_out:
            time.sleep(0.2)
        if time.time() - timer_start > time_out:
            raise TimeoutError("Busy time out")

    def _send_and_read_no_busy_check(
        self,
        cmd: str,
        is_query: bool,
        info: str | int = "",
        time_out: int = 1,
    ) -> tuple:
        assert len(cmd) == 1, f"Invalid command {cmd}"

        if is_query:
            self.query_cmd(cmd)
        elif isinstance(info, str):
            self.send_str_cmd(cmd, info)
        elif isinstance(info, int):
            self.send_num_cmd(cmd, info)
        else:
            raise ValueError(f"{info} wrong type: str or int")

        timer_start = time.time()
        time.sleep(0.1)
        while not self.available() and time.time() - timer_start <= time_out:
            time.sleep(0.1)
        if not self.available():
            raise TimeoutError("No response")
        return self.read_response()

    def send_and_read(
        self,
        cmd: str,
        is_query: bool,
        info: str | int = "",
        time_out: int = 5,
    ):
        assert len(cmd) == 1, f"Invalid command {cmd}"
        self.wait_busy(time_out=time_out)
        return self._send_and_read_no_busy_check(
            cmd=cmd.upper(), is_query=is_query, info=info
        )

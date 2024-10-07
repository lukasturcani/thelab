import json

from thelab._internal.serial_manager import SerialManager


class OpenTurbidityClient:
    def __init__(self, port: str | None = None):
        self.hand_shaken: bool = False
        self._serial_manager = SerialManager(port=port)

    def check_busy(self) -> bool:
        return self._serial_manager.check_is_busy()

    def wait_busy(self, time_out: int = 5) -> None:
        return self._serial_manager.wait_busy(time_out=time_out)

    def hello(self) -> bool:
        cmd, _, _ = self._serial_manager.send_and_read("H", False, 0)
        if cmd == "H":
            self.hand_shaken = True
            return True
        return False

    def bye(self) -> bool:
        cmd, info, is_query = self._serial_manager.send_and_read("B", False, 0)
        self.hand_shaken = False
        return cmd == "B"

    def get_run_number(self) -> int:
        assert self.hand_shaken, "Must say hello first"
        cmd, info, is_query = self._serial_manager.send_and_read("X", True)
        self._serial_manager.check_error(cmd, info)
        return info

    def get_solution_status(self) -> int:
        assert self.hand_shaken, "Must say hello first"
        cmd, info, is_query = self._serial_manager.send_and_read("Q", True)
        self._serial_manager.check_error(cmd, info)
        return info

    def get_is_monitoring(self) -> bool:
        cmd, info, is_query = self._serial_manager.send_and_read("M", True)
        self._serial_manager.check_error(cmd, info)
        return info == 1

    def start_monitoring(self) -> bool:
        assert self.hand_shaken, "Must say hello first"
        cmd, info, is_query = self._serial_manager.send_and_read("M", False, 1)
        self._serial_manager.check_error(cmd, info)
        self.wait_busy(time_out=30)
        return self.get_is_monitoring()

    def stop_monitoring(self) -> bool:
        assert self.hand_shaken, "Must say hello first"
        cmd, info, is_query = self._serial_manager.send_and_read("M", False, 0)
        self._serial_manager.check_error(cmd, info)
        self.wait_busy(time_out=300)
        return not self.get_is_monitoring()

    def get_study_name(self) -> str:
        cmd, info, is_query = self._serial_manager.send_and_read("N", True, 0)
        self._serial_manager.check_error(cmd, info)
        return info

    def set_study_name(self, name: str) -> str:
        cmd, info, is_query = self._serial_manager.send_and_read(
            "N", False, name
        )
        self._serial_manager.check_error(cmd, info)
        return self.get_study_name()

    def get_folder_name(self) -> str:
        cmd, info, is_query = self._serial_manager.send_and_read("F", True, 0)
        self._serial_manager.check_error(cmd, info)
        return info

    def set_folder_name(self, folder: str) -> str:
        cmd, info, is_query = self._serial_manager.send_and_read(
            "F", False, folder
        )
        self._serial_manager.check_error(cmd, info)
        return self.get_folder_name()

    def get_data(self) -> tuple[float, float, float]:  # time, ref, spl
        assert self.hand_shaken, "Must say hello first"
        cmd, info, is_query = self._serial_manager.send_and_read("D", True)
        info: str | int
        self._serial_manager.check_error(cmd, info)
        split_str = info.split(",")
        return_tuple = (
            float(split_str[0]),
            float(split_str[1]),
            float(split_str[2]),
        )
        return return_tuple

    def get_parameters(self) -> dict:
        cmd, info, is_query = self._serial_manager.send_and_read("P", True)
        self._serial_manager.check_error(cmd, info)
        params_dict = json.loads(info)
        return params_dict

    def set_parameters(self, params: dict) -> dict:
        params_str: str = json.dumps(params)
        cmd, info, is_query = self._serial_manager.send_and_read(
            "P", False, params_str
        )
        self._serial_manager.check_error(cmd, info)
        return self.get_parameters()

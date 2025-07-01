import time


class Rate:
    def __init__(self, hz: float):
        self.__hz = hz
        self.__time = self.now()

    def now(self):
        return time.monotonic()

    def sleep(self):
        sleep_duration = max(
            0,
            (1 / self.__hz) - (self.now() - self.__time)
        )
        time.sleep(sleep_duration)
        self.__time = self.now()

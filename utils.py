from pathlib import Path
import json
import os
import time
import pandas as pd

# Fuente: https://realpython.com/python-timer/
class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


# Fuente: https://realpython.com/python-timer/
class Timer:
    def __init__(self):
        self._start_time = None

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")

# Aquí poner parser, creador de graficas, etc

if __name__ == "__main__":
    # aquí espacio para testear
    pass

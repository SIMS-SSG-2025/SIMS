"""
Entry point for the device runtime. Initializes the database worker thread and
DeviceRuntime instance, then enters the main loop that checks system status and
controls AI processing. Handles graceful shutdown and thread cleanup.
"""

import time
import threading, queue
from .utils.logger import get_logger
from .utils.db_worker import db_worker

from device.DeviceRuntime import DeviceRuntime

if __name__ == "__main__":
    # Initialize logger for main module
    logger = get_logger("Main")

    # -- Setup DB Thread --
    db_queue = queue.Queue(maxsize=100)
    response_queue = queue.Queue()
    stop_event = threading.Event()

    db_thread = threading.Thread(target=db_worker, args=(db_queue, stop_event))
    db_thread.start()

    device_runtime = DeviceRuntime(db_queue)
    while True:
        try:
            # Check system status
            db_queue.put({"action": "get_status", "response": response_queue})
            try:
                run_flag = response_queue.get(timeout=0.2)
            except queue.Empty:
                logger.warning("No response from database worker for status check")
                run_flag = False
                time.sleep(1)
                continue

            if run_flag:
                device_runtime.start()
            else:
                time.sleep(0.5)

        except KeyboardInterrupt:
            stop_event.set()
            device_runtime.stop()
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(1)

    device_runtime.stop()
    stop_event.set()
    db_thread.join()

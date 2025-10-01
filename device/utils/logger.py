import logging
from pathlib import Path

def get_logger(name, log_file="device.log", level=logging.INFO):
    log_path = Path(__file__).resolve().parent.parent / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / log_file

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

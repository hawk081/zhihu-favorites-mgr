# -*- coding: utf-8 -*-

# Build-in / Std
import os
import sys
import logging


def init_logger():
    logging.getLogger("requests").setLevel(logging.WARNING)
    logger = logging.getLogger("UserLog")
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
    # file_handler = logging.FileHandler(os.path.join(os.getcwd(), "work.log" ))
    # file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    # logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

    logger.info("=" * 80)

    return logger

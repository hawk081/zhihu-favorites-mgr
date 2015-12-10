# -*- coding: utf-8 -*-

# Build-in / Std
import os
import sys
import logging

loggers = {}

def init_logger():
    global loggers

    logging.getLogger("requests").setLevel(logging.WARNING)
    if not loggers.get("UserLog"):
        logger = logging.getLogger("UserLog")
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
        # file_handler = logging.FileHandler(os.path.join(os.getcwd(), "work.log" ))
        # file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler(sys.stdout)
        # logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.DEBUG)

        loggers.update(dict(UserLog=logger))

        logger.info("=" * 80)

        return logger
    else:
        return loggers.get("UserLog")

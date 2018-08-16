from garage_web_api import GarageWebApi
import time
import core.tkutil as tkutil
import config


def log_garage(log_content, push_to_server=False):
    tkutil.log(log_content)
    if push_to_server and config.PUSH_LOG_TO_SERVER:
        GarageWebApi.log_to_server(log_content)
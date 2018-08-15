from garage_web_api import GarageWebApi
import time
import core.tkutil as tkutil


def log_garage(log_content, push_to_server=False):
    tkutil.log(log_content)
    if push_to_server:
        GarageWebApi.log_to_server(log_content)
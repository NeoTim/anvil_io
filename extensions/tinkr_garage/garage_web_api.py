# coding:utf-8
import requests
import json
import time
import config


class GarageWebApi:

    @classmethod
    def check_session(cls, cid, token):
        if config.CHECK_SESSION is False:
            # Pretending all is well
            return True
        # check whether the client was logged in
        api_url = config.WEB_SERVER_API
        try:
            response = requests.get(
                api_url + 'checksession?pid=' + str(cid) + '&sessionid=' + str(token),
                timeout=2
            )
            if response and response.text:
                res = json.loads(response.text)
                if res['result'] == 'succeed':
                    return True
            return False
        except requests.exceptions.Timeout, e:
            print 'web server timed out.'
        return False

    @classmethod
    def push_log(cls, server_name, log_content, timestamp):
        api_url = config.WEB_SERVER_API
        try:
            res = requests.post(
                url = api_url + 'updatelog',
                data=json.dumps({
                    'serverName': server_name,
                    'content': log_content,
                    'timestamp': timestamp
                }, encoding='utf-8'),
                timeout=2
            )
        except Exception, e:
            print e

    @classmethod
    def log_to_server(cls, log_content):
        cls.push_log(
            config.SERVER_NAME_IN_LOG,
            log_content,
            int(time.time())
        )


if __name__ == '__main__':

    import time
    print str(('45', 343))

    web_api = GarageWebApi()
    # web_api.SERVER_IP = 'http://192.168.145.41:4000/api/'
    # web_api.push_log('serverlog', 'test_log2', int(time.time()))
import requests
import time

start_time = time.time()
t = requests.get('https://www.youtube.com/')
print time.time() - start_time
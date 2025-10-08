# This file communicates to RPI. Hardcoded ip, must be changed.
import requests

url = "http://192.168.43.169:8080/"

def update_data(signal: str):
    return requests.post(url=url, data=signal).text
    


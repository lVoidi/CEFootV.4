import requests
import serial
import time

url = "http://192.168.43.169:8080/"

def update_data(signal):
    r = requests.post(url=url, data=signal.encode("utf-8"))
    return r.text.split(":")


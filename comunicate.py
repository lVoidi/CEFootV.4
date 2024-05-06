import requests
import serial
import time

url = "http://192.168.100.38:8080/"

def update_data():
    r = requests.request(url=url, method="GET")
    return r.content.split(":")


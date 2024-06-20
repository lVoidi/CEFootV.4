import requests
url = "http://192.168.100.216:8080/"

def update_data(signal: str):
    return requests.post(url=url, data=signal).text
    


from machine import Pin, ADC
import network
import random
import socket
import time

# Boton del team y leds
change_player_signal = Pin(28, Pin.IN, Pin.PULL_UP)
current_team_playing = "blue"

blue_team = Pin(0, Pin.OUT)

red_team = Pin(1, Pin.OUT)

blue_team.value(1)

bits = [
    Pin(2, Pin.OUT),
    Pin(3, Pin.OUT),
    Pin(4, Pin.OUT),
]
states = [
    (0,0,0),
    (0,0,1),
    (0,1,0),
    (0,1,1),
    (1,0,0),
    (1,0,1),
    (1,1,0),
    (1,1,1)
]

blue_score = []
red_score = []

def main():
    global blue_team, code, red_team, current_team_playing
    current_team_playing = "blue"
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(100)
    print(f"[DEBUG] Escuchando al puerto 8080, en {addr}")
    while True:
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            print(line)
            if not line or line == b'\r\n':
                break
        print(f"[DEBUG] Cliente conectado desde: {addr} ")
        request = cl.recv(1024).decode()
        signal = request.upper()
        
        print(signal)

        if signal == "SIGTEAM":
            if current_team_playing == "blue":
                send_code("1", cl)
                current_team_playing = "red"
                blue_team.value(0)
                red_team.value(1)
            elif current_team_playing == "red":
                send_code("0", cl)
                current_team_playing = "blue"
                blue_team.value(1)
                red_team.value(0)
        elif "SIGVAR" in signal:
            pin = Pin(5, Pin.OUT)
            pin.value(1)
            time.sleep(2.5)
            pin.value(0)
            _, score = signal.split()
            score = int(score) 
            state1, state2, state3 = states[score]
            bits[0].value(state1)
            bits[1].value(state2)
            bits[2].value(state3)
            if score - 3 < 0:
                score = 7 + (score-2)
            else:
                score -= 3
            send_code(f"{score}", cl)
        elif "SIGSCORE" in signal:
            _, score = signal.split()
            table = [
                "011",
                "100",
                "101",
                "110",
                "111",
                "000",
                "001",
                "010"
            ]
            binary_code = table[int(score)]
            state1, state2, state3 = int(binary_code[0]), int(binary_code[1]), int(binary_code[2])
            bits[0].value(state1)
            bits[1].value(state2)
            bits[2].value(state3)
            send_code("DONE", cl)
        elif signal == "TEST":
            for bit in bits:
                bit.value(0)
            for state in states:
                p1, p2, p3 = state 
                bits[0].value(p1)
                bits[1].value(p2)
                bits[2].value(p3)
                time.sleep(2)
            for bit in bits:
                bit.value(0)
            send_code("DONE", cl)


def send_code(code, client):
    print(f'enviando {code}')
    client.send('HTTP/1.0 200 OK\r\n\r\n')
    print('enviando dato')
    client.send(code.encode())
    print('cerrando')
    client.close()

def do_connect():
    debug_pin = Pin(16, Pin.OUT)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect("gary", "Brinco2020")
        while not sta_if.isconnected():
            pass
    debug_pin.value(1)
    print('network config:', sta_if.ifconfig())



if __name__ == "__main__":  
    do_connect()
    main()
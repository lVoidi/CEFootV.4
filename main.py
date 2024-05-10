from machine import Pin, ADC
import network
import json
import random
import socket
import time

# Boton del team y leds
change_player_signal = Pin(28, Pin.IN, Pin.PULL_UP)
current_team_playing = "blue"

blue_team = Pin(0, Pin.OUT)

red_team = Pin(1, Pin.OUT)

blue_team.value(1)
# Empieza con el azul como team inicial
#blue_team["pin"].value(1)
#red_team["pin"].value(0)


# Botones de cada paleta 
goal_buttons = [
    Pin(7, Pin.IN),
    Pin(8, Pin.IN),
    Pin(9, Pin.IN),
    Pin(10, Pin.IN),
    Pin(11, Pin.IN),
    Pin(12, Pin.IN),
]

goal_leds = [
    Pin(18, Pin.OUT),
    Pin(17, Pin.OUT),
    Pin(16, Pin.OUT),
    Pin(3, Pin.OUT),
    Pin(4, Pin.OUT),
    Pin(5, Pin.OUT),
]


pot = ADC(26)

def return_pot_val():
    return int((pot.read_u16()/65535)*100)//50

def listen_to_goal(goalkeeper_indices, cl, addr):
    global blue_team,red_team
    pressed_button_index = 0
    values = [
        button.value() for button in goal_buttons
    ]
    print(goalkeeper_indices)
    while not any(values):
        values = [
            button.value() for button in goal_buttons
        ]

    is_goal = True
    pressed = False
    for index, value in enumerate(values):
        if value:
            pressed_button_index = index
            pressed = True
        if value and index in goalkeeper_indices:
            is_goal = False
            break

    prefix = ""
    if pressed and is_goal:
        prefix = "1"
    elif pressed and not is_goal:
        prefix = "0"

    code = prefix
    if pressed:
        goal_leds[pressed_button_index].value(1)
        send_code(code, cl)
        time.sleep(1.5)
        goal_leds[pressed_button_index].value(0)

    if not is_goal:
        for _ in range(10):  
            for led in goal_leds:
                led.value(1)
            time.sleep(0.1)
            for led in goal_leds:
                led.value(0) 
            time.sleep(0.1)
    else:
        leds = goal_leds
        for _ in range(10):
            for led in leds:
                led.value(1)
                time.sleep(0.05)
            leds.reverse()
            for led in leds:
                led.value(0) 
                time.sleep(0.05)

def main():
    global blue_team, code, red_team, current_team_playing
    current_team_playing = "blue"
    # Leds de cada paleta
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(100)
    print(f"[DEBUG] Escuchando al puerto 8080, en {addr}")
    goal = [i for i in range(6)]
    while True:
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            print(line)
            if not line or line == b'\r\n':
                break
        print(f"[DEBUG] Cliente conectado desde: {addr} ")
        request = cl.recv(1024).decode().upper()
        signal = request.upper()
        
        print(signal)
        if signal == "SIGTEAM":
            while True:
                if change_player_signal.value() and current_team_playing == "blue":
                    send_code("1", cl)
                    current_team_playing = "red"
                    blue_team.value(0)
                    red_team.value(1)
                    break
                elif change_player_signal.value() and current_team_playing == "red":
                    send_code("0", cl)
                    current_team_playing = "blue"
                    blue_team.value(1)
                    red_team.value(0)
                    break
        elif signal  == "SIGPOT":
            send_code(f"{return_pot_val()}", cl)
        elif signal == "SIGGOAL":
            anotation_algorithm = random.randint(1, 3)

            # Índices de las paletas en las que está el portero
            index_list = []
            if anotation_algorithm == 1:
                goalkeeper_index = random.choice(goal)
                index_list = [goalkeeper_index, goalkeeper_index + 1] if goalkeeper_index + 1 < len(goal) else [goalkeeper_index - 1, goalkeeper_index]
            elif anotation_algorithm == 2:
                goalkeeper_index = random.choice(goal)
                index_list = []
                if goalkeeper_index == len(goal) - 1:
                    index_list = [goalkeeper_index-2, goalkeeper_index-1, goalkeeper_index]
                elif goalkeeper_index == 0:
                    index_list = [goalkeeper_index, goalkeeper_index + 1, goalkeeper_index + 2]
                else:
                    index_list = [goalkeeper_index-1, goalkeeper_index, goalkeeper_index + 1]
            else:
                group = random.randint(0, 1)
                index_list = []
                if group == 1:
                    index_list = list(filter(lambda x: (x % 2 == 0), goal))
                else:
                    index_list = list(filter(lambda x: (x % 2 == 1), goal))

            code = listen_to_goal(index_list, cl, addr)

def send_code(code, client):
    print(f'enviando {code}')
    client.send('HTTP/1.0 200 OK\r\n\r\n')
    print('enviando dato')
    client.send(code.encode())
    print('cerrando')
    client.close()

def do_connect():
    debug_pin = Pin(20, Pin.OUT)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect("Senora de lo Angeles", "44556677")
        while not sta_if.isconnected():
            pass
    debug_pin.value(1)
    print('network config:', sta_if.ifconfig())



if __name__ == "__main__":  
    do_connect()
    main()
    

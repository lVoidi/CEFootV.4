from machine import Pin, ADC, UART
import network
import _thread
import random
import socket
import time
import uos 

data_pin = Pin(13, Pin.OUT)
latch_pin = Pin(15, Pin.OUT)
clock_pin = Pin(14, Pin.OUT)



# Boton del team y leds
change_player_signal = Pin(28, Pin.IN, Pin.PULL_UP)
current_team_playing = "blue"

blue_team = Pin(0, Pin.OUT)

red_team = Pin(1, Pin.OUT)

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

def listen_to_goal(goalkeeper_indices, team):
    global blue_team,red_team, current_team_playing
    pressed_button_index = 0
    values = [
        button.value() for button in goal_buttons
    ]
    print(goalkeeper_indices)
    while not any(values):
        if change_player_signal.value() and current_team_playing == "blue":
            print(red_team.value(), blue_team.value())
            current_team_playing = "red"
            blue_team.value(0)
            red_team.value(1)
        elif change_player_signal.value() and current_team_playing == "red":
            current_team_playing = "blue"
            blue_team.value(1)
            red_team.value(0)
        
        values = [
            button.value() for button in goal_buttons
        ]
        time.sleep(0.5)
    
    code = False
    goal = ""
    for i in range(6):
        if i in goalkeeper_indices:
            goal += "1"
        else:
            goal += "0"

    for index, value in enumerate(values):
        if value:
            pressed_button_index = index
        if value and index in goalkeeper_indices:
            code = f"B:{index}:{goal}"
            break
    else:    
        code = f"A:{pressed_button_index}:{goal}"

    goal_leds[pressed_button_index].value(1)
    print(pressed_button_index, goal_leds[pressed_button_index])
    time.sleep(3)
    goal_leds[pressed_button_index].value(0)
    return code

code = ""

def main():
    global blue_team, code, red_team, current_team_playing
    current_team_playing = "blue"
    # Leds de cada paleta
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    s.settimeout(100)
    print(f"[DEBUG] Escuchando al puerto 8080, en {addr}")

    goal = [i for i in range(6)]
    while True:
        if change_player_signal.value() and current_team_playing == "blue":
            current_team_playing = "red"
            blue_team.value(0)
            red_team.value(1)
        elif change_player_signal.value() and current_team_playing == "red":
            current_team_playing = "blue"
            blue_team.value(1)
            red_team.value(0)

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
        code = listen_to_goal(index_list, current_team_playing)
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
        print(f"[DEBUG] Cliente conectado desde: {addr}")
        cl.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
        cl.sendall(code.encode("utf-8"))
        cl.close()

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect("Senora de lo Angeles", "44556677")
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())



if __name__ == "__main__":  
    do_connect()
    main()
    

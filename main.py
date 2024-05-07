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
    return int((pot.read_u16()/65535)*100)//16

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
    goal = ""
    for i in range(6):
        if i in goalkeeper_indices:
            goal += "1"
        else:
            goal += "0"
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

    code = prefix# + f"{pressed_button_index}"
    if pressed:
        goal_leds[pressed_button_index].value(1)
        send_code(code, cl, addr, timeout=0)
        print(pressed_button_index, goal_leds[pressed_button_index])
        time.sleep(3)
        goal_leds[pressed_button_index].value(0)
    
    

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
        cl, addr = s.accept()
        print(f"[DEBUG] Cliente conectado desde: {addr} ")
        request = cl.recv(1024).decode().upper().split("\n")
        signal = ""
        for request_content in request:
            if "LENGTH" in request_content:
                request_content = request_content.split(":")[1]
                if "2" in request_content:
                    signal = "SIGTEAM"
                elif "3" in request_content:
                    signal = "SIGPOT"       
                else:
                    signal = "SIGGOAL"
        print(signal)
        if signal == "SIGTEAM":
            selected = False
            while not selected:
                print(selected)
                if change_player_signal.value() and current_team_playing == "blue":
                    current_team_playing = "red"
                    selected = True
                    blue_team.value(0)
                    red_team.value(1)
                elif change_player_signal.value() and current_team_playing == "red":
                    current_team_playing = "blue"
                    selected = True
                    blue_team.value(1)
                    red_team.value(0)
            print("sending code")
            if current_team_playing == "blue":
                send_code(f"C:1", cl, addr)
            else:
                send_code(f"C:0", cl, addr)
            time.sleep(0.25)
        elif signal  == "SIGPOT":
            send_code(f"C:{return_pot_val()}", cl, addr)
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

def send_code(code, client, address, timeout=0):
    if timeout > 5:
        cl_file = client.makefile('r')
        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
    print(f'enviando {code}')
    client.send('HTTP/1.0 200 OK\r\n\r\n')
    print('enviando dato')
    client.sendall(code.encode())
    print('cerrando')
    client.close()

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect("Senora de lo Angeles", "Brinco2020")
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())



if __name__ == "__main__":  
    do_connect()
    main()
    

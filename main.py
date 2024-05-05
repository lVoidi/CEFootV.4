from machine import Pin, ADC, UART
import network
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

blue_team = {
    "pin": Pin(0, Pin.OUT),
    "nombre": "", 
    "goles": {}, # {"artillero": n} donde n es la cantidad de goles 
    "fallados": [], 
}

red_team = {
    "pin": Pin(1, Pin.OUT),
    "nombre": "", 
    "goles": {}, # {"artillero": n} donde n es la cantidad de goles 
    "fallados": [], 
}

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

baudrate = 115200


pot = ADC(26)

def return_pot_val():
    return int((pot.read_u16()/65535)*100)//50

def listen_to_goal(goalkeeper_indices, team):
    global blue_team,red_team, current_team_playing
    pressed_button_index = 0
    values = [
        button.value() for button in goal_buttons
    ]
    while not any(values):
        print(change_player_signal.value())
        if change_player_signal.value() and current_team_playing == "blue":
            print(red_team["pin"].value(), blue_team["pin"].value())
            current_team_playing = "red"
            blue_team["pin"].value(0)
            red_team["pin"].value(1)
        elif change_player_signal.value() and current_team_playing == "red":
            current_team_playing = "blue"
            blue_team["pin"].value(1)
            red_team["pin"].value(0)
        
        
        values = [
            button.value() for button in goal_buttons
        ]
        time.sleep(0.5)
    
    for index, value in enumerate(values):
        if value:
            pressed_button_index = index
        if value and index in goalkeeper_indices:
            
            print("A"*128)
    else:    
        print("B"*128)
            # Código para cuando el equipo no hace gol
    goal_leds[pressed_button_index].value(1)
    print(pressed_button_index, goal_leds[pressed_button_index])
    time.sleep(2)
    goal_leds[pressed_button_index].value(0)

def main():
    global blue_team,red_team, current_team_playing
    current_team_playing = "blue"
    # Leds de cada paleta
    goal = [i for i in range(6)]
    while True:
        print(change_player_signal.value())
        if change_player_signal.value() and current_team_playing == "blue":
            current_team_playing = "red"
            blue_team["pin"].value(0)
            red_team["pin"].value(1)
        elif change_player_signal.value() and current_team_playing == "red":
            current_team_playing = "blue"
            blue_team["pin"].value(1)
            red_team["pin"].value(0)

        anotation_algorithm = random.randint(1, 3)

        # Índices de las paletas en las que está el portero
        index_list = []
        if anotation_algorithm == 1:
            goalkeeper_index = random.choice(goal)
            index_list = [goalkeeper_index, goalkeeper_index + 1] if goalkeeper_index + 1 < len(goal) else [goalkeeper_index - 1, goalkeeper_index]
        elif anotation_algorithm == 2:
            goalkeeper_index = random.choice(goal)
            ndex_list = []
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
        listen_to_goal(index_list, current_team_playing)


def create_http_server():
    pins = [Pin(i, Pin.IN) for i in (0, 2, 4, 5, 12, 13, 14, 15)]

    html = """<!DOCTYPE html>
    <html>
        <head> <title>ESP8266 Pins</title> </head>
        <body> <h1>ESP8266 Pins</h1>
            <table border="1"> <tr><th>Pin</th><th>Value</th></tr> %s </table>
        </body>
    </html>
    """
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print('listening on', addr)

    while True:
        cl, addr = s.accept()
        print('client connected from', addr)
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
        rows = ['<tr><td>%s</td><td>%d</td></tr>' % (str(p), p.value()) for p in pins]
        response = html % '\n'.join(rows)
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())



if __name__ == "__main__":  
    do_connect()
    create_http_server()
    #main()
    

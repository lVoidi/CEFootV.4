from machine import Pin, ADC
import random
import time

data_pin = Pin(13, Pin.OUT)
latch_pin = Pin(15, Pin.OUT)
clock_pin = Pin(14, Pin.OUT)

# Boton del team y leds
change_player_signal = Pin(5, Pin.IN, Pin.PULL_UP)
blue_team = {
    "pin": Pin(26, Pin.OUT),
    "nombre": "", 
    "goles": {}, # {"artillero": n} donde n es la cantidad de goles 
    "fallados": [], 
}

red_team = {
    "pin": Pin(27, Pin.OUT),
    "nombre": "", 
    "goles": {}, # {"artillero": n} donde n es la cantidad de goles 
    "fallados": [], 
}

# Empieza con el azul como team inicial
blue_team["pin"].high()
red_team["pin"].low()


# Botones de cada paleta 
goal_buttons = [
    Pin(7, Pin.IN),
    Pin(8, Pin.IN),
    Pin(9, Pin.IN),
    Pin(10, Pin.IN),
    Pin(11, Pin.IN),
    Pin(12, Pin.IN),
]

pot = ADC(Pin(26))

def listen_to_goal(goalkeeper_indices, team):
    values = [
        button.value() for button in goal_buttons
    ]
    while not any(values):
        values = [
            button.value() for button in goal_buttons
        ]
    
    for index, value in enumerate(values):
        if value and index in goalkeeper_indices:
            print("no gol")
            break   
    else:    
        print("gol")
            # Código para cuando el equipo no hace gol
    print(values)
    time.sleep(2)

def main():
    current_team_playing = "blue"
    # Leds de cada paleta
    goal = [i for i in range(6)]
    while True:
        if change_player_signal.value():
            current_team_playing = "red"
            blue_team["pin"].low()
            red_team["pin"].high()
        else:
            current_team_playing = "blue"
            blue_team["pin"].high()
            red_team["pin"].low()

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

if __name__ == "__main__":
    main()

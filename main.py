from machine import Pin
import threading
import random
import utime

data_pin = Pin(13, Pin.OUT)
latch_pin = Pin(15, Pin.OUT)
clock_pin = Pin(14, Pin.OUT)

# Boton del team y leds
change_player_signal = Pin(5, Pin.IN, Pin.PULL_UP)
blue_team = Pin(26, Pin.OUT)
red_team = Pin(27, Pin.OUT)
blue_team.high()
red_team.low()


# Botones de cada paleta 
goal_buttons = [
    Pin(7, Pin.IN, Pin.PULL_UP),
    Pin(8, Pin.IN, Pin.PULL_UP),
    Pin(9, Pin.IN, Pin.PULL_UP),
    Pin(10, Pin.IN, Pin.PULL_UP),
    Pin(11, Pin.IN, Pin.PULL_UP),
    Pin(12, Pin.IN, Pin.PULL_UP),
]


def listen_to_goal(goalkeeper_indices, team):
    values = [
        button.value() for button in goal_buttons
    ]
    while not any(values):
        values = [
            button.value() for button in goal_buttons
        ]
    
    for index, value in values:
        if value and i in goalkeeper_indices:
            # Código para el gol de un equipo
            pass 
        else:
            pass
            # Código para cuando el equipo no hace gol


def main():
    current_team_playing = "blue"
    # Leds de cada paleta
    goal = [i for i in range(6)]
    while True:
        if change_player_signal.value():
            current_team_playing = "red"
            blue_team.low()
            red_team.high()
        else:
            current_team_playing = "blue"
            blue_team.high()
            red_team.low()

        anotation_algorithm = random.choice(1, 3)

        # Índices de las paletas en las que está el portero
        index_list = []
        match anotation_algorithm:
            case 1:
                goalkeeper_index = random.sample(goal, 2)
                index_list = [goalkeeper_index, goalkeeper_index + 1] if goalkeeper_index + 1 < len(goal) else [goalkeeper_index - 1, goalkeeper_index]

                # Aquí debería checar si el botón presionado está relacionado con el portero

            case 2:
                goalkeeper_index = random.sample(goal, 3)
                index_list = []
                if goalkeeper_index == len(goal) - 1:
                    index_list = [goalkeeper_index-2, goalkeeper_index-1, goalkeeper_index]
                elif goalkeeper_index == 0:
                    index_list = [goalkeeper_index, goalkeeper_index + 1, goalkeeper_index + 2]
                else:
                    index_list = [goalkeeper_index-1, goalkeeper_index, goalkeeper_index + 1]
            case 3:
                group = random.randint(0, 1)
                index_list = []
                if group == 1:
                    index_list = list(filter(lambda x: (x % 2 == 0), goal))
                else:
                    index_list = list(filter(lambda x: (x % 2 == 1), goal))
        listen_to_goal(index_list, current_team_playing)

main_thread = threading.Thread(target=main)
main_thread.start()

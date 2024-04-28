import digitalio
import random
import board

# Leds para cada equipo
blue_team = digitalio.DigitalInOut(board.GP27)
red_team = digitalio.DigitalInOut(board.GP26)

blue_team.direction = digitalio.Direction.OUTPUT
red_team.direction = digitalio.Direction.OUTPUT


current_team_playing = blue_team

# Leds de cada paleta
goal = [i for i in range(6)]
reg_clk = digitalio.DigitalInOut(board.GP19)
reg_con = digitalio.DigitalInOut(board.GP18)


while True:
    anotation_algorithm = random.choice(1, 3)
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

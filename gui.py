# noinspection SpellCheckingInspection
# Arrow icon: https://www.flaticon.com/free-icon/next_2885955?term=pixel+arrow&page=1&position=1&origin=search&related_id=2885955
from comunicate import update_data
from PIL import Image, ImageTk
from pathlib import Path
import tkinter as tk
import threading
import json
import random
import time
import pygame
import os

DEFAULT = {
    "Manchester United": {
        "score": 0,
        "shots": 0,
        "scores": {
            "Cavani": {
                "score": 0,
                "shots": 0
            },
            "harry": {
                "score": 0,
                "shots": 0
            },
            "RonaldoMU": {
                "score": 0,
                "shots": 0
            }
        }
    },
    "Barcelona": {
        "score": 0,
        "shots": 0,
        "scores": {
            "Lewi": {
                "score": 0,
                "shots": 0
            },
            "Neymar": {
                "score": 0,
                "shots": 0
            },
            "Pessi": {
                "score": 0,
                "shots": 0
            }
        }
    },
    "Real Madrid": {
        "score": 0,
        "shots": 0,
        "scores": {
            "Bale": {
                "score": 0,
                "shots": 0
            },
            "Ronaldo": {
                "score": 0,
                "shots": 0
            },
            "Vinicius": {
                "score": 0,
                "shots": 0
            }
        }
    }
}


class Player:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.score = 0
        self.shots = 0


class Goalie:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.saved = 0


class Team:
    def __init__(self, name: str):
        self.name = name
        self.score = 0
        self.shot = 0
        self.player: Player = None
        self.goalie: Goalie = None
        self.shot_record = ["empty" for _ in range(5)]
        self.path = Path(f"assets/{name}/")
        self.logo = self.path.joinpath("logo.jpg")
        self.logo_png = self.path.joinpath("logo.png")
        self.goalies_path = self.path.joinpath("goalie")
        self.players_path = self.path.joinpath("player")
        self.goalies = []
        self.players = []
        for name in os.listdir(self.goalies_path):
            self.goalies.append(Goalie(name.replace(".jpg", "").replace(".png",
                                                                        "").replace("jpeg", ""),
                                       self.goalies_path.joinpath(name)))
        for name in os.listdir(self.players_path):
            self.players.append(Player(name.replace(".jpg", "").replace(".png",
                                                                        "").replace("jpeg", ""),
                                       self.players_path.joinpath(name)))


def movement_ratio(x):
    return -1.778 * x * (x - 1.5)


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.ball_image_id = None
        pygame.mixer.init()
        pygame.mixer.music.load("assets/bgmusic.mp3")
        pygame.mixer.music.play(loops=-1)
        pygame.mixer.music.set_volume(1.0)
        # Constantes
        self.wm_attributes('-alpha', 0.5)
        self.ON_FAIL = pygame.mixer.Sound("assets/abucheo.mp3")
        self.ON_GOAL = pygame.mixer.Sound("assets/gol.mp3")
        self.ON_SHOT = pygame.mixer.Sound("assets/shot.mp3")
        self.ON_EXPLOSION = pygame.mixer.Sound("assets/explosion.mp3")
        self.ON_START = pygame.mixer.Sound("assets/pito.mp3")
        self.ON_SELECT = pygame.mixer.Sound("assets/select.mp3")
        self.image_counter = 0
        self.ball = 0
        self.shooting_points = []
        # Configuración inicial
        self.config(
            bg="#000000",
            width=1920,
            height=1080,

        )
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)

        # Pantalla principal
        background = self.image("assets/main_win_background.png", (1920, 1080))
        background_widget = tk.Label(
            self,
            bd=0,
            relief="flat",
            image=background
        )

        start_button = self.button("Iniciar juego", self.select_team_screen)
        about_button = self.button("Acerca de", self.show_about_page)

        background_widget.place(x=0, y=0)
        start_button.place(x=360, y=840)
        about_button.place(x=1150, y=840)
        self.divisions = []
        self.game_canvas: tk.Canvas = None
        self.red_team: Team = None
        self.blue_team: Team = None
        self.defending_team: Team = None
        self.is_team_selected = False
        self.current_team_playing: Team = None
        self.blue_team_widget = None
        self.red_team_widget = None
        self.team_selecting_title = None
        self.player_widget = None
        self.goalie_widget = None
        self.is_player_selected = False
        self.player_title = None

        self.teams_pool = [Team("Barcelona"), Team("Manchester United"), Team("Real Madrid")]
        self.bind("<Key>", lambda e: self.close(e))

    def image(self, name, resolution):
        image = ImageTk.PhotoImage(Image.open(name).resize(resolution))
        setattr(self, f"img{self.image_counter}", image)
        self.image_counter += 1
        return image

    def show_stats(self):
        local_window = tk.Toplevel(self)
        local_window.config(
            bg="#000000",
            width=1920,
            height=1080
        )
        ganador = f"{self.defending_team.name}"
        if self.current_team_playing.score > self.defending_team.score:
            ganador = f"{self.current_team_playing.name}"
        title = tk.Label(
            text=f"Ganador: {ganador}",
            pady=50,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 50)
        )
        stats = {}
        with open("stats.json") as file:
            stats_file = file.read()
            stats = json.loads(stats_file)

        local_team_name = self.current_team_playing.name
        defending_team_name = self.defending_team.name

        old_stats = stats

        for player in self.current_team_playing.players:
            stats[local_team_name]["scores"][player.name] = {
                "score": player.score + old_stats[local_team_name]["scores"][player.name]["score"],
                "shots": player.shots + old_stats[local_team_name]["scores"][player.name]["shots"],
            }

        stats[local_team_name]["score"] = old_stats[local_team_name]["score"] + self.current_team_playing.score
        stats[local_team_name]["shots"] = old_stats[local_team_name]["shots"] + self.current_team_playing.shot

        for player in self.defending_team.players:
            stats[defending_team_name]["scores"][player.name] = {
                "score": player.score + old_stats[defending_team_name]["scores"][player.name]["score"],
                "shots": player.shots + old_stats[defending_team_name]["scores"][player.name]["shots"],
            }

        stats[defending_team_name]["score"] = old_stats[defending_team_name]["score"] + self.defending_team.score
        stats[defending_team_name]["shots"] = old_stats[defending_team_name]["shots"] + self.defending_team.shot

        new_stats = json.dumps(stats)
        with open("stats.json", "w") as file:
            file.write(new_stats)

        best_local = sorted(stats[local_team_name]["scores"].items(),
                            key=lambda x: x[1]['score'], reverse=True)

        best_defending = sorted(stats[defending_team_name]["scores"].items(),
                                key=lambda x: x[1]['score'], reverse=True)

        local_team_best = best_local[:3]
        defending_best = best_defending[:3]

        text_local = ""
        for player in best_local:
            score = stats[local_team_name]["scores"][player[0]]["score"]
            shots = stats[local_team_name]["scores"][player[0]]["shots"]
            percent = 0
            if shots:
                percent = (score / shots) * 100
            text_local += f"""
{player[0]}
{shots} tiros
{score} goles
{percent}%
            """

        text_defending = ""
        for player in best_defending:
            score = stats[defending_team_name]["scores"][player[0]]["score"]
            shots = stats[defending_team_name]["scores"][player[0]]["shots"]
            percent = 0
            if shots:
                percent = (score / shots) * 100
            text_defending += f"""
{player[0]}
{shots} tiros
{score} goles
{percent}%
                    """

        info_local = tk.Label(
            local_window,
            text=f"""
Tiros: {stats[local_team_name]["shots"]}
Goles: {stats[local_team_name]["score"]}
% de anotación: {(stats[local_team_name]["score"] / stats[local_team_name]["shots"]) * 100}
-----------------
Mejores jugadores:
{text_local}
            """,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 30)
        )

        info_defending = tk.Label(
            local_window,
            text=f"""
        Tiros: {stats[defending_team_name]["shots"]}
        Goles: {stats[defending_team_name]["score"]}
        % de anotación: {(stats[defending_team_name]["score"] / stats[defending_team_name]["shots"]) * 100}
        -----------------
        Mejores jugadores:
        {text_defending}
                    """,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 30)
        )
        local_window.attributes("-topmost", True)
        local_window.attributes("-fullscreen", True)

        info_local.grid(row=1, column=0, sticky="nsew")
        info_defending.grid(row=1, column=1, sticky="nsew")
        title.grid(row=0, column=0, columnspan=1, sticky="nsew")

    def button(self, text, on_activation, master=None):
        button_widget = tk.Button(
            self if not master else master,
            text=text,
            relief="flat",
            bg="#111111",
            fg="#ffffff",
            font=("04b", 40),
            command=lambda: self.button_sfx(on_activation)
        )
        return button_widget

    def button_sfx(self, aditional_method):
        self.ON_SELECT.play()
        aditional_method()

    def close(self, event):
        if event.keysym == 'q' or event.keysym == 'Q':
            self.destroy()

    def show_about_page(self):
        local_window = tk.Toplevel(self)
        local_window.config(
            bg="#000000",
            width=1920,
            height=1080
        )

        back_arrow = self.image("assets/arrow.png", (128, 128))
        back_arrow_widget = tk.Button(
            local_window,
            relief="flat",
            overrelief="flat",
            bg="#000000",
            bd=0,
            image=back_arrow,
            command=lambda: self.button_sfx(local_window.destroy)
        )

        background = self.image("assets/about_page.png", (1792, 1080))
        background_widget = tk.Label(
            local_window,
            bd=0,
            relief="flat",
            image=background
        )
        back_arrow_widget.place(x=0, y=0)
        background_widget.place(x=128, y=0)
        local_window.attributes("-fullscreen", True)
        local_window.attributes("-topmost", True)

    def select_team_screen(self):
        local_window = tk.Toplevel(self)
        local_window.config(
            bg="#000000",
            width=1920,
            height=1080
        )

        back_arrow = self.image("assets/arrow.png", (128, 128))
        back_arrow_widget = tk.Button(
            local_window,
            relief="flat",
            overrelief="flat",
            bg="#000000",
            bd=0,
            image=back_arrow,
            command=lambda: self.button_sfx(local_window.destroy)
        )

        back_arrow_widget.place(x=0, y=0)

        blue_team_image = self.image(self.teams_pool[0].logo, (512, 512))
        red_team_image = self.image(self.teams_pool[1].logo, (512, 512))
        self.blue_team_widget = tk.Label(
            local_window,
            bd=0,
            relief="flat",
            image=blue_team_image
        )
        self.red_team_widget = tk.Label(
            local_window,
            bd=0,
            relief="flat",
            image=red_team_image
        )
        self.team_selecting_title = tk.Label(
            local_window,
            text=f"Seleccionando: Azul",
            pady=100,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 40)
        )

        select_button = self.button("Seleccionar", self.set_team, master=local_window)

        self.blue_team_widget.place(x=256, y=256)
        self.red_team_widget.place(x=1152, y=256)
        select_button.place(x=700, y=800)
        self.team_selecting_title.pack()
        local_window.attributes("-fullscreen", True)
        local_window.attributes("-topmost", True)
        selecting_team_thread = threading.Thread(target=self.selecting_team, args=(local_window,))
        selecting_team_thread.start()

    def selecting_team(self, master):
        while not self.is_team_selected:
            try:
                pot_value = int(update_data("SIGPOT"))
            except:  # La única excepcion print(self.shooting_points, index, final_coords):
                continue
            self.blue_team = self.teams_pool[pot_value]
            blue_team_image = self.image(self.blue_team.logo, (512, 512))
            self.blue_team_widget["image"] = blue_team_image
            time.sleep(1)

        self.is_team_selected = False
        self.team_selecting_title["text"] = "Seleccionando: Rojo"

        while not self.is_team_selected:
            try:
                pot_value = int(update_data("SIGPOT"))
            except:  # La única excepcion print(self.shooting_points, index, final_coords):
                continue
            self.red_team = self.teams_pool[pot_value]
            red_team_image = self.image(self.red_team.logo, (512, 512))
            self.red_team_widget["image"] = red_team_image
            time.sleep(1)
        self.is_team_selected = False
        master.destroy()
        self.open_coin_window()

    def set_team(self):
        if self.blue_team != self.red_team:
            self.is_team_selected = True

    def set_player(self):
        self.is_player_selected = True

    def open_coin_window(self):
        coin_window = tk.Toplevel(self)
        coin_window.config(
            bg="#000000",
            width=1920,
            height=1080
        )

        if not self.current_team_playing:
            self.current_team_playing = random.choice((self.blue_team, self.red_team))
        self.defending_team = self.blue_team if self.current_team_playing != self.blue_team else self.red_team
        title = tk.Label(
            coin_window,
            text=f"{self.current_team_playing.name} Inicia",
            pady=500,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 40)
        )
        frames = [
            self.image(f"assets/Coin/frame{n}.png", (128, 128)) for n in range(1, 7)
        ]
        coin = tk.Label(
            coin_window,
            bd=0,
            relief="flat",
            image=frames[0]
        )
        title.pack()
        coin.place(x=1800 // 2, y=600)
        coin_window.attributes("-topmost", True)
        coin_window.attributes("-fullscreen", True)
        coin_animation = threading.Thread(target=self.animate_coin, args=(frames, coin, coin_window,))
        coin_animation.start()

    def animate_coin(self, frames, coin, master):
        initial_time = time.time()
        while 0 <= time.time() - initial_time <= 5:
            for frame in frames:
                coin["image"] = frame
                time.sleep(0.05)
        master.destroy()
        self.select_player()

    def select_player(self):
        player_window = tk.Toplevel(self)
        player_window.config(
            bg="#000000",
            width=1920,
            height=1080
        )

        player_image = self.image(self.current_team_playing.players[0].path, (512, 512))
        goalie_image = self.image(self.defending_team.goalies[0].path, (512, 512))

        self.player_widget = tk.Label(
            player_window,
            bd=0,
            relief="flat",
            image=player_image
        )

        self.goalie_widget = tk.Label(
            player_window,
            bd=0,
            relief="flat",
            image=goalie_image
        )

        self.player_title = tk.Label(
            player_window,
            text=f"{self.current_team_playing.name}: {self.current_team_playing.players[0].name}",
            pady=100,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 40)
        )

        player_button = self.button("Seleccionar", self.set_player, master=player_window)

        self.player_widget.place(x=256, y=256)
        self.goalie_widget.place(x=1152, y=256)
        player_button.place(x=700, y=800)
        self.player_title.pack()
        player_window.attributes("-topmost", True)
        player_window.attributes("-fullscreen", True)

        selecting_player_thread = threading.Thread(target=self.selecting_player, args=(player_window,))
        selecting_player_thread.start()

    def selecting_player(self, master):
        while not self.is_player_selected:
            try:
                pot_value = int(update_data("SIGPOT"))
            except:  # La única excepcion print(self.shooting_points, index, final_coords):
                continue
            player = self.current_team_playing.players[pot_value]
            self.current_team_playing.player = player
            player_image = self.image(player.path, (512, 512))
            self.player_widget["image"] = player_image
            self.player_title["text"] = f"{self.current_team_playing.name}: {player.name}"
            time.sleep(1)
        self.is_player_selected = False
        while not self.is_player_selected:
            try:
                pot_value = int(update_data("SIGPOT"))
            except:  # La única excepcion print(self.shooting_points, index, final_coords):
                continue
            goalie = self.defending_team.goalies[pot_value]
            self.defending_team.goalie = goalie
            goalie_image = self.image(goalie.path, (512, 512))
            self.goalie_widget["image"] = goalie_image
            self.player_title["text"] = f"{self.defending_team.name}: {goalie.name}"
            time.sleep(1)
        self.is_player_selected = False
        master.destroy()
        self.start_playing()

    def start_playing(self):
        game = tk.Toplevel(self)
        game.config(
            bg="#000000",
            width=1920,
            height=1080
        )
        game.attributes("-topmost", True)
        game.attributes("-fullscreen", True)
        pygame.mixer.music.stop()
        pygame.mixer.music.load("assets/crowd.mp3")
        pygame.mixer.music.play(loops=-1)

        game_canvas = tk.Canvas(
            game,
            width=1920,
            height=1080,
            bg=f"#cafbfb"
        )
        self.game_canvas = game_canvas
        background = self.image("assets/back.png", (1920, 1080))
        background_image = game_canvas.create_image(
            0, 0,
            image=background,
            anchor="nw"
        )

        ball = self.image("assets/ball.png", (128, 128))
        self.ball = game_canvas.create_image(
            960, 975,
            image=ball,
            anchor="center"
        )

        goal_coordinates = 472, 199, 1450, 669
        goal_division = []
        goal_width = goal_coordinates[2] - goal_coordinates[0]
        goal_anchor = goal_width // 6
        initial, final = goal_coordinates[0], goal_coordinates[2]
        for i in range(6):
            x0, y0, x1, y1 = goal_coordinates
            goal_division.append(
                [initial, y0, initial + goal_anchor, y1]
            )
            if 0 <= len(self.shooting_points) <= 5:
                self.shooting_points.append([(2 * initial + goal_anchor) // 2, (y0 + y1) // 2])
            initial += goal_anchor

        penalties_blue, penalties_red = [], []
        for i in range(5):
            bias = i * 20 + 20
            if self.blue_team.shot_record[i] == "empty":
                oval_blue = game_canvas.create_oval(
                    bias + i * 100, 20, bias + 100 + i * 100, 120,
                    width=10
                )
                penalties_blue.append(oval_blue)
            elif self.blue_team.shot_record[i] == "goal":
                oval_blue = game_canvas.create_oval(
                    bias + i * 100, 20, bias + 100 + i * 100, 120,
                    fill="#aaffaa",
                    width=10
                )
                penalties_blue.append(oval_blue)
            elif self.blue_team.shot_record[i] == "failed":
                oval_blue = game_canvas.create_oval(
                    bias + i * 100, 20, bias + 100 + i * 100, 120,
                    fill="#ffaaaa",
                    width=10
                )
                penalties_blue.append(oval_blue)
            if self.red_team.shot_record[i] == "empty":
                oval_red = game_canvas.create_oval(
                    1920 - i * 100 - bias, 20, 1920 - (i * 100 + 100) - bias, 120,
                    width=10
                )
                penalties_red.append(oval_red)
            elif self.red_team.shot_record[i] == "goal":
                oval_red = game_canvas.create_oval(
                    1920 - i * 100 - bias, 20, 1920 - (i * 100 + 100) - bias, 120,
                    width=10,
                    fill="#aaffaa"
                )
                penalties_red.append(oval_red)
            elif self.red_team.shot_record[i] == "failed":
                oval_red = game_canvas.create_oval(
                    1920 - i * 100 - bias, 20, 1920 - (i * 100 + 100) - bias, 120,
                    width=10,
                    fill="#ffaaaa"
                )
                penalties_red.append(oval_red)

        self.divisions = []

        for division in goal_division:
            div = game_canvas.create_rectangle(
                *division
            )
            self.divisions.append(div)

        blue_team = self.image(self.blue_team.logo_png, (256, 256))
        red_team = self.image(self.red_team.logo_png, (256, 256))
        game_canvas.create_image(
            250, 350,
            image=blue_team
        )
        game_canvas.create_image(
            1920 - 250, 350,
            image=red_team
        )

        game_canvas.pack()
        check_goal = threading.Thread(target=self.wait_for_shot, args=(game,))
        check_goal.start()

    def wait_for_shot(self, master):
        time.sleep(2)
        self.ON_START.play()
        initial_time = time.time()
        listener = update_data("SIGGOAL")

        final_time = time.time()
        is_goal, index, goalie = listener.split(":")

        for i, division in enumerate(self.divisions):
            if goalie[i] == "1":
                self.game_canvas.itemconfig(division, fill="#aaaaaa")
        self.game_canvas.tag_raise(self.ball)
        self.draw_ball_shot(int(index))
        if is_goal == "1" and final_time - initial_time <= 5:
            self.ON_GOAL.play()
            title = self.game_canvas.create_text(
                0, 1080 // 2,
                text="GOLAZO!!!",
                fill="#000000",
                anchor="center",
                font=("Platinum Sign", 60)
            )
            title_2 = self.game_canvas.create_text(
                5, 5 + 1080 // 2,
                text="GOLAZO!!!",
                fill="#ffffff",
                anchor="center",
                font=("Platinum Sign", 60)
            )
            for i in range(40):
                self.game_canvas.move(title, 40 - i, 0)
                self.game_canvas.move(title_2, 40 - i, 0)
                time.sleep(0.025)
            for i in range(20):
                self.game_canvas.move(title, 1, 0)
                self.game_canvas.move(title_2, 1, 0)
                time.sleep(0.05)
            for i in range(1000):
                self.game_canvas.move(title, i, 0)
                self.game_canvas.move(title_2, i, 0)
                time.sleep(0.005)

            self.current_team_playing.shot_record[self.current_team_playing.shot] = "goal"
            self.current_team_playing.player.shots += 1
            self.current_team_playing.player.score += 1
            self.current_team_playing.score += 1



        else:
            text = "ES UN \nP*JA\n DE PORTERO!!!"
            if final_time - initial_time > 5:
                text = "Tiro perdido\n POR TIEMPO"
            self.ON_FAIL.play()
            title = self.game_canvas.create_text(
                0, 1080 // 2,
                text=text,
                fill="#000000",
                justify="center",
                anchor="center",
                font=("Platinum Sign", 60)
            )
            title_2 = self.game_canvas.create_text(
                5, 5 + 1080 // 2,
                text=text,
                justify="center",
                fill="#ffffff",
                anchor="center",
                font=("Platinum Sign", 60)
            )
            for i in range(40):
                self.game_canvas.move(title, 40 - i, 0)
                self.game_canvas.move(title_2, 40 - i, 0)
                time.sleep(0.025)
            for i in range(20):
                self.game_canvas.move(title, 1, 0)
                self.game_canvas.move(title_2, 1, 0)
                time.sleep(0.1)
            for i in range(1000):
                self.game_canvas.move(title, i, 0)
                self.game_canvas.move(title_2, i, 0)
                time.sleep(0.005)
            self.current_team_playing.shot_record[self.current_team_playing.shot] = "failed"
            self.current_team_playing.player.shots += 1
            self.defending_team.goalie.saved += 1
        self.current_team_playing.shot += 1
        time.sleep(3)

        waiting_for_team_change = self.game_canvas.create_text(
            400, 500,
            text="PRESIONAR BOTON\n DE\n CAMBIO DE EQUIPO",
            justify="center",
            fill="#000000",
            anchor="nw",
            font=("04b", 50)
        )
        waiting_for_team_change_2 = self.game_canvas.create_text(
            400 - 5, 500 - 5,
            text="PRESIONAR BOTON\n DE\n CAMBIO DE EQUIPO",
            justify="center",
            fill="#ffffff",
            anchor="nw",
            font=("04b", 50)
        )

        if self.defending_team.shot == 5 and self.current_team_playing.shot == 5:
            self.show_stats()
            master.destroy()
        else:
            change_team = update_data("SIGTEAM")
            self.defending_team, self.current_team_playing = self.current_team_playing, self.defending_team
            master.destroy()
            self.select_player()

    def draw_ball_shot(self, index):
        self.ON_SHOT.play()
        final_coords = self.shooting_points[index]
        reference = (960, 975)
        difference_x = final_coords[0] - reference[0]
        difference_y = final_coords[1] - reference[1]
        print(self.shooting_points,
              index, final_coords,
              difference_y, difference_x, "\n\n\n")
        initial_time = time.time()
        t = time.time() - initial_time
        size = 128
        angle = 360
        last_pos = ()
        while 0 <= t <= 0.75:
            size = int(128 * (1 - t))
            ratio = movement_ratio(t)
            angle = 360 * ratio
            bias = 50
            if difference_x < 0:
                bias = -50

            new_position = (reference[0] + (difference_x + bias) * ratio,
                            reference[1] + (difference_y - 100) * ratio)

            last_pos = new_position
            frame = Image.open("assets/ball.png").rotate(angle).resize((size, size))
            image = ImageTk.PhotoImage(frame)
            self.ball_image_id = image
            self.game_canvas.coords(
                self.ball, *new_position
            )
            self.game_canvas.itemconfig(self.ball, image=image)
            t = time.time() - initial_time
        size = 32
        difference_x = final_coords[0] - last_pos[0]
        difference_y = final_coords[1] - last_pos[1]
        new_position = ()
        while 0 <= t <= 1.5:
            ratio = movement_ratio(t)
            angle = 360 * ratio

            new_position = (last_pos[0] + difference_x * (1 - ratio),
                            last_pos[1] + difference_y * (1 - ratio))

            frame = Image.open("assets/ball.png").rotate(-angle).resize((size, size))
            image = ImageTk.PhotoImage(frame)
            self.ball_image_id = image
            self.game_canvas.coords(
                self.ball, *new_position
            )
            self.game_canvas.itemconfig(self.ball, image=image)
            t = time.time() - initial_time

        self.game_canvas.delete(self.ball)
        self.ON_EXPLOSION.play()
        frames = [
            self.image(f"assets/explosion/fram{n}.png", (256, 256)) for n in range(1, 8)
        ]
        explosion_image = self.game_canvas.create_image(
            *new_position,
            image=frames[0],
            anchor="center"
        )
        for frame in frames[1:]:
            self.game_canvas.itemconfig(explosion_image, image=frame)
            time.sleep(0.15)

        self.game_canvas.delete(explosion_image)


root = MainWindow()
root.mainloop()

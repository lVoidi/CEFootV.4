# noinspection SpellCheckingInspection
# Arrow icon: https://www.flaticon.com/free-icon/next_2885955?term=pixel+arrow&page=1&position=1&origin=search&related_id=2885955
from comunicate import update_data
from PIL import Image, ImageTk
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
import threading
import random
import time
import pygame
import os


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
        self.path = Path(f"assets/{name}/")
        self.logo = self.path.joinpath("logo.png")
        self.goalies_path = self.path.joinpath("goalie")
        self.players_path = self.path.joinpath("player")
        self.goalies = []
        self.players = []
        for name in os.listdir(self.goalies_path):
            self.goalies.append(Goalie(name.replace(".jpg", ""), self.goalies_path))
        for name in os.listdir(self.players_path):
            self.players.append(Player(name.replace(".jpg", ""), self.players_path))


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        pygame.mixer.init()
        pygame.mixer.music.load("assets/bgmusic.mp3")
        pygame.mixer.music.play(loops=-1)
        # Constantes
        self.ON_FAIL = pygame.mixer.Sound("assets/abucheo.mp3")
        self.ON_GOAL = pygame.mixer.Sound("assets/gol.mp3")
        self.ON_START = pygame.mixer.Sound("assets/pito.mp3")
        self.ON_SELECT = pygame.mixer.Sound("assets/select.mp3")
        self.image_counter = 0
        # Configuración inicial
        self.config(
            bg="#000000"
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

        self.red_team: Team = None
        self.blue_team: Team = None
        self.is_red_selected = False
        self.is_blue_selected = False
        self.blue_team_widget = None
        self.red_team_widget = None
        self.team_selecting_title = None
        self.teams_pool = [Team("Barcelona"), Team("Manchester United"), Team("Real Madrid")]
        self.current_team_playing: Team = None
        self.bind("<Key>", lambda e: self.close(e))

    def image(self, name, resolution):
        image = ImageTk.PhotoImage(Image.open(name).resize(resolution))
        setattr(self, f"img{self.image_counter}", image)
        self.image_counter += 1
        return image

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
            bg="#000000"
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
            bg="#000000"
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

        select_blue = self.button("Seleccionar azul", self.set_blue_team, master=local_window)
        select_red = self.button("Seleccionar rojo", self.set_red_team, master=local_window)

        self.blue_team_widget.place(x=256, y=256)
        self.red_team_widget.place(x=1152, y=256)
        select_blue.place(x=160, y=800)
        select_red.place(x=1050, y=800)
        self.team_selecting_title.pack()
        local_window.attributes("-fullscreen", True)
        local_window.attributes("-topmost", True)
        selecting_team_thread = threading.Thread(target=self.selecting_team, args=(local_window,))
        selecting_team_thread.start()

    def selecting_team(self, master):
        while not self.is_blue_selected:
            pot_value = int(update_data("SIGPOT"))
            self.blue_team = self.teams_pool[pot_value]
            blue_team_image = self.image(self.blue_team.logo, (512, 512))
            self.blue_team_widget["image"] = blue_team_image
            time.sleep(0.2)

        self.team_selecting_title["text"] = "Seleccionando: Rojo"

        while not self.is_red_selected:
            pot_value = int(update_data("SIGPOT"))
            self.red_team = self.teams_pool[pot_value]
            red_team_image = self.image(self.red_team.logo, (512, 512))
            self.red_team_widget["image"] = red_team_image
            time.sleep(0.2)

        master.destroy()
        self.open_coin_window()

    def set_blue_team(self):
        if self.blue_team != self.red_team:
            self.is_blue_selected = True

    def set_red_team(self):
        if self.blue_team != self.red_team:
            self.is_red_selected = True

    def open_coin_window(self):
        coin_window = tk.Toplevel(self)
        coin_window.config(
            bg="#000000"
        )

        if not self.current_team_playing:
            self.current_team_playing = random.choice((self.blue_team, self.red_team))
        title = tk.Label(
            coin_window,
            text=f"{self.current_team_playing.name} Inicia",
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
        coin.pack()
        coin_window.attributes("-topmost", True)
        coin_window.attributes("-fullscreen", True)
        coin_animation = threading.Thread(target=self.animate_coin, args=(frames, coin,))
        coin_animation.start()

    def animate_coin(self, frames, coin):
        initial_time = time.time()
        while 0 <= time.time() - initial_time <= 5:
            for frame in frames:
                coin["image"] = frame
                time.sleep(0.05)


root = MainWindow()
root.mainloop()

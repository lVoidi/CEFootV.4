# noinspection SpellCheckingInspection
# Arrow icon: https://www.flaticon.com/free-icon/next_2885955?term=pixel+arrow&page=1&position=1&origin=search&related_id=2885955

# Código que se comunica con la raspberry pi
# SIGGOAL: La raspberry se queda esperando a que se presione un botón
# de la portería. Si es gol, prende los leds con un efecto de ola; Si no,
# prende los leds de manera paralela
# SIGTEAM: La raspberry espera a que se presione el boton que cambia el color del
# led del equipo
# SIGPOT: La raspberry devuelve el valor actual del potenciómetro. El valor
# del potenciómetro es un numero entre 0 y 2, incluyéndolos.
from dataclasses import dataclass, field
from comunicate import update_data
from PIL import Image, ImageTk
from pathlib import Path
import tkinter as tk
import threading
import random
import pygame
import json
import time
import os

__version__ = "V2 12.5.2024"

# Valores por defecto de la configuración. Al darle al boton de reset,
# estos datos se suben al archivo de stats.json
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

@dataclass
class Player:
    """
    :param name: Nombre del jugador, como aparece en los archivos
    :param Path: Path del jugador, como aparece en los archivos
    """
    name: str
    path: str | Path
    score: int = 0
    shots: int = 0


@dataclass
class Goalie:
    """
    :param name: Nombre del portero (Igual que en los archivos, exceptuando extensiones)
    :param path: Path del portero
    """
    name: str
    path: str | Path


@dataclass
class Team:
    name: str
    score: int = 0
    shot: int = 0
    # Jugadores en el turno actual
    player: Player = None
    goalie: Goalie = None
    path: Path = None
    shot_record: list[str] = field(default_factory=lambda: ["empty" for _ in range(7)])
    logo: Path = None
    logo_png: Path = None
    def __post_init__(self):

        self.path: Path = Path(f"assets/{self.name}/")
        # Guarda el path del escudo del equipo, tanto su versión jpg como su
        # versión png. La versión jpg se necesita en la primera pantalla de
        # selección de equipo, y la versión png se ocupa para la pantalla de tiros
        self.logo: Path = self.path.joinpath("logo.jpg")
        self.logo_png: Path = self.path.joinpath("logo.png")
        
        # Guarda los paths tanto de los jugadores como de los porteros
        self.goalies_path: Path = self.path.joinpath("goalie")
        self.players_path: Path = self.path.joinpath("player")

        # Esta parte del código guarda una pool con todos los jugadores y
        # porteros disponibles para el equipo «name».
        self.goalies: list[str] = []
        self.players: list[str] = []
        for name in os.listdir(self.goalies_path):
            # Los replace se aseguran de quitar cualquier extensión de archivo innecesaria
            self.goalies.append(Goalie(name.replace(".jpg", "").replace(".png",
                                                                        "").replace("jpeg", ""),
                                       self.goalies_path.joinpath(name)))
        for name in os.listdir(self.players_path):
            self.players.append(Player(name.replace(".jpg", "").replace(".png",
                                                                            "").replace("jpeg", ""),
                                           self.players_path.joinpath(name)))
    


def movement_ratio(t):
    """
    Posición relativa de la bola en función del tiempo. La idea
    de esta función es emular un movimiento 3d de la bola en
    función del tiempo, para un plano 2d, como lo es un canvas
    :param t: Tiempo actual. En realidad, sería correcto denotarlo Δt pues
              este valor del tiempo en realidad es (time.time() - initial_time)
    :return: f(t) Número entre 0 y 1. Intersecciones de la gráfica en t=0 y t=1.5
    """
    return -1.778 * t * (t - 1.5)


def reset_stats():
    with open("stats.json", "w") as file:
        file.write(json.dumps(DEFAULT))


class MainWindow(tk.Tk):
    def __init__(self):
        """
        Esta clase hereda la clase tk.Tk de tkinter, para uso más
        sencillo del mismo root.
        """
        super().__init__()

        # Guarda la imagen de la bola. No confundir por
        # la id de la bola generada al crear la imagen en el canvas
        self.ball_image_id = None

        # Carga todos los sonidos y música default
        pygame.mixer.init()
        pygame.mixer.music.load("assets/bgmusic.mp3")
        pygame.mixer.music.play(loops=-1)
        pygame.mixer.music.set_volume(1.0)

        self.ON_FAIL = pygame.mixer.Sound("assets/abucheo.mp3")
        self.ON_GOAL = pygame.mixer.Sound("assets/gol.mp3")
        self.ON_SHOT = pygame.mixer.Sound("assets/shot.mp3")
        self.ON_EXPLOSION = pygame.mixer.Sound("assets/explosion.mp3")
        self.ON_START = pygame.mixer.Sound("assets/pito.mp3")
        self.ON_SELECT = pygame.mixer.Sound("assets/select.mp3")
        self.ON_VAR = pygame.mixer.Sound("assets/var.mp3")

        # Este contador de imágenes funciona para
        # evitar problemas con el garbage collector.
        self.image_counter = 0

        # ID de la bola en el self.game_canvas
        self.ball = 0
        self.blue_score = 0 
        self.red_score = 0 

        self.index = 0
        self.did_shot = False 

        # Matriz 6*2 que guarda el punto medio de cada
        # paleta. A estos puntos, es que se dirige la bola al
        # ser tirada
        self.shooting_points = []

        # Matriz 6*4 que guarda todas las paletas. Tanto posiciones iniciales
        # como posiciones finales de la paleta: (xi, yi, xf, yf)
        self.divisions = []

        # Canvas del juego principal
        self.game_canvas: tk.Canvas = None

        # Clases para cada equipo. Cabe destacar que
        # blue team y red team son una manera de diferenciar los
        # equipos. Esto no indica el jugador inicial en sí
        self.red_team: Team = None
        self.blue_team: Team = None

        # Esto indica el equipo defendiendo y el equipo tirando
        # en el turno actual
        self.defending_team: Team = None
        self.current_team_playing: Team = None

        # Estas variables se vuelven True cuando se selecciona el equipo o
        # los jugadores, para el caso de is_player_selected.
        self.is_team_selected = False
        self.is_player_selected = False

        # Guarda el widget de cada equipo
        self.blue_team_widget = None
        self.red_team_widget = None

        # Este titulo se actualiza cuando se selecciona el equipo.
        self.team_selecting_title = None

        self.player_widget = None
        self.goalie_widget = None

        self.player_title = None

        # Guarda en una pool todos los equipos posibles
        self.teams_pool = [Team("Barcelona"), Team("Manchester United"), Team("Real Madrid")]
        
        # To select players
        self.counter = 0  

        # Configuración inicial
        self.config(
            bg="#000000",
            width=1920,
            height=1080,

        )
        self.attributes("-topmost", True)
        self.attributes("-fullscreen", True)

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

        # Hace que el programa se pueda cerrar presionando la q
        self.bind("<Key>", lambda e: self.on_key_press(e))
    

    def on_key_press(self, event):
        if event.keysym == 'q' or event.keysym == 'Q':
            pygame.mixer.music.stop()
            self.destroy()
        elif event.keysym == "n":
            self.counter -= 1 
        elif event.keysym == "m":
            self.counter += 1 

    def image(self, name, resolution):
        """
        Este código devuelve una instancia de PhotoImage para facilitar
        el posicionamiento de imágenes en el código.
        :param name: Path de la imagen (str | Path)
        :param resolution: Tupla del tamaño de la imagen
        :return: Instancia de PhotoImage
        """
        image = ImageTk.PhotoImage(Image.open(name).resize(resolution))

        # Esta parte es necesaria para esquivar el garbage collector. Lo
        # que hace es asignarle a la clase de MainWindow un atributo especial,
        # que será "img«n»", donde n es el contador de imágenes. Esto evita que
        # la imagen sea borrada por el garbage collector
        setattr(self, f"img{self.image_counter}", image)
        self.image_counter += 1
        return image

    def button(self, text, on_activation, master=None):
        """
        Manera sencilla de crear un botón
        :param text: Texto del botón
        :param on_activation: función a activar en el botój
        :param master: toplevel, en caso de ser necesario
        :return: El widget del botón
        """
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
        """
        Esta funcion es un auxiliar que permite agregar un efecto de sonido
        a la hora de presionar un boton
        :param aditional_method: Metodo adicional del boton
        :return: None
        """
        self.ON_SELECT.play()
        aditional_method()

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

        local_window.attributes("-topmost", True)
        local_window.attributes("-fullscreen", True)
        self.blue_team_widget.place(x=256, y=256)
        self.red_team_widget.place(x=1152, y=256)
        select_button.place(x=700, y=800)
        self.team_selecting_title.pack()
        local_window.bind("<Key>", lambda e: self.on_key_press(e))
        selecting_team_thread = threading.Thread(target=self.selecting_team, args=(local_window,))
        selecting_team_thread.start()

    def selecting_team(self, master):
        while not self.is_team_selected:
            value = self.counter % 3
            self.blue_team = self.teams_pool[value]
            blue_team_image = self.image(self.blue_team.logo, (512, 512))
            self.blue_team_widget["image"] = blue_team_image
            time.sleep(0.01)

        self.is_team_selected = False
        self.team_selecting_title["text"] = "Seleccionando: Rojo"

        while not self.is_team_selected:
            value = self.counter % 3
            self.red_team = self.teams_pool[value]
            red_team_image = self.image(self.red_team.logo, (512, 512))
            self.red_team_widget["image"] = red_team_image
            time.sleep(0.01)
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
        # Selecciona aleatoriamente uno de los equipos como local
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
        # Anima la moneda por 5 segundos
        initial_time = time.time()
        while 0 <= time.time() - initial_time <= 2:
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
        player_window.bind("<Key>", lambda e: self.on_key_press(e))

        selecting_player_thread = threading.Thread(target=self.selecting_player, args=(player_window,))
        selecting_player_thread.start()

    def selecting_player(self, master):
        while not self.is_player_selected:
            value = self.counter % 3
            player = self.current_team_playing.players[value]
            self.current_team_playing.player = player
            player_image = self.image(player.path, (512, 512))
            self.player_widget["image"] = player_image
            self.player_title["text"] = f"{self.current_team_playing.name}: {player.name}"
            time.sleep(0.01)
        self.is_player_selected = False
        while not self.is_player_selected:
            value = self.counter % 3
            goalie = self.defending_team.goalies[value]
            self.defending_team.goalie = goalie
            goalie_image = self.image(goalie.path, (512, 512))
            self.goalie_widget["image"] = goalie_image
            self.player_title["text"] = f"{self.defending_team.name}: {goalie.name}"
            time.sleep(0.01)
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
        # Crea cada una de las paletas
        for i in range(6):
            x0, y0, x1, y1 = goal_coordinates
            goal_division.append(
                [initial, y0, initial + goal_anchor, y1]
            )

            # Agrega los puntos medios
            if 0 <= len(self.shooting_points) <= 5:
                self.shooting_points.append([(2 * initial + goal_anchor) // 2, (y0 + y1) // 2])
            initial += goal_anchor

        self.blue_score = self.game_canvas.create_text(
            256, 256, 
            text="0",
            justify="center",
            fill="#000000",
            anchor="center",
            font=("04b", 60)
        )

        self.red_score = self.game_canvas.create_text(
            1920-256, 256, 
            text="0",
            justify="center",
            fill="#000000",
            anchor="center",
            font=("04b", 60)
        )

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
        game.bind("<Key>", lambda e: self.do_shot(e))
        check_goal = threading.Thread(target=self.wait_for_shot, args=(game,))
        check_goal.start()

    def do_shot(self, event):
        if event.keysym in "123456":
            self.index = int(event.keysym) - 1
            self.did_shot = True
            time.sleep(0.01)
        self.did_shot = False

    def show_stats(self):
        """
        Muestra la pantalla de estadísticas
        :return: None
        """
        self.withdraw()

        local_window = tk.Toplevel(self)
        local_window.config(
            bg="#000000"
        )

        # Determina el equipo ganador
        winner = f"{self.defending_team.name}"
        if self.current_team_playing.score > self.defending_team.score:
            winner = f"{self.current_team_playing.name}"
        elif self.current_team_playing.score == self.defending_team.score:
            winner = "Empate"
        title = tk.Label(
            local_window,
            text=f"Ganador: {winner}",
            justify="center",
            pady=50,
            fg="#ffffff",
            bg="#000000",
            font=("04b", 50)
        )

        # Esto carga las estadísticas ya guardadas en el archivo stats.json
        stats = {}
        with open("stats.json") as file:
            stats_file = file.read()
            stats = json.loads(stats_file)

        # Asignados nuevos nombres para mayor facilidad
        local_team_name = self.current_team_playing.name
        defending_team_name = self.defending_team.name

        # Variable auxiliar que permite trabajar con las stats antiguas, ya que la
        # variable stats es modificada constantemente
        old_stats = stats

        # |===============| Equipo local |===============|
        for player in self.current_team_playing.players:
            # Actualiza las stats de cada jugador del team local
            stats[local_team_name]["scores"][player.name] = {
                "score": player.score + old_stats[local_team_name]["scores"][player.name]["score"],
                "shots": player.shots + old_stats[local_team_name]["scores"][player.name]["shots"],
            }

        # Actualiza las stats globales del equipo local
        stats[local_team_name]["score"] = old_stats[local_team_name]["score"] + self.current_team_playing.score
        stats[local_team_name]["shots"] = old_stats[local_team_name]["shots"] + self.current_team_playing.shot

        # |===============| Equipo defensor |===============|
        for player in self.defending_team.players:
            # Actualiza las stats de cada jugador del team defensor
            stats[defending_team_name]["scores"][player.name] = {
                "score": player.score + old_stats[defending_team_name]["scores"][player.name]["score"],
                "shots": player.shots + old_stats[defending_team_name]["scores"][player.name]["shots"],
            }

        # Actualiza las stats globales del equipo defensor
        stats[defending_team_name]["score"] = old_stats[defending_team_name]["score"] + self.defending_team.score
        stats[defending_team_name]["shots"] = old_stats[defending_team_name]["shots"] + self.defending_team.shot

        # Objeto json de las stats, luego es subido al archivo de stats
        new_stats = json.dumps(stats)
        with open("stats.json", "w") as file:
            file.write(new_stats)

        # Estas lineas consiguen los 3 mejores jugadores de cada
        # uno de los equipos. Ordena a los jugadores por goles
        best_local = sorted(stats[local_team_name]["scores"].items(),
                            key=lambda x: x[1]['score'], reverse=True)
        #                   ~~~~^^^^^^^^^^^^^^^^^^^^^^^~~~~
        #                   Estas lineas se encargan de ordenar cada
        #                   Uno de los items de este diccionario por goles

        best_defending = sorted(stats[defending_team_name]["scores"].items(),
                                key=lambda x: x[1]['score'], reverse=True)

        # Obtiene los 3 mejores de cada uno
        local_team_best = best_local[:3]
        defending_best = best_defending[:3]

        # En esta variable guarda las stats de cada uno de los jugadores
        # del equipo local
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

        # En esta variable guarda las stats de cada uno de los jugadores del
        # equipo defensor
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
        # Stats de cada equipo
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
            justify="center",
            fg="#ffffff",
            bg="#000000",
            font=("04b", 20)
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
            justify="center",
            fg="#ffffff",
            bg="#000000",
            font=("04b", 20)
        )
        reset_button = self.button("Resetear stats", reset_stats, master=local_window)
        exit_button = self.button("Salir", self.destroy, master=local_window)

        info_local.grid(row=1, column=0, sticky="nsew")
        info_defending.grid(row=1, column=1, sticky="nsew")
        reset_button.grid(row=2, column=0, columnspan=2, sticky="nsew")
        exit_button.grid(row=3, column=0, columnspan=2, sticky="nsew")
        title.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def wait_for_shot(self, master):
        anotation_algorithm = random.randint(1, 3)

        # Índices de las paletas en las que está el portero
        # Elige uno de los índices aleatorios
        update_data(f"SIGSCORE {self.current_team_playing.score}")
        goal = [i for i in range(6)]
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
        time.sleep(2)
        self.ON_START.play()
        initial_time = time.time()

        while not self.did_shot:
            pass

        final_time = time.time()
        index = self.index
        is_goal = True
        if index in index_list:
            is_goal = False

        for i, division in enumerate(self.divisions):
            if i in index_list:
                self.game_canvas.itemconfig(division, fill="#aaaaaa")

        self.game_canvas.tag_raise(self.ball)
        self.draw_ball_shot(index)
        if is_goal and final_time - initial_time <= 5:
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
            for i in range(100):
                self.game_canvas.move(title, i, 0)
                self.game_canvas.move(title_2, i, 0)
                time.sleep(0.005)
            
            self.current_team_playing.player.shots += 1
            self.current_team_playing.player.score += 1
            self.current_team_playing.score += 1



        else:
            text = "ES UN \nPIJA\n DE PORTERO!!!"
            if final_time - initial_time > 5:
                text = "TIRO PERDIDO\n POR TIEMPO"
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
            for i in range(100):
                self.game_canvas.move(title, i, 0)
                self.game_canvas.move(title_2, i, 0)
                time.sleep(0.005)
            self.current_team_playing.player.shots += 1
            self.defending_team.goalie.saved += 1

        self.current_team_playing.shot += 1
        update_data(f"SIGSCORE {self.current_team_playing.score}")

        time.sleep(3)
        # Termina la partida si ambos equipos tienen 5 disparos
        if (self.defending_team.shot == 7 and self.current_team_playing.shot == 7) or self.defending_team.shot > 7 or self.current_team_playing.shot > 7:

            if self.defending_team.name == "Real Madrid" and self.defending_team.score <= self.current_team_playing.score:
                self.ON_VAR.play()
                title_2 = self.game_canvas.create_text(
                    500, 5 + 1080 // 2,
                    text=f"El VAR HA DECIDIDO\n RESTARLE 3 GOLES A\n {self.current_team_playing.name.upper()}",
                    justify="center",
                    fill="#ffffff",
                    anchor="center",
                    font=("Platinum Sign", 40)
                )
                self.current_team_playing.score = int(update_data(f"SIGVAR {self.current_team_playing.score}"))
            elif self.current_team_playing.name == "Real Madrid" and self.current_team_playing.score <= self.defending_team.score:
                self.ON_VAR.play()
                title_2 = self.game_canvas.create_text(
                    500, 5 + 1080 // 2,
                    text=f"El VAR HA DECIDIDO\n RESTARLE 3 GOLES A\n {self.defending_team.name.upper()}",
                    justify="center",
                    fill="#ffffff",
                    anchor="center",
                    font=("Platinum Sign", 40)
                )
                self.current_team_playing.score = int(update_data(f"SIGVAR {self.current_team_playing.score}"))

            
            time.sleep(5)
            self.show_stats()
            master.destroy()
        else:
            do_var_event = random.randint(1, 3) == 1
            # do_var_event = True
            if do_var_event:
                self.ON_VAR.play()
                self.current_team_playing.score = int(update_data(f"SIGVAR {self.current_team_playing.score}"))
                print(self.current_team_playing.score)

                title_2 = self.game_canvas.create_text(
                    700, 5 + 1080 // 2,
                    text=f"EL VAR HA DECIDIDO\n RESTARLE 3 GOLES A\n {self.current_team_playing.name.upper()}",
                    justify="center",
                    fill="#ffffff",
                    anchor="center",
                    font=("Platinum Sign", 50)
                )
                self.current_team_playing.shot = self.current_team_playing.score + 1 if self.current_team_playing.score < 8 else self.current_team_playing.score
                self.defending_team.shot = self.current_team_playing.score + 1 if self.current_team_playing.score < 8 else self.current_team_playing.score

                print(self.current_team_playing.score, self.current_team_playing.name)
                print(self.current_team_playing.shot, self.current_team_playing.name)
                print(self.defending_team.shot, self.defending_team.name)
                print(self.defending_team.score, self.defending_team.name)

                time.sleep(5)
            update_data("SIGTEAM")
            self.defending_team, self.current_team_playing = self.current_team_playing, self.defending_team
            master.destroy()
            self.select_player()

    def draw_ball_shot(self, index):
        """
Dibuja el movimiento de la bola. Este movimiento está descrito por una función
cuadrática, que se encargará de crear la ilusión de un movimiento acelerado, a su
vez de un efecto tridimensional del disparo, donde el tamaño de la bola funciona
como la profundidad del campo.

El movimiento de la bola está dividido en 2 tractos. En el primero, la bola se
moverá uniformemente acelerada en dirección de un punto en específico. Este punto
está dado desde el punto de referencia inicial, que es aproximadamente el centro
de la pantalla. A partir de este punto, la partícula se va a mover un porcentaje
de su diferencia respecto al punto final (diferencia + bias). Recordemos que el
bias es un valor adicional para que la bola de el efecto de curvatura.
Este porcentaje, es dado por la función llamada movement_ratio (un número entre 0 y 1).
Esto sucede en funcion del tiempo para 0 <= Δt <= 0.75, osea, para la mitad del trayecto.

En el segundo trayecto, la bola empieza a caer, a causa de la parábola generada por movement_ratio
Sin embargo, en este caso el punto de referencia cambia para que el punto final sea el punto medio
de la paleta «index». Esto no sería posible si se hiciera el movimiento en un solo transecto, ya que
la bola terminaríá yendo al punto inicial. Al final del disparo, la bola crea una explosión.
        :param index: Índice de la paleta presionada
        :return:
        """
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
            ratio = movement_ratio(t)  # 0 <= ratio <= 1
            angle = 360 * ratio

            # El bias da el efecto de curvatura
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

        # Animación de la explosión
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

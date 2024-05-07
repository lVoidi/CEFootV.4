from comunicate import update_data
from PIL import Image, ImageTk
from tkinter import messagebox
import tkinter as tk
import threading
import random
import pygame
import time

pygame.mixer.init()
pygame.mixer.music.load("assets/crowd.mp3")
pygame.mixer.music.play(loops=-1)

main_window = tk.Tk()
main_window.config(bg="#000000")
main_window.attributes("-fullscreen", True)
main_window.attributes("-topmost", True)

logo = ImageTk.PhotoImage(
    Image.open("assets/logo.png").resize((1280, 720))
)

main_window.image = logo

title = tk.Label(
    main_window,
    image=logo,
    bg="#000000"
)


def close_window(event, w, win_to_deiconify=None):
    if event.keysym == 'q' or event.keysym == 'Q':
        if win_to_deiconify:
            win_to_deiconify.deiconify()
        w.destroy()


def about_page():
    main_window.withdraw()
    win = tk.Toplevel(main_window)
    win.config(bg="#000000")
    win.attributes("-fullscreen", True)
    win.attributes("-topmost", True)

    titulo = tk.Label(
        win,
        text="Creadores",
        fg="#aaaaff",
        pady=80,
        bg="#000000",
        bd=0,
        relief="flat",
        font=("04b", 50)
    )

    info = tk.Label(
        win,
        text="""Este juego fue creado por 
Rodrigo Arce Bastos (2024115582)
y David Garcia Cruz (2024115575), en Costa Rica.
Ambos somos estudiantes muy apasionados
de CE. Este programa fue creado para el 
curso Fundamentos de Sistemas Computa-
cionales en el año 2024 con el profesor
Luis Barboza Artavia.
             """,
        fg="#ffffff",
        justify="center",
        bg="#000000",
        bd=0,
        relief="flat",
        font=("04b", 25)
    )

    img1 = ImageTk.PhotoImage(Image.open("assets/creadores.png").resize((1280, 720)))

    win.img1 = img1
    rod = tk.Label(
        win,
        image=img1
    )
    titulo.pack()
    info.pack()
    rod.pack()
    win.bind("<Key>", lambda e: close_window(e, win, win_to_deiconify=main_window))


team_1 = {
    "name": "",
    "jugadores": {},
}
team_2 = {
    "name": "",
    "jugadores": {},
}
new = True


def start_game():
    main_window.withdraw()
    win = tk.Toplevel(main_window)
    win.config(bg="#000000")
    win.attributes("-fullscreen", True)
    win.attributes("-topmost", True)

    canvas_width, canvas_height = 635, 635

    canvas_1 = tk.Canvas(win, bg="#000000", width=canvas_width, height=canvas_height)
    canvas_2 = tk.Canvas(win, bg="#000000", width=canvas_width, height=canvas_height)
    canvas_3 = tk.Canvas(win, bg="#000000", width=canvas_width, height=canvas_height)

    skin1 = ImageTk.PhotoImage(
        Image.open("assets/steins_gate/logo.jpg").resize((canvas_width // 3, canvas_height // 3)))
    skin2 = ImageTk.PhotoImage(
        Image.open("assets/one_piece/one_piece.jpg").resize((canvas_width // 3, canvas_height // 3)))
    skin3 = ImageTk.PhotoImage(
        Image.open("assets/jojos/logo.png").resize((canvas_width, canvas_height)))
    win.skin1 = skin1
    win.skin2 = skin2
    win.skin3 = skin3

    canvas_1.create_image(
        canvas_width // 2, canvas_height // 2,
        image=skin1,
        anchor="center"
    )
    canvas_2.create_image(
        canvas_width // 2, canvas_height // 2,
        image=skin2,
        anchor="center"
    )
    canvas_3.create_image(
        canvas_width // 2, canvas_height // 2,
        image=skin3,
        anchor="center"
    )

    label = tk.Label(
        win,
        text="Elija equipo 1",
        fg="#ffffff",
        bg="#000000",
        font=("04b", 40)
    )

    play = tk.Button(
        win,
        text="Jugar",
        command=lambda: on_game_start(win),
        font=("04b", 40)
    )

    canvas_1.bind("<Button-1>", lambda e: on_team_select(1, label))
    canvas_2.bind("<Button-1>", lambda e: on_team_select(2, label))
    canvas_3.bind("<Button-1>", lambda e: on_team_select(3, label))

    canvas_1.grid(row=1, column=0)
    canvas_2.grid(row=1, column=1)
    canvas_3.grid(row=1, column=2)
    label.grid(row=2, column=0, columnspan=3)
    play.grid(row=3, column=0, columnspan=3)
    win.bind("<Key>", lambda e: close_window(e, win, win_to_deiconify=main_window))


selected = False


def select():
    global selected
    selected = True


def on_game_start(win):
    global selected, team_1, team_2
    if not (team_1["name"] and team_2["name"]):
        return
    win.withdraw()

    new_win = tk.Toplevel(main_window)

    new_win.config(bg="#000000")
    new_win.attributes("-fullscreen", True)
    new_win.attributes("-topmost", True)

    pool_1 = [f"{key}.jpg" for key in team_1["jugadores"].keys()]
    pool_2 = [f"{key}.jpg" for key in team_2["jugadores"].keys()]
    teams = (team_1["name"], team_2["name"])
    local_team = random.choice(teams)

    if team_1["name"] != local_team:
        team_1, team_2 = team_2, team_1

    title = tk.Label(
        new_win,
        text=f"Seleccione artillero equipo {local_team}",
        fg="#ffffff",
        bg="#000000",
        font=("04b", 40)
    )

    image = ImageTk.PhotoImage(Image.open("assets/coin.gif").resize((128, 128)))
    img = ""
    main_window.coin = image
    coin = tk.Label(
        new_win,
        image=image,
    )
    current_player = tk.Label(
        new_win,
    )
    select_button = tk.Button(
        new_win,
        text="Seleccionar",
        fg="#ffffff",
        bg="#000000",
        bd=0,
        relief="flat",
        command=select,
        font=("04b", 40)
    )

    play = tk.Button(
        new_win,
        text="Jugar",
        bd=0,
        relief="flat",
        command=select,
        font=("04b", 40)
    )

    initial = None
    if local_team == teams[0]:
        initial = ImageTk.PhotoImage(
            Image.open(f"assets/{local_team.lower().replace(" ", "_")}/{pool_1[0]}").resize((512, 512)))
    else:
        initial = ImageTk.PhotoImage(
            Image.open(f"assets/{local_team.lower().replace(" ", "_")}/{pool_2[0]}").resize((512, 512)))
    main_window.initial = initial
    current_player["image"] = initial
    coin.grid(row=0, column=0)
    title.grid(row=0, column=1)
    current_player.grid(row=1, column=0, sticky="nsew", columnspan=2)
    select_button.grid(row=2, column=0, sticky="nsew", columnspan=2)
    new_win.bind("<Key>", lambda e: close_window(e, win, win_to_deiconify=main_window))
    thread = threading.Thread(target=change_image,
                              args=(current_player, local_team, teams.index(local_team), teams, title, play))
    thread.start()


def change_image(label, local_team, team_index, teams, title, button):
    global selected
    pool_1 = [f"{key}.jpg" for key in team_1["jugadores"].keys()]
    pool_2 = [f"{key}.jpg" for key in team_2["jugadores"].keys()]
    title_list = ["artillero", "portero"]
    for pool in range(2):
        print(f"{pool=} {team_index=}")
        title["text"] = f"Seleccione el {title_list[pool]} para {teams[team_index - pool]}"
        while not selected:
            try:
                img = ""
                image = None
                if pool == 0:
                    get_pot_value = int(update_data("00\r")[1])  # Para el potenciómetro
                    img = pool_1[get_pot_value - 1]
                    image = ImageTk.PhotoImage(
                        Image.open(f"assets/{local_team.lower().replace(" ", "_")}/{img}").resize((512, 512)))
                else:
                    get_pot_value = int(update_data("00\r")[1])  # Para el potenciómetro
                    img = pool_2[get_pot_value - 1]
                    image = ImageTk.PhotoImage(
                        Image.open(f"assets/{teams[team_index - 1].lower().replace(" ", "_")}/{img}").resize(
                            (512, 512)))
                setattr(main_window, f"a{random.randint(0, 999)}", image)
                label["image"] = image
            except Exception as e:
                print("Excepción: ", e, ": Omitiendo")

        selected = False


def play_game(win, artillero, equipo):
    global team_1, team_2
    win.withdraw()
    level_window = tk.Toplevel(main_window)
    level_window.attributes("-fullscreen", True)
    level_window.attributes("-topmost", True)

    canva_juego = tk.Canvas(
        level_window,
        bd=0,
        highlightthickness=0,
        width=1920,
        height=1080
    )

    background = ImageTk.PhotoImage(Image.open("assets/back.png"))

    pito_sfx = pygame.mixer.Sound("assets/pito.mp3")
    gol_sfx = pygame.mixer.Sound("assets/gol.mp3")
    abucheo_sfx = pygame.mixer.Sound("assets/abucheo.mp3")
    pito_sfx.play()

    canva_juego.create_image(
        0, 0,
        image=background,
        anchor="nw"
    )
    done = False
    goles, cobros = 0, 0

    while not done:
        try:
            is_goal = "1" in update_data("000\r")
            cobros += 1

            if equipo == team_1["name"]:
                goles, cobros = team_1["jugadores"][artillero]
                if is_goal:
                    goles += 1
                    gol_sfx.play()
                else:
                    abucheo_sfx.play()
                cobros += 1
                team_1["jugadores"][artillero] = [goles, cobros]

            elif equipo == team_2["name"]:
                goles, cobros = team_2["jugadores"][artillero]

                if is_goal:
                    goles += 1
                    gol_sfx.play()
                else:
                    abucheo_sfx.play()
                cobros += 1

                team_2["jugadores"][artillero] = [goles, cobros]
            done = True

        except Exception as e:
            messagebox.showerror("Error interno", f"{e}: Tire la bola de nuevo.")


def on_team_select(team, label):
    global team_1, team_2, new
    if team == 1:
        if new:
            team_1 = {
                "name": "Steins Gate",
                "jugadores": {
                    "faris": [0, 0],
                    "itaru": [0, 0],
                    "kurisu": [0, 0],
                    "okabe": [0, 0],
                    "ruka": [0, 0],
                    "suzuha": [0, 0]
                }
            }
        else:
            team_2 = {
                "name": "Steins Gate",
                "jugadores": {
                    "faris": [0, 0],
                    "itaru": [0, 0],
                    "kurisu": [0, 0],
                    "okabe": [0, 0],
                    "ruka": [0, 0],
                    "suzuha": [0, 0]
                }
            }
    elif team == 2:
        if new:
            team_1 = {
                "name": "One Piece",
                "jugadores": {
                    "luffy": [0, 0],
                    "chopper": [0, 0],
                    "jinbe": [0, 0],
                    "sanji": [0, 0],
                    "zoro": [0, 0],
                    "kuma": [0, 0]
                }
            }
        else:
            team_2 = {
                "name": "One Piece",
                "jugadores": {
                    "luffy": [0, 0],
                    "chopper": [0, 0],
                    "jinbe": [0, 0],
                    "sanji": [0, 0],
                    "zoro": [0, 0],
                    "kuma": [0, 0]
                }
            }
    elif team == 3:
        if new:
            team_1 = {
                "name": "Jojos",
                "jugadores": {
                    "giorno": [0, 0],
                    "jhonny": [0, 0],
                    "jolyne": [0, 0],
                    "joseph": [0, 0],
                    "josuke": [0, 0],
                    "jotaro": [0, 0]
                }
            }
        else:
            team_2 = {
                "name": "Jojos",
                "jugadores": {
                    "giorno": [0, 0],
                    "jhonny": [0, 0],
                    "jolyne": [0, 0],
                    "joseph": [0, 0],
                    "josuke": [0, 0],
                    "jotaro": [0, 0]
                }
            }
    if new:
        label["text"] = "Elija equipo 2"
        new = False


start_button = tk.Button(
    main_window,
    text="Iniciar juego",
    fg="#ffffff",
    bg="#000000",
    bd=0,
    relief="flat",
    command=start_game,
    font=("04b", 40)
)

about_button = tk.Button(
    main_window,
    text="Acerca de",
    fg="#ffffff",
    bg="#000000",
    bd=0,
    relief="flat",
    command=about_page,
    font=("04b", 40)
)
exit_button = tk.Button(
    main_window,
    text="Salir",
    fg="#ffffff",
    bg="#000000",
    bd=0,
    relief="flat",
    command=main_window.destroy,
    font=("04b", 40)
)
title.pack()
start_button.pack()
about_button.pack()
exit_button.pack()
main_window.bind('<Key>', lambda e: close_window(e, main_window))
main_window.mainloop()

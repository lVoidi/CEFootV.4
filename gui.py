# Arrow icon: https://www.flaticon.com/free-icon/next_2885955?term=pixel+arrow&page=1&position=1&origin=search&related_id=2885955
from comunicate import update_data
from PIL import Image, ImageTk
from tkinter import messagebox
import tkinter as tk
import threading
import random
import pygame


# noinspection SpellCheckingInspection
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

        start_button = self.button("Iniciar juego", lambda: None)
        about_button = self.button("Acerca de", self.show_about_page)

        background_widget.place(x=0, y=0)
        start_button.place(x=360, y=840)
        about_button.place(x=1150, y=840)
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
        local_window.attributes("-fullscreen", True)
        local_window.attributes("-topmost", True)
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




root = MainWindow()
root.mainloop()

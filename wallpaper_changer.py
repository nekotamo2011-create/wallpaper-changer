import os
import sys
import platform
import subprocess
import ctypes
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image


APP_NAME = "Wallpaper Changer"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def set_wallpaper(image_path: str) -> None:
    system = platform.system()

    if system == "Windows":
        absolute_path = os.path.abspath(image_path)
        result = ctypes.windll.user32.SystemParametersInfoW(
            20,
            0,
            absolute_path,
            3
        )

        if not result:
            raise RuntimeError("Windows did not succeed in changing the wallpaper.")

    elif system == "Darwin":
        absolute_path = os.path.abspath(image_path)

        script = f'''
        tell application "System Events"
            tell every desktop
                set picture to "{absolute_path}"
            end tell
        end tell
        '''

        subprocess.run(
            ["osascript", "-e", script],
            check=True
        )

    elif system == "Linux":
        absolute_path = os.path.abspath(image_path)

        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

        if "gnome" in desktop or "ubuntu" in desktop:
            uri = Path(absolute_path).as_uri()
            subprocess.run(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.background",
                    "picture-uri",
                    uri
                ],
                check=True
            )
            subprocess.run(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.background",
                    "picture-uri-dark",
                    uri
                ],
                check=True
            )

        elif "kde" in desktop:
            raise RuntimeError(
                "KDE zahteva drugačiji DBus pristup. Ova verzija trenutno podržava Windows, macOS i GNOME/Ubuntu Linux."
            )

        else:
            raise RuntimeError(
                "Nepoznato Linux desktop okruženje. Najbolje radi na GNOME/Ubuntu."
            )

    else:
        raise RuntimeError("Ovaj operativni sistem nije podržan.")


class WallpaperChangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("900x560")
        self.minsize(760, 500)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.selected_image_path = None
        self.preview_image = None

        self.create_layout()

    def create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text="Wallpaper\nChanger",
            font=ctk.CTkFont(size=32, weight="bold"),
            justify="left"
        )
        self.title_label.grid(row=0, column=0, padx=30, pady=(40, 10), sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Change your desktop background with a single click.",
            font=ctk.CTkFont(size=15),
            text_color="#b7b7b7",
            wraplength=260,
            justify="left"
        )
        self.subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="w")

        self.select_button = ctk.CTkButton(
            self.sidebar,
            text="Select Image",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.choose_image
        )
        self.select_button.grid(row=2, column=0, padx=30, pady=10, sticky="ew")

        self.apply_button = ctk.CTkButton(
            self.sidebar,
            text="Apply Wallpaper",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#22a06b",
            hover_color="#1b7f55",
            command=self.apply_wallpaper
        )
        self.apply_button.grid(row=3, column=0, padx=30, pady=10, sticky="ew")

        self.clear_button = ctk.CTkButton(
            self.sidebar,
            text="Clear Selection",
            height=40,
            fg_color="#444444",
            hover_color="#555555",
            command=self.clear_selection
        )
        self.clear_button.grid(row=4, column=0, padx=30, pady=(10, 30), sticky="ew")

        self.status_title = ctk.CTkLabel(
            self.sidebar,
            text="Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_title.grid(row=5, column=0, padx=30, pady=(20, 5), sticky="w")

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="No image selected.",
            text_color="#b7b7b7",
            wraplength=260,
            justify="left"
        )
        self.status_label.grid(row=6, column=0, padx=30, pady=(0, 20), sticky="w")

        self.theme_label = ctk.CTkLabel(
            self.sidebar,
            text="Theme"
        )
        self.theme_label.grid(row=9, column=0, padx=30, pady=(20, 5), sticky="w")

        self.theme_switch = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["Dark", "Light"],
            command=self.change_theme
        )
        self.theme_switch.set("Dark")
        self.theme_switch.grid(row=10, column=0, padx=30, pady=(0, 30), sticky="ew")

        self.main_frame = ctk.CTkFrame(self, corner_radius=20)
        self.main_frame.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.preview_title = ctk.CTkLabel(
            self.main_frame,
            text="Image Preview",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.preview_title.grid(row=0, column=0, padx=25, pady=(25, 10), sticky="w")

        self.preview_container = ctk.CTkFrame(
            self.main_frame,
            fg_color="#1f1f1f",
            corner_radius=18
        )
        self.preview_container.grid(row=1, column=0, padx=25, pady=15, sticky="nsew")
        self.preview_container.grid_columnconfigure(0, weight=1)
        self.preview_container.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            self.preview_container,
            text="Selected image will be displayed here",
            text_color="#888888",
            font=ctk.CTkFont(size=16)
        )
        self.preview_label.grid(row=0, column=0, padx=20, pady=20)

        self.file_label = ctk.CTkLabel(
            self.main_frame,
            text="File: -",
            text_color="#b7b7b7",
            wraplength=520,
            justify="left"
        )
        self.file_label.grid(row=2, column=0, padx=25, pady=(5, 25), sticky="w")

    def choose_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.bmp"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        extension = Path(file_path).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            messagebox.showerror(
                "Unsupported Format",
                "Please select a JPG, JPEG, PNG or BMP image."
            )
            return

        self.selected_image_path = file_path
        self.status_label.configure(text="Image selected. Click 'Apply Wallpaper'.")
        self.file_label.configure(text=f"File: {file_path}")
        self.show_preview(file_path)

    def show_preview(self, image_path):
        try:
            image = Image.open(image_path)
            image.thumbnail((560, 340))

            self.preview_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=image.size
            )

            self.preview_label.configure(
                image=self.preview_image,
                text=""
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Unable to display image.\n\n{error}"
            )

    def apply_wallpaper(self):
        if not self.selected_image_path:
            messagebox.showwarning(
                "No Image Selected",
                "Please select an image first."
            )
            return

        try:
            set_wallpaper(self.selected_image_path)
            self.status_label.configure(text="Wallpaper changed successfully.")
            messagebox.showinfo(
                "Success",
                "Wallpaper changed."
            )

        except Exception as error:
            self.status_label.configure(text="An error occurred.")
            messagebox.showerror(
                "Error",
                str(error)
            )

    def clear_selection(self):
        self.selected_image_path = None
        self.preview_image = None

        self.preview_label.configure(
            image=None,
            text="Selected image will be displayed here"
        )

        self.file_label.configure(text="File: -")
        self.status_label.configure(text="No image selected.")

    def change_theme(self, value):
        if value == "Dark":
            ctk.set_appearance_mode("dark")
            self.preview_container.configure(fg_color="#1f1f1f")
        else:
            ctk.set_appearance_mode("light")
            self.preview_container.configure(fg_color="#eeeeee")


if __name__ == "__main__":
    app = WallpaperChangerApp()
    app.mainloop()

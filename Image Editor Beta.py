import tkinter as tk
from tkinter import filedialog, messagebox, Menu, Scale, HORIZONTAL
from PIL import Image, ImageTk, ImageEnhance
import numpy as np
import os
import time


class PhotoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("РћРїС‚РёРјРёР·РёСЂРѕРІР°РЅРЅС‹Р№ СЂРµРґР°РєС‚РѕСЂ РёР·РѕР±СЂР°Р¶РµРЅРёР№")
        self.root.geometry("800x700")
        self.root.configure(bg="#f5f5f5")
        self.image = None
        self.img_display = None
        self.original_image = None
        self.slider_window = None
        self.edit_history = []
        self.max_history = 5
        self.current_preview = None

        # Р’РµСЂС…РЅСЏСЏ РїР°РЅРµР»СЊ СЃ РєРЅРѕРїРєР°РјРё
        btn_frame = tk.Frame(root, bg="#f5f5f5")
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        button_style = {"width": 12, "bg": "#e0e0e0", "fg": "#333333", "relief": tk.RAISED, "bd": 1,
                        "font": ("Segoe UI", 9)}
        buttons = [
            ("РћС‚РєСЂС‹С‚СЊ", self.open_image), ("РЎРѕС…СЂР°РЅРёС‚СЊ", self.save_image),
            ("РЇСЂРєРѕСЃС‚СЊ", self.brightness), ("РљРѕРЅС‚СЂР°СЃС‚", self.contrast),
            ("Р§/Р‘", self.to_grayscale), ("Р РµР·РєРѕСЃС‚СЊ", self.sharpen),
            ("Р“Р°РјРјР°", self.gamma_correction), ("РЁСѓРј", self.add_noise),
            ("РЎС‚РµРєР»Рѕ", self.glass_effect), ("Р’РѕР»РЅР°", self.wave_effect),
            ("РџРѕРІРµСЂРЅСѓС‚СЊ", self.rotate), ("РћР±СЂРµР·Р°С‚СЊ", self.crop),
            ("РЎР±СЂРѕСЃ", self.reset), ("РћС‚РјРµРЅРёС‚СЊ", self.undo)
        ]

        row = 0
        col = 0
        max_cols = 5
        for text, command in buttons:
            btn = tk.Button(btn_frame, text=text, command=command, **button_style)
            btn.grid(row=row, column=col, padx=3, pady=3)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # РљР°РЅРІР° РґР»СЏ РёР·РѕР±СЂР°Р¶РµРЅРёСЏ
        self.canvas = tk.Label(root, bg="#ffffff", relief="groove", bd=2)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # РЎС‚Р°С‚СѓСЃ Р±Р°СЂ
        self.status_var = tk.StringVar()
        self.status_var.set("Р“РѕС‚РѕРІ")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#e0e0e0")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # РњРµРЅСЋ
        menu = Menu(self.root)
        self.root.config(menu=menu)

        info_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="РЎРїСЂР°РІРєР°", menu=info_menu)
        info_menu.add_command(label="Рћ РїСЂРѕРіСЂР°РјРјРµ", command=self.about)
        info_menu.add_command(label="РљРѕРЅС‚Р°РєС‚С‹", command=self.contacts)
        info_menu.add_command(label="РџРѕР»СЊР·РѕРІР°С‚РµР»СЊСЃРєРѕРµ СЃРѕРіР»Р°С€РµРЅРёРµ", command=self.license)

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def open_slider_window(self, title, minval, maxval, default, resolution, command, second_slider=None):
        if not self.image:
            messagebox.showwarning("РќРµС‚ РёР·РѕР±СЂР°Р¶РµРЅРёСЏ", "РЎРЅР°С‡Р°Р»Р° РѕС‚РєСЂРѕР№С‚Рµ РёР·РѕР±СЂР°Р¶РµРЅРёРµ!")
            return

        # Р—Р°РєСЂС‹С‚СЊ РїСЂРµРґС‹РґСѓС‰РµРµ РѕРєРЅРѕ СЃР»Р°Р№РґРµСЂР°
        if self.slider_window and tk.Toplevel.winfo_exists(self.slider_window):
            self.slider_window.destroy()

        # РЎРѕС…СЂР°РЅСЏРµРј С‚РµРєСѓС‰РµРµ СЃРѕСЃС‚РѕСЏРЅРёРµ РІ РёСЃС‚РѕСЂРёСЋ
        self.push_history()

        # РЎРѕС…СЂР°РЅСЏРµРј Р±Р°Р·РѕРІРѕРµ РёР·РѕР±СЂР°Р¶РµРЅРёРµ РґР»СЏ СЃР»Р°Р№РґРµСЂР°
        self.slider_base_image = self.image.copy()

        self.slider_window = tk.Toplevel(self.root)
        self.slider_window.title(title)
        self.slider_window.geometry("300x150")
        self.slider_window.configure(bg="#f5f5f5")
        self.slider_window.grab_set()
        self.slider_window.protocol("WM_DELETE_WINDOW", lambda: self.close_slider_window(apply=False))

        # РћСЃРЅРѕРІРЅРѕР№ СЃР»Р°Р№РґРµСЂ
        main_frame = tk.Frame(self.slider_window, bg="#f5f5f5")
        main_frame.pack(pady=5)

        tk.Label(main_frame, text=title.split(':')[0], bg="#f5f5f5").pack()

        self.current_scale = Scale(main_frame, from_=minval, to=maxval, orient=HORIZONTAL,
                                   resolution=resolution, length=250, bg="#ffffff",
                                   troughcolor="#d0d0d0", highlightbackground="#f5f5f5",
                                   font=("Segoe UI", 9))
        self.current_scale.set(default)
        self.current_scale.pack(pady=5)

        # Р’С‚РѕСЂРѕР№ СЃР»Р°Р№РґРµСЂ
        self.second_scale = None
        if second_slider:
            second_frame = tk.Frame(self.slider_window, bg="#f5f5f5")
            second_frame.pack(pady=5)

            tk.Label(second_frame, text=second_slider['label'], bg="#f5f5f5").pack()

            self.second_scale = Scale(second_frame, from_=second_slider['min'], to=second_slider['max'],
                                      orient=HORIZONTAL, resolution=second_slider['res'], length=250,
                                      bg="#ffffff", troughcolor="#d0d0d0", font=("Segoe UI", 9))
            self.second_scale.set(second_slider['default'])
            self.second_scale.pack(pady=5)

        # РљРЅРѕРїРєРё
        btn_frame = tk.Frame(self.slider_window, bg="#f5f5f5")
        btn_frame.pack(pady=5)

        btn_apply = tk.Button(btn_frame, text="РџСЂРёРјРµРЅРёС‚СЊ", width=10, bg="#4CAF50", fg="white",
                              command=lambda: self.close_slider_window(apply=True))
        btn_apply.pack(side=tk.LEFT, padx=5)

        btn_cancel = tk.Button(btn_frame, text="РћС‚РјРµРЅР°", width=10, bg="#f44336", fg="white",
                               command=lambda: self.close_slider_window(apply=False))
        btn_cancel.pack(side=tk.LEFT, padx=5)

        # РћР±СЂР°Р±РѕС‚РєР° РёР·РјРµРЅРµРЅРёР№ РІ СЂРµР°Р»СЊРЅРѕРј РІСЂРµРјРµРЅРё
        def on_change(value):
            start_time = time.time()

            # РЎРѕР·РґР°РµРј РєРѕРїРёСЋ Р±Р°Р·РѕРІРѕРіРѕ РёР·РѕР±СЂР°Р¶РµРЅРёСЏ
            img_copy = self.slider_base_image.copy()

            # РџСЂРёРјРµРЅСЏРµРј СЌС„С„РµРєС‚
            if self.second_scale:
                result = command(img_copy, float(self.current_scale.get()), float(self.second_scale.get()))
            else:
                result = command(img_copy, float(self.current_scale.get()))

            # РћР±РЅРѕРІР»СЏРµРј РёР·РѕР±СЂР°Р¶РµРЅРёРµ
            if result:
                self.image = result
                self.show_preview()

                # РћР±РЅРѕРІР»СЏРµРј СЃС‚Р°С‚СѓСЃ
                elapsed = (time.time() - start_time) * 1000
                self.update_status(f"РџСЂРёРјРµРЅРµРЅРѕ: {title} | Р’СЂРµРјСЏ: {elapsed:.1f} РјСЃ")

        self.current_scale.bind("<B1-Motion>", lambda e: on_change(self.current_scale.get()))
        self.current_scale.bind("<ButtonRelease-1>", lambda e: on_change(self.current_scale.get()))

        if self.second_scale:
            self.second_scale.bind("<B1-Motion>", lambda e: on_change(self.second_scale.get()))
            self.second_scale.bind("<ButtonRelease-1>", lambda e: on_change(self.second_scale.get()))

        # РџРµСЂРІРѕРЅР°С‡Р°Р»СЊРЅРѕРµ РѕР±РЅРѕРІР»РµРЅРёРµ
        on_change(default)

    def close_slider_window(self, apply=True):
        if not apply:
            # РћС‚РјРµРЅСЏРµРј РёР·РјРµРЅРµРЅРёСЏ
            self.undo()

        if self.slider_window:
            self.slider_window.destroy()
            self.slider_window = None
            self.update_status("Р“РѕС‚РѕРІ")

    def push_history(self):
        if self.image:
            # РЎРѕС…СЂР°РЅСЏРµРј С‚РѕР»СЊРєРѕ РїРѕСЃР»РµРґРЅРёРµ N РёР·РјРµРЅРµРЅРёР№
            if len(self.edit_history) >= self.max_history:
                self.edit_history.pop(0)
            self.edit_history.append(self.image.copy())

    def undo(self):
        if self.edit_history:
            self.image = self.edit_history.pop()
            self.show_preview()
            self.update_status("РћС‚РјРµРЅРµРЅРѕ РїРѕСЃР»РµРґРЅРµРµ РґРµР№СЃС‚РІРёРµ")
        elif self.original_image:
            self.image = self.original_image.copy()
            self.show_preview()
            self.update_status("Р’РѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРѕ РёСЃС…РѕРґРЅРѕРµ РёР·РѕР±СЂР°Р¶РµРЅРёРµ")

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("РР·РѕР±СЂР°Р¶РµРЅРёСЏ", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if path:
            if os.path.getsize(path) > 64 * 1024 * 1024:
                messagebox.showerror("РћС€РёР±РєР°", "Р¤Р°Р№Р» РїСЂРµРІС‹С€Р°РµС‚ 64 РњР‘")
                return
            try:
                self.image = Image.open(path)
                self.original_image = self.image.copy()
                self.edit_history = []
                self.push_history()  # РЎРѕС…СЂР°РЅСЏРµРј РѕСЂРёРіРёРЅР°Р» РІ РёСЃС‚РѕСЂРёСЋ
                self.show_preview()
                self.update_status(
                    f"Р—Р°РіСЂСѓР¶РµРЅРѕ: {os.path.basename(path)} | Р Р°Р·РјРµСЂ: {self.image.size[0]}x{self.image.size[1]}")
            except Exception as e:
                messagebox.showerror("РћС€РёР±РєР°", f"РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РєСЂС‹С‚СЊ РёР·РѕР±СЂР°Р¶РµРЅРёРµ:\n{e}")

    def save_image(self):
        if self.image:
            path = filedialog.asksaveasfilename(defaultextension=".jpg",
                                                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("BMP", "*.bmp"),
                                                           ("GIF", "*.gif")])
            if path:
                try:
                    self.image.save(path)
                    messagebox.showinfo("РЎРѕС…СЂР°РЅРµРЅРѕ", "РР·РѕР±СЂР°Р¶РµРЅРёРµ СѓСЃРїРµС€РЅРѕ СЃРѕС…СЂР°РЅРµРЅРѕ!")
                    self.update_status(f"РЎРѕС…СЂР°РЅРµРЅРѕ: {os.path.basename(path)}")
                except Exception as e:
                    messagebox.showerror("РћС€РёР±РєР°", f"РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕС…СЂР°РЅРёС‚СЊ РёР·РѕР±СЂР°Р¶РµРЅРёРµ:\n{e}")

    def show_preview(self):
        """РџРѕРєР°Р·С‹РІР°РµС‚ СѓРјРµРЅСЊС€РµРЅРЅСѓСЋ РІРµСЂСЃРёСЋ РёР·РѕР±СЂР°Р¶РµРЅРёСЏ"""
        if self.image:
            # РЎРѕР·РґР°РµРј СѓРјРµРЅСЊС€РµРЅРЅСѓСЋ РєРѕРїРёСЋ РґР»СЏ РїСЂРµРґРїСЂРѕСЃРјРѕС‚СЂР°
            preview = self.image.copy()

            # РћРїСЂРµРґРµР»СЏРµРј СЂР°Р·РјРµСЂС‹ РґР»СЏ РїСЂРµРґРїСЂРѕСЃРјРѕС‚СЂР°
            canvas_width = self.canvas.winfo_width() - 20
            canvas_height = self.canvas.winfo_height() - 20

            if canvas_width < 10 or canvas_height < 10:
                canvas_width, canvas_height = 700, 500

            # РЎРѕС…СЂР°РЅСЏРµРј РїСЂРѕРїРѕСЂС†РёРё
            w, h = preview.size
            ratio = min(canvas_width / w, canvas_height / h)
            new_size = (int(w * ratio), int(h * ratio))

            # РР·РјРµРЅСЏРµРј СЂР°Р·РјРµСЂ
            preview = preview.resize(new_size, Image.LANCZOS)

            # РћС‚РѕР±СЂР°Р¶Р°РµРј
            self.img_display = ImageTk.PhotoImage(preview)
            self.canvas.config(image=self.img_display)
            self.canvas.image = self.img_display

    def brightness(self):
        self.open_slider_window("РЇСЂРєРѕСЃС‚СЊ", 0.1, 3.0, 1.0, 0.1, self.apply_brightness)

    def apply_brightness(self, img, factor):
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def contrast(self):
        self.open_slider_window("РљРѕРЅС‚СЂР°СЃС‚", 0.1, 3.0, 1.0, 0.1, self.apply_contrast)

    def apply_contrast(self, img, factor):
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def to_grayscale(self):
        if self.image:
            self.push_history()
            self.image = self.image.convert("L").convert("RGB")
            self.show_preview()
            self.update_status("РџСЂРёРјРµРЅРµРЅРѕ: Р§РµСЂРЅРѕ-Р±РµР»С‹Р№ С„РёР»СЊС‚СЂ")

    def sharpen(self):
        self.open_slider_window("Р РµР·РєРѕСЃС‚СЊ", 0.1, 5.0, 1.0, 0.1, self.apply_sharpen)

    def apply_sharpen(self, img, factor):
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(factor)

    def gamma_correction(self):
        self.open_slider_window("Р“Р°РјРјР°-РєРѕСЂСЂРµРєС†РёСЏ", 0.1, 5.0, 1.0, 0.1, self.apply_gamma)

    def apply_gamma(self, img, gamma):
        inv_gamma = 1.0 / gamma
        lut = [pow(x / 255., inv_gamma) * 255 for x in range(256)] * 3
        return img.point(lut)

    def add_noise(self):
        self.open_slider_window("РЁСѓРј", 0, 30, 10, 1, self.apply_noise)

    def apply_noise(self, img, amount):
        if amount > 0:
            img_array = np.array(img)
            noise = np.random.randint(-int(amount), int(amount) + 1, img_array.shape, dtype='int16')
            noisy_img = np.clip(img_array + noise, 0, 255).astype('uint8')
            return Image.fromarray(noisy_img)
        return img

    def glass_effect(self):
        self.open_slider_window("Р­С„С„РµРєС‚ СЃС‚РµРєР»Р°", 1, 10, 3, 1, self.apply_glass)

    def apply_glass(self, img, radius):
        if radius > 0:
            img_array = np.array(img)
            h, w, _ = img_array.shape

            # Р“РµРЅРµСЂРёСЂСѓРµРј СЃР»СѓС‡Р°Р№РЅС‹Рµ СЃРјРµС‰РµРЅРёСЏ
            dx = np.random.randint(-int(radius), int(radius) + 1, size=(h, w))
            dy = np.random.randint(-int(radius), int(radius) + 1, size=(h, w))

            # РЎРѕР·РґР°РµРј СЃРµС‚РєСѓ РёРЅРґРµРєСЃРѕРІ
            y_indices, x_indices = np.indices((h, w))
            new_y = np.clip(y_indices + dy, 0, h - 1)
            new_x = np.clip(x_indices + dx, 0, w - 1)

            # РџСЂРёРјРµРЅСЏРµРј СЌС„С„РµРєС‚
            img_array = img_array[new_y, new_x]
            return Image.fromarray(img_array)
        return img

    def wave_effect(self):
        # РћРїС‚РёРјРёР·РёСЂРѕРІР°РЅРЅР°СЏ РІРµСЂСЃРёСЏ РІРѕР»РЅС‹
        second_slider = {
            'label': "РџРµСЂРёРѕРґ РІРѕР»РЅС‹:",
            'min': 10,
            'max': 200,
            'default': 64,
            'res': 1
        }
        self.open_slider_window("Р’РѕР»РЅР°: РђРјРїР»РёС‚СѓРґР°", 1, 20, 5, 1, self.apply_wave, second_slider)

    def apply_wave(self, img, amplitude, period):
        # РћРїС‚РёРјРёР·РёСЂРѕРІР°РЅРЅС‹Р№ Р°Р»РіРѕСЂРёС‚Рј СЃ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµРј NumPy
        if amplitude > 0 and period > 0:
            img_array = np.array(img)
            h, w, _ = img_array.shape

            # РЎРѕР·РґР°РµРј РєРѕРѕСЂРґРёРЅР°С‚РЅСѓСЋ СЃРµС‚РєСѓ
            y_coords = np.arange(h)
            x_coords = np.arange(w)

            # Р’С‹С‡РёСЃР»СЏРµРј РЅРѕРІС‹Рµ РєРѕРѕСЂРґРёРЅР°С‚С‹ X СЃ РІРµРєС‚РѕСЂРёР·Р°С†РёРµР№
            new_x = (x_coords + amplitude * np.sin(2 * np.pi * y_coords[:, np.newaxis] / period)).astype(int)
            new_x = np.clip(new_x, 0, w - 1)

            # РџСЂРёРјРµРЅСЏРµРј СЌС„С„РµРєС‚ СЃ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµРј РїСЂРѕРґРІРёРЅСѓС‚РѕР№ РёРЅРґРµРєСЃР°С†РёРё
            wave_img = img_array[y_coords[:, np.newaxis], new_x]
            return Image.fromarray(wave_img)
        return img

    def rotate(self):
        self.open_slider_window("РџРѕРІРѕСЂРѕС‚", 0, 360, 0, 1, self.apply_rotate)

    def apply_rotate(self, img, angle):
        return img.rotate(angle, expand=True, resample=Image.BICUBIC)

    def crop(self):
        if not self.image:
            return
        self.open_slider_window("РћР±СЂРµР·РєР° (%)", 0, 40, 10, 1, self.apply_crop)

    def apply_crop(self, img, percent):
        w, h = img.size
        border = min(w, h) * percent / 100
        left = border
        top = border
        right = w - border
        bottom = h - border
        return img.crop((left, top, right, bottom))

    def reset(self):
        if self.original_image:
            self.image = self.original_image.copy()
            self.edit_history = []
            self.push_history()
            self.show_preview()
            self.update_status("РР·РѕР±СЂР°Р¶РµРЅРёРµ СЃР±СЂРѕС€РµРЅРѕ Рє РёСЃС…РѕРґРЅРѕРјСѓ")

    def about(self):
        messagebox.showinfo("Рћ РїСЂРѕРіСЂР°РјРјРµ", "РћРїС‚РёРјРёР·РёСЂРѕРІР°РЅРЅС‹Р№ СЂРµРґР°РєС‚РѕСЂ РёР·РѕР±СЂР°Р¶РµРЅРёР№\nР’РµСЂСЃРёСЏ 3.0\n2025")

    def contacts(self):
        messagebox.showinfo("РљРѕРЅС‚Р°РєС‚С‹", "Р Р°Р·СЂР°Р±РѕС‚С‡РёРє: РћРїС‚РёРјР°Р»СЊРЅС‹Рµ Р РµС€РµРЅРёСЏ\nsupport@optimizededitor.com")

    def license(self):
        messagebox.showinfo("РЎРѕРіР»Р°С€РµРЅРёРµ",
                            "Р’С‹ РјРѕР¶РµС‚Рµ СЃРІРѕР±РѕРґРЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ СЌС‚Рѕ РџРћ РґР»СЏ Р»РёС‡РЅС‹С… С†РµР»РµР№. РљРѕРјРјРµСЂС‡РµСЃРєРѕРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ С‚СЂРµР±СѓРµС‚ Р»РёС†РµРЅР·РёРё.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditor(root)
    root.mainloop()

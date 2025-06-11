import tkinter as tk
from tkinter import filedialog, messagebox, Menu, Scale, HORIZONTAL
from PIL import Image, ImageTk, ImageEnhance
import numpy as np
import os
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

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
        btn_frame = ttk.Frame(root, padding=10)
        btn_frame.pack(side=tk.TOP, fill=tk.X)

        button_style = {"bootstyle": "secondary", "width": 12}
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
            btn = ttk.Button(btn_frame, text=text, command=command, **button_style)
            btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # РљР°РЅРІР° РґР»СЏ РёР·РѕР±СЂР°Р¶РµРЅРёСЏ
        self.canvas = ttk.Label(root, background="#ffffff", relief="groove")
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # РЎС‚Р°С‚СѓСЃ Р±Р°СЂ
        self.status_var = tk.StringVar()
        self.status_var.set("Р“РѕС‚РѕРІ")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
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

        self.slider_window = ttk.Toplevel(self.root)
        self.slider_window.title(title)
        self.slider_window.geometry("300x200")
        self.slider_window.grab_set()
        self.slider_window.protocol("WM_DELETE_WINDOW", lambda: self.close_slider_window(apply=False))

        # РћСЃРЅРѕРІРЅРѕР№ СЃР»Р°Р№РґРµСЂ
        main_frame = ttk.Frame(self.slider_window, padding=10)
        main_frame.pack(pady=5)

        ttk.Label(main_frame, text=title.split(':')[0]).pack()

        self.current_scale = ttk.Scale(main_frame, from_=minval, to=maxval, orient=HORIZONTAL,
                                       length=250)
        self.current_scale.set(default)
        self.current_scale.pack(pady=5)

        # Р’С‚РѕСЂРѕР№ СЃР»Р°Р№РґРµСЂ
        self.second_scale = None
        if second_slider:
            second_frame = ttk.Frame(self.slider_window, padding=10)
            second_frame.pack(pady=5)

            ttk.Label(second_frame, text=second_slider['label']).pack()

            self.second_scale = ttk.Scale(second_frame, from_=second_slider['min'], to=second_slider['max'],
                                          orient=HORIZONTAL, length=250)
            self.second_scale.set(second_slider['default'])
            self.second_scale.pack(pady=5)

        # РљРЅРѕРїРєРё
        btn_frame = ttk.Frame(self.slider_window, padding=10)
        btn_frame.pack(pady=5)

        btn_apply = ttk.Button(btn_frame, text="РџСЂРёРјРµРЅРёС‚СЊ", bootstyle="success",
                               command=lambda: self.close_slider_window(apply=True))
        btn_apply.pack(side=tk.LEFT, padx=5)

        btn_cancel = ttk.Button(btn_frame, text="РћС‚РјРµРЅР°", bootstyle="danger",
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

    def sharpen(self):
        self.open_slider_window("Р РµР·РєРѕСЃС‚СЊ", 0.1, 3.0, 1.0, 0.1, self.apply_sharpen)

    def apply_sharpen(self, img, factor):
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(factor)

    def gamma_correction(self):
        self.open_slider_window("Р“Р°РјРјР°-РєРѕСЂСЂРµРєС†РёСЏ", 0.1, 5.0, 1.0, 0.1, self.apply_gamma)

    def apply_gamma(self, img, gamma):
        if gamma <= 0:
            return img
        lut = [pow(i / 255.0, gamma) * 255 for i in range(256)]
        lut = list(map(int, lut)) * (3 if img.mode == 'RGB' else 1)
        return img.point(lut)

    def to_grayscale(self):
        if self.image:
            self.push_history()
            self.image = self.image.convert("L").convert("RGB")
            self.show_preview()
            self.update_status("РџСЂРёРјРµРЅРµРЅРѕ: Р§/Р‘")

    def add_noise(self):
        self.open_slider_window("РЁСѓРј", 0.0, 0.5, 0.1, 0.01, self.apply_noise)

    def apply_noise(self, img, factor):
        np_img = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 255 * factor, np_img.shape)
        noisy_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_img)

    def glass_effect(self):
        self.open_slider_window("Р­С„С„РµРєС‚ СЃС‚РµРєР»Р°", 1, 10, 3, 1, self.apply_glass)

    def apply_glass(self, img, radius):
        np_img = np.array(img)
        output = np.zeros_like(np_img)
        height, width = np_img.shape[:2]

        for y in range(height):
            for x in range(width):
                dx = int(x + np.random.uniform(-radius, radius))
                dy = int(y + np.random.uniform(-radius, radius))
                if 0 <= dx < width and 0 <= dy < height:
                    output[y, x] = np_img[dy, dx]
                else:
                    output[y, x] = np_img[y, x]
        return Image.fromarray(output)

    def wave_effect(self):
        self.open_slider_window("Р­С„С„РµРєС‚ РІРѕР»РЅС‹", 5, 30, 10, 1, self.apply_wave)

    def apply_wave(self, img, factor):
        np_img = np.array(img)
        output = np.zeros_like(np_img)
        height, width = np_img.shape[:2]
        for y in range(height):
            offset = int(factor * np.sin(2 * np.pi * y / 64))
            for x in range(width):
                nx = x + offset
                if 0 <= nx < width:
                    output[y, x] = np_img[y, nx]
                else:
                    output[y, x] = np_img[y, x]
        return Image.fromarray(output)

    def rotate(self):
        if self.image:
            self.push_history()
            self.image = self.image.rotate(90, expand=True)
            self.show_preview()
            self.update_status("РџРѕРІРµСЂРЅСѓС‚Рѕ РЅР° 90В°")

    def crop(self):
        if self.image:
            self.push_history()
            width, height = self.image.size
            new_width, new_height = width // 2, height // 2
            left = (width - new_width) // 2
            top = (height - new_height) // 2
            right = (width + new_width) // 2
            bottom = (height + new_height) // 2
            self.image = self.image.crop((left, top, right, bottom))
            self.show_preview()
            self.update_status("РР·РѕР±СЂР°Р¶РµРЅРёРµ РѕР±СЂРµР·Р°РЅРѕ")

    def reset(self):
        if self.original_image:
            self.image = self.original_image.copy()
            self.edit_history = []
            self.push_history()
            self.show_preview()
            self.update_status("РР·РѕР±СЂР°Р¶РµРЅРёРµ СЃР±СЂРѕС€РµРЅРѕ")

    def about(self):
        messagebox.showinfo("Рћ РїСЂРѕРіСЂР°РјРјРµ", "Р РµРґР°РєС‚РѕСЂ РёР·РѕР±СЂР°Р¶РµРЅРёР№ РЅР° Python\nР’РµСЂСЃРёСЏ 1.0\n2025")

    def contacts(self):
        messagebox.showinfo("РљРѕРЅС‚Р°РєС‚С‹", "Р Р°Р·СЂР°Р±РѕС‚С‡РёРє: РІР°С€Р° РєРѕРјР°РЅРґР°\nEmail: example@email.com")

    def license(self):
        messagebox.showinfo("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊСЃРєРѕРµ СЃРѕРіР»Р°С€РµРЅРёРµ",
                           "Р’С‹ РјРѕР¶РµС‚Рµ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РїСЂРѕРіСЂР°РјРјСѓ РІ РЅРµРєРѕРјРјРµСЂС‡РµСЃРєРёС… С†РµР»СЏС….")

if __name__ == "__main__":
    root = ttk.Window(themename="minty")  # СЃРІРµС‚Р»Р°СЏ С‚РµРјР° РѕС‚ ttkbootstrap
    app = PhotoEditor(root)
    root.mainloop()

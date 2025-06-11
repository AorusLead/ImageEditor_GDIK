import tkinter as tk
from tkinter import filedialog, messagebox, Menu, Scale, HORIZONTAL
from PIL import Image, ImageTk, ImageEnhance, ImageOps
import numpy as np
import os
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import utility


class PhotoEditor:
    def __init__(self, root):

        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        self.root.configure(bg="#f5f5f5")
        self.image = None
        self.img_display = None
        self.original_image = None
        self.slider_window = None
        self.edit_history = []
        self.max_history = 7
        self.current_preview = None

        # Главный контейнер
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Панель инструментов с современным дизайном
        tool_frame = ttk.LabelFrame(main_container, text="Инструменты", padding=10, bootstyle="info")
        tool_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # Стили для кнопок
        primary_style = {"bootstyle": "primary-outline", "width": 10}
        secondary_style = {"bootstyle": "secondary-outline", "width": 10}
        accent_style = {"bootstyle": "success-outline", "width": 10}

        # Группы кнопок
        file_btns = [
            ("Открыть", self.open_image, primary_style, "📂"),
            ("Сохранить", self.save_image, primary_style, "💾")
        ]

        adjust_btns = [
            ("Яркость", self.brightness, secondary_style, "☀️"),
            ("Контраст", self.contrast, secondary_style, "◐"),
            ("Гамма", self.gamma_correction, secondary_style, "γ"),
            ("Ч/Б", self.to_grayscale, secondary_style, "⚫")
        ]

        effect_btns = [
            ("Резкость", self.sharpen, accent_style, "🔍"),
            ("Шум", self.add_noise, accent_style, "✨"),
            ("Стекло", self.glass_effect, accent_style, "🔮"),
            ("Волна", self.wave_effect, accent_style, "🌊")
        ]

        transform_btns = [
            ("Повернуть", self.rotate, accent_style, "🔄"),
            ("Обрезать", self.crop, accent_style, "✂️"),
            ("Зеркало", self.mirror, accent_style, "🪞"),
            ("Сброс", self.reset, accent_style, "🔄")
        ]

        history_btns = [
            ("Отменить", self.undo, primary_style, "⏪"),
            ("Повторить", self.redo, primary_style, "⏩")
        ]

        # Создаем фреймы для групп кнопок
        groups = [
            ("Файл", file_btns),
            ("Коррекция", adjust_btns),
            ("Эффекты", effect_btns),
            ("Трансформация", transform_btns),
            ("История", history_btns)
        ]

        for group_name, buttons in groups:
            group_frame = ttk.Frame(tool_frame)
            group_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            ttk.Label(group_frame, text=group_name, font=("Helvetica", 9, "bold")).pack(pady=(0, 5))

            for text, command, style, icon in buttons:
                btn = ttk.Button(
                    group_frame,
                    text=f"{icon} {text}",
                    command=command,
                    **style
                )
                btn.pack(side=tk.TOP, fill=tk.X, pady=2)

        # Область изображения с современным оформлением
        img_frame = ttk.Frame(main_container)
        img_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Canvas с тенями и границами
        self.canvas_container = ttk.Frame(
            img_frame,
            relief="groove",
            borderwidth=2,
            bootstyle="light"
        )
        self.canvas_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.canvas_container, background="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статус бар с улучшенным дизайном
        status_frame = ttk.Frame(main_container, height=25)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")

        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            anchor="w",
            padding=(10, 0),
            bootstyle="inverse-light"
        )
        status_bar.pack(fill=tk.X)

        # Меню с современными иконками
        menu = Menu(self.root)
        self.root.config(menu=menu)

        # Меню "Файл"
        file_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть...", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=root.quit, accelerator="Alt+F4")

        # Меню "Правка"
        edit_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Отменить", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Сбросить изменения", command=self.reset)

        # Меню "Справка"
        info_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Справка", menu=info_menu)
        info_menu.add_command(label="О программе", command=self.about)
        info_menu.add_command(label="Контакты", command=self.contacts)
        info_menu.add_command(label="Пользовательское соглашение", command=self.license)

        # Привязка горячих клавиш
        root.bind("<Control-o>", lambda e: self.open_image())
        root.bind("<Control-s>", lambda e: self.save_image())
        root.bind("<Control-z>", lambda e: self.undo())
        root.bind("<Control-y>", lambda e: self.redo())

        # Переменные для истории
        self.history_index = -1

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def open_slider_window(self, title, minval, maxval, default, resolution, command, second_slider=None):
        if not self.image:
            messagebox.showwarning("Нет изображения", "Сначала откройте изображение!")
            return

        # Закрыть предыдущее окно слайдера
        if self.slider_window and tk.Toplevel.winfo_exists(self.slider_window):
            self.slider_window.destroy()

        # Сохраняем текущее состояние в историю
        self.push_history()

        # Сохраняем базовое изображение для слайдера
        self.slider_base_image = self.image.copy()

        self.slider_window = ttk.Toplevel(self.root)
        self.slider_window.title(title)
        self.slider_window.geometry("400x300")
        self.slider_window.resizable(False, False)
        self.slider_window.grab_set()
        self.slider_window.protocol("WM_DELETE_WINDOW", lambda: self.close_slider_window(apply=False))

        # Стиль для окна
        style = ttk.Style()
        style.configure('Slider.TFrame', background="#f0f0f0")

        # Основной контейнер
        main_frame = ttk.Frame(self.slider_window, padding=15, style='Slider.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Основной слайдер
        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(fill=tk.X, pady=5)

        ttk.Label(slider_frame, text=title.split(':')[0], font=("Helvetica", 10, "bold")).pack(anchor="w")

        value_frame = ttk.Frame(slider_frame)
        value_frame.pack(fill=tk.X, pady=(5, 0))

        # УДАЛЕНО: Создание слайдера здесь (первоначальное)
        # Оставлено только создание StringVar
        self.value_var1 = tk.StringVar(value=f"{default:.2f}")

        # Второй слайдер
        self.second_scale = None
        self.value_var2 = None
        if second_slider:
            slider_frame2 = ttk.Frame(main_frame)
            slider_frame2.pack(fill=tk.X, pady=10)

            ttk.Label(slider_frame2, text=second_slider['label'], font=("Helvetica", 10, "bold")).pack(anchor="w")

            value_frame2 = ttk.Frame(slider_frame2)
            value_frame2.pack(fill=tk.X, pady=(5, 0))

            self.second_scale = ttk.Scale(
                value_frame2,
                from_=second_slider['min'],
                to=second_slider['max'],
                orient=HORIZONTAL,
                length=300,
                bootstyle="info"
            )
            self.second_scale.set(second_slider['default'])
            self.second_scale.pack(side=tk.LEFT, expand=True)

            self.value_var2 = tk.StringVar(value=f"{second_slider['default']:.2f}")
            ttk.Label(value_frame2, textvariable=self.value_var2, width=5).pack(side=tk.RIGHT, padx=5)

        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)

        btn_cancel = ttk.Button(
            btn_frame,
            text="Отмена",
            bootstyle="danger-outline",
            width=12,
            command=lambda: self.close_slider_window(apply=False)
        )
        btn_cancel.grid(row=0, column=0, padx=10)

        btn_apply = ttk.Button(
            btn_frame,
            text="Применить",
            bootstyle="success",
            width=12,
            command=lambda: self.close_slider_window(apply=True)
        )
        btn_apply.grid(row=0, column=1, padx=10)

        # Функция обработки изменений
        def on_change(value):
            start_time = time.time()
            img_copy = self.slider_base_image.copy()

            if self.second_scale:
                result = command(img_copy, float(self.current_scale.get()), float(self.second_scale.get()))
                if self.value_var2:
                    self.value_var2.set(f"{self.second_scale.get():.2f}")
            else:
                result = command(img_copy, float(self.current_scale.get()))

            self.value_var1.set(f"{self.current_scale.get():.2f}")

            if result:
                self.image = result
                self.show_preview()
                elapsed = (time.time() - start_time) * 1000
                self.update_status(f"{title.split(':')[0]}: {self.value_var1.get()} | Время: {elapsed:.1f} мс")

        # СОЗДАЕМ СЛАЙДЕР ПОСЛЕ ОПРЕДЕЛЕНИЯ on_change
        self.current_scale = ttk.Scale(
            value_frame,
            from_=minval,
            to=maxval,
            orient=HORIZONTAL,
            length=300,
            bootstyle="info",
            command=lambda val: on_change(float(val))
        )
        self.current_scale.set(default)
        self.current_scale.pack(side=tk.LEFT, expand=True)

        # Добавляем Label для отображения значения ПОСЛЕ создания слайдера
        ttk.Label(value_frame, textvariable=self.value_var1, width=5).pack(side=tk.RIGHT, padx=5)

        # Привязки событий
        self.current_scale.bind("<B1-Motion>", lambda e: on_change(self.current_scale.get()))
        self.current_scale.bind("<ButtonRelease-1>", lambda e: on_change(self.current_scale.get()))

        if self.second_scale:
            self.second_scale.bind("<B1-Motion>", lambda e: on_change(self.second_scale.get()))
            self.second_scale.bind("<ButtonRelease-1>", lambda e: on_change(self.second_scale.get()))

        # Первоначальное обновление
        on_change(default)

    def close_slider_window(self, apply=True):
        if not apply:
            # Отменяем изменения
            self.undo()

        if self.slider_window:
            self.slider_window.destroy()
            self.slider_window = None
            self.update_status("Готов к работе")

    def push_history(self):
        if self.image:
            # Обрезаем историю после текущего индекса
            if self.history_index < len(self.edit_history) - 1:
                self.edit_history = self.edit_history[:self.history_index + 1]

            # Сохраняем только последние N изменений
            if len(self.edit_history) >= self.max_history:
                self.edit_history.pop(0)

            self.edit_history.append(self.image.copy())
            self.history_index = len(self.edit_history) - 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.image = self.edit_history[self.history_index].copy()
            self.show_preview()
            self.update_status(f"Отменено действие {len(self.edit_history) - self.history_index}")
        elif self.original_image:
            self.image = self.original_image.copy()
            self.show_preview()
            self.update_status("Восстановлено исходное изображение")

    def redo(self):
        if self.history_index < len(self.edit_history) - 1:
            self.history_index += 1
            self.image = self.edit_history[self.history_index].copy()
            self.show_preview()
            self.update_status(f"Повторено действие {self.history_index + 1}")

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[
            ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("Все файлы", "*.*")
        ])
        if path:
            if os.path.getsize(path) > 64 * 1024 * 1024:
                messagebox.showerror("Ошибка", "Файл превышает 64 МБ")
                return
            try:
                self.image = Image.open(path)
                self.original_image = self.image.copy()
                self.edit_history = [self.image.copy()]
                self.history_index = 0
                self.show_preview()
                self.update_status(
                    f"Загружено: {os.path.basename(path)} | Размер: {self.image.size[0]}x{self.image.size[1]} | Формат: {self.image.format} | Вес:  {int(os.path.getsize(path)/1024)}" +" КБ")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{str(e)}")

    def save_image(self):
        if self.image:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg"),
                    ("BMP", "*.bmp"),
                    ("GIF", "*.gif"),
                    ("Все файлы", "*.*")
                ])
            if path:
                try:
                    format = os.path.splitext(path)[1][1:].upper()
                    if format == "JPG": format = "JPEG"

                    self.image.save(path, format=format)
                    messagebox.showinfo("Сохранено", "Изображение успешно сохранено!")
                    self.update_status(f"Сохранено: {os.path.basename(path)} | Формат: {format}")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить изображение:\n{str(e)}")

    def show_preview(self):
        """Показывает изображение с сохранением пропорций"""
        if self.image:
            # Создаем копию для предпросмотра
            preview = self.image.copy()

            # Определяем размеры контейнера
            container_width = self.canvas_container.winfo_width() - 20
            container_height = self.canvas_container.winfo_height() - 20

            if container_width < 10 or container_height < 10:
                container_width, container_height = 700, 500

            # Сохраняем пропорции
            w, h = preview.size
            ratio = min(container_width / w, container_height / h)
            new_size = (int(w * ratio), int(h * ratio))

            # Изменяем размер
            preview = preview.resize(new_size, Image.LANCZOS)

            # Отображаем
            self.img_display = ImageTk.PhotoImage(preview)
            self.canvas.delete("all")
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            x = (canvas_width - preview.width) // 2
            y = (canvas_height - preview.height) // 2
            self.canvas.create_image(x, y, image=self.img_display, anchor=tk.NW)
            self.canvas.image = self.img_display

    def brightness(self):
        self.open_slider_window("Яркость", 0.1, 3.0, 1.0, 0.1, self.apply_brightness)

    def apply_brightness(self, img, factor):
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def contrast(self):
        self.open_slider_window("Контраст", 0.1, 3.0, 1.0, 0.1, self.apply_contrast)

    def apply_contrast(self, img, factor):
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def sharpen(self):
        self.open_slider_window("Резкость", 0.1, 3.0, 1.0, 0.1, self.apply_sharpen)

    def apply_sharpen(self, img, factor):
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(factor)

    def gamma_correction(self):
        self.open_slider_window("Гамма-коррекция", 0.1, 5.0, 1.0, 0.1, self.apply_gamma)

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
            self.update_status("Применено: Черно-белый фильтр")

    def add_noise(self):
        self.open_slider_window("Шум", 0.0, 0.5, 0.1, 0.01, self.apply_noise)

    def apply_noise(self, img, factor):
        np_img = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 255 * factor, np_img.shape)
        noisy_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_img)

    def glass_effect(self):
        self.open_slider_window("Эффект стекла", 1, 10, 3, 1, self.apply_glass)

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
        self.open_slider_window("Эффект волны", 5, 30, 10, 1, self.apply_wave)

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
            self.update_status("Повернуто на 90°")

    def mirror(self):
        if self.image:
            self.push_history()
            self.image = ImageOps.mirror(self.image)
            self.show_preview()
            self.update_status("Зеркальное отражение применено")

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
            self.update_status("Изображение обрезано")

    def reset(self):
        if self.original_image:
            self.image = self.original_image.copy()
            self.edit_history = [self.image.copy()]
            self.history_index = 0
            self.show_preview()
            self.update_status("Изображение сброшено к исходному")

    def about(self):
        messagebox.showinfo("О программе",
                            "ProImage Editor\nВерсия 2.0\n\nПрофессиональный редактор изображений\nс современным интерфейсом\n\n© 2025")

    def contacts(self):
        messagebox.showinfo("Контакты",
                            "Разработчик: Группа ПИ-23б\nКирилл Ильин\nДмитрий Харченко\nРустам Зрожевский\nКирилл Фадеев\nБогдан Зимин\n"
                            "Email: aorus.lord@yandex.com\n"
                            "Телефон: +7 (949) 638-25-50\n\n"
                            "Техническая поддержка: vk/@dmitry_order")

    def license(self):
        messagebox.showinfo("Пользовательское соглашение",
                            "Лицензионное соглашение Image Editor\n\n"
                            "1. Разрешено использование для личных и коммерческих целей\n"
                            "2. Запрещено распространение без разрешения правообладателя\n"
                            "3. Гарантии не предоставляются\n"
                            "4. Ответственность за использование несет конечный пользователь")


if __name__ == "__main__":
    root = ttk.Window(themename="minty")  # светлая тема от ttkbootstrap
    app = PhotoEditor(root)
    root.mainloop()







    #
    #   СПАСИБО ЗА ВНИМАНИЕ
    #











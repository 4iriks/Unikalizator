import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import random
import sys
import glob
import threading
from datetime import datetime

# --- ИСПРАВЛЕНИЕ ОШИБКИ PIL ---
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# ------------------------------

try:
    from moviepy.editor import VideoFileClip
    import moviepy.video.fx.all as vfx
except ImportError:
    import tkinter.messagebox

    root = tk.Tk()
    root.withdraw()
    tkinter.messagebox.showerror("Ошибка", "Библиотеки не найдены.\nВыполните: pip install \"moviepy<2.0.0\"")
    sys.exit(1)


class VideoUniquifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Уникализатор Видео PRO 6.0 (Logger Edition)")
        self.root.geometry("700x850")  # Увеличили высоту для логов
        self.root.resizable(False, False)

        # Переменные
        self.mode_var = tk.StringVar(value="single")
        self.input_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_name = tk.StringVar()

        # Настройки функций
        self.change_speed = tk.BooleanVar(value=True)
        self.mirror = tk.BooleanVar(value=False)
        self.crop = tk.BooleanVar(value=True)
        self.color_filter = tk.BooleanVar(value=True)
        self.rotate = tk.BooleanVar(value=True)
        self.trim = tk.BooleanVar(value=False)
        self.reencode = tk.BooleanVar(value=True)

        self.create_widgets()
        self.toggle_mode()

    def create_widgets(self):
        # Заголовок
        header = tk.Frame(self.root, bg="#2c3e50")
        header.pack(fill="x")
        tk.Label(header, text="🛡️ УНИКАЛИЗАТОР С ЛОГАМИ",
                 font=("Arial", 14, "bold"), fg="white", bg="#2c3e50", pady=15).pack()

        # Верхняя часть (Настройки и файлы)
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10)

        # Режим
        mode_frame = tk.LabelFrame(top_frame, text="Режим работы", font=("Arial", 9, "bold"))
        mode_frame.pack(pady=5, fill="x")
        tk.Radiobutton(mode_frame, text="Один файл", variable=self.mode_var,
                       value="single", command=self.toggle_mode).pack(side="left", padx=20)
        tk.Radiobutton(mode_frame, text="Пакетная обработка (папка)", variable=self.mode_var,
                       value="folder", command=self.toggle_mode).pack(side="left", padx=20)

        # Файлы
        self.file_frame = tk.LabelFrame(top_frame, text="📁 Пути", font=("Arial", 9, "bold"), padx=10, pady=5)
        self.file_frame.pack(pady=5, fill="x")

        self.lbl_input = tk.Label(self.file_frame, text="Исходный файл:")
        self.lbl_input.grid(row=0, column=0, sticky="w")
        self.entry_input = tk.Entry(self.file_frame, textvariable=self.input_path, width=45, state="readonly")
        self.entry_input.grid(row=1, column=0, pady=2)
        self.btn_input = tk.Button(self.file_frame, text="Обзор...", command=self.select_input, bg="#3498db",
                                   fg="white")
        self.btn_input.grid(row=1, column=1, padx=5)

        tk.Label(self.file_frame, text="Папка сохранения:").grid(row=2, column=0, sticky="w")
        tk.Entry(self.file_frame, textvariable=self.output_folder, width=45, state="readonly").grid(row=3, column=0,
                                                                                                    pady=2)
        tk.Button(self.file_frame, text="Обзор...", command=self.select_output, bg="#3498db", fg="white").grid(row=3,
                                                                                                               column=1,
                                                                                                               padx=5)

        self.lbl_name = tk.Label(self.file_frame, text="Имя файла:")
        self.lbl_name.grid(row=4, column=0, sticky="w", pady=(5, 0))
        self.entry_name = tk.Entry(self.file_frame, textvariable=self.output_name, width=45)
        self.entry_name.grid(row=5, column=0, pady=2)

        # Функции
        func_frame = tk.LabelFrame(top_frame, text="⚙️ Опции обработки", font=("Arial", 9, "bold"), padx=10, pady=5)
        func_frame.pack(pady=5, fill="both")

        functions = [
            (self.change_speed, "⚡ Скорость (±2%)"),
            (self.rotate, "📐 Микро-поворот"),
            (self.color_filter, "🎨 Микро-Цветокор (Гамма ±1%)"),  # Исправлено описание
            (self.crop, "✂️ Умный кроп"),
            (self.mirror, "🔄 Зеркало"),
            (self.trim, "⏱️ Обрезка (-1 сек)"),
        ]

        # Размещаем галочки в 2 колонки
        for i, (var, text) in enumerate(functions):
            col = 0 if i < 3 else 1
            row = i if i < 3 else i - 3
            tk.Checkbutton(func_frame, text=text, variable=var, font=("Arial", 9)).grid(row=row, column=col, sticky="w",
                                                                                        padx=20)

        # Кнопка старта
        self.process_button = tk.Button(top_frame, text="🚀 ЗАПУСТИТЬ ОБРАБОТКУ", command=self.start_thread,
                                        bg="#27ae60", fg="white", font=("Arial", 11, "bold"), height=2)
        self.process_button.pack(pady=10, fill="x")

        # --- ЛОГИ (Красивое окно снизу) ---
        log_frame = tk.LabelFrame(self.root, text="📝 Лог выполнения", font=("Arial", 9, "bold"))
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.log_text = ScrolledText(log_frame, height=12, state='disabled',
                                     bg="#2d3436", fg="#dfe6e9", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Настройка цветов для логов
        self.log_text.tag_config("INFO", foreground="#dfe6e9")  # Белый
        self.log_text.tag_config("WARN", foreground="#f1c40f")  # Желтый
        self.log_text.tag_config("SUCCESS", foreground="#2ecc71")  # Зеленый
        self.log_text.tag_config("ERROR", foreground="#e74c3c")  # Красный
        self.log_text.tag_config("CMD", foreground="#3498db")  # Синий

    def log(self, message, level="INFO"):
        """Добавляет сообщение в окно логов"""
        time_str = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{time_str}] {message}\n"

        self.log_text.config(state='normal')  # Разрешаем запись
        self.log_text.insert(tk.END, full_msg, level)
        self.log_text.see(tk.END)  # Автоскролл вниз
        self.log_text.config(state='disabled')  # Запрещаем запись

    def toggle_mode(self):
        mode = self.mode_var.get()
        if mode == "single":
            self.lbl_input.config(text="Исходный файл:")
            self.lbl_name.grid()
            self.entry_name.grid()
        else:
            self.lbl_input.config(text="Папка с видео:")
            self.lbl_name.grid_remove()
            self.entry_name.grid_remove()
        self.input_path.set("")
        self.log("Режим изменен: " + ("Один файл" if mode == "single" else "Пакетная обработка"), "CMD")

    def select_input(self):
        if self.mode_var.get() == "single":
            f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
            if f:
                self.input_path.set(f)
                base = os.path.splitext(os.path.basename(f))[0]
                self.output_name.set(base + "_new")
                self.log(f"Выбран файл: {os.path.basename(f)}")
        else:
            d = filedialog.askdirectory()
            if d:
                self.input_path.set(d)
                self.log(f"Выбрана папка: {d}")

    def select_output(self):
        d = filedialog.askdirectory()
        if d: self.output_folder.set(d)

    def start_thread(self):
        if not self.input_path.get() or not self.output_folder.get():
            messagebox.showwarning("Внимание", "Выберите пути!")
            return

        self.process_button.config(state="disabled", text="⏳ РАБОТАЮ...")
        self.log("--- ЗАПУСК ПРОЦЕССА ---", "CMD")

        t = threading.Thread(target=self.processing_logic)
        t.daemon = True
        t.start()

    def processing_logic(self):
        inp = self.input_path.get()
        out_dir = self.output_folder.get()

        files_to_process = []
        if self.mode_var.get() == "single":
            files_to_process.append(inp)
        else:
            extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.MP4', '*.MOV']
            for ext in extensions:
                files_to_process.extend(glob.glob(os.path.join(inp, ext)))

        if not files_to_process:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", "Файлы не найдены"))
            self.root.after(0, lambda: self.process_button.config(state="normal", text="🚀 ЗАПУСТИТЬ ОБРАБОТКУ"))
            self.log("Файлы не найдены", "ERROR")
            return

        total = len(files_to_process)
        self.log(f"Найдено файлов для обработки: {total}", "INFO")

        for index, video_path in enumerate(files_to_process):
            filename = os.path.basename(video_path)
            self.log(f"[{index + 1}/{total}] Начало обработки: {filename}", "CMD")

            try:
                self.process_one_video(video_path, out_dir)
                self.log(f"[{index + 1}/{total}] Успешно завершен: {filename}", "SUCCESS")
            except Exception as e:
                self.log(f"Ошибка с файлом {filename}: {str(e)}", "ERROR")
                # Для стабильности просто идем дальше
                continue

        self.log("--- ВСЕ ЗАДАЧИ ВЫПОЛНЕНЫ ---", "SUCCESS")
        self.root.after(0, lambda: messagebox.showinfo("Готово", f"Обработка завершена!"))
        self.root.after(0, lambda: self.process_button.config(state="normal", text="🚀 ЗАПУСТИТЬ ОБРАБОТКУ"))

    def process_one_video(self, input_path, output_dir):
        # Логика обработки
        video = VideoFileClip(input_path)
        w, h = video.size

        log_msg = []

        # 1. Обрезка
        if self.trim.get():
            start = random.uniform(0.5, 1.0)
            end = random.uniform(0.5, 1.0)
            if video.duration > (start + end + 3):
                video = video.subclip(start, video.duration - end)
                log_msg.append(f"Trim (-{start:.2f}s)")

        # 2. Скорость
        if self.change_speed.get():
            factor = random.uniform(0.98, 1.02)
            video = video.speedx(factor)
            log_msg.append(f"Speed ({factor:.3f}x)")

        # 3. Зеркало
        if self.mirror.get():
            video = video.fx(vfx.mirror_x)
            log_msg.append("Mirror")

        # 4. Цветокор (ИСПРАВЛЕНО: Очень мягкие значения)
        if self.color_filter.get():
            # Диапазон 0.99 - 1.01 (±1%)
            gamma_val = random.uniform(0.99, 1.01)
            video = video.fx(vfx.gamma_corr, gamma_val)

            # Контраст тоже минимальный
            contrast_val = random.uniform(0.99, 1.01)
            video = video.fx(vfx.lum_contrast, lum=0, contrast=contrast_val, contrast_thr=127)

            log_msg.append(f"Color (G:{gamma_val:.3f})")

        # 5. Поворот
        if self.rotate.get():
            angle = random.uniform(-1.0, 1.0)
            video = video.rotate(angle)
            zoom_factor = 1.03
            new_w_zoom = w / zoom_factor
            new_h_zoom = h / zoom_factor
            video = video.crop(x_center=w / 2, y_center=h / 2, width=new_w_zoom, height=new_h_zoom)
            video = video.resize((w, h))
            log_msg.append(f"Rotate ({angle:.2f}°)")

        # 6. Кроп
        if self.crop.get():
            crop_val = random.uniform(0.005, 0.015)
            new_w = int(w * (1 - crop_val))
            new_h = int(h * (1 - crop_val))
            if new_w % 2 != 0: new_w -= 1
            if new_h % 2 != 0: new_h -= 1
            video = video.crop(x_center=w / 2, y_center=h / 2, width=new_w, height=new_h)
            log_msg.append("SmartCrop")

        self.log(f"-> Применено: {', '.join(log_msg)}", "INFO")

        # Имя файла
        if self.mode_var.get() == "single":
            user_name = self.output_name.get().strip()
            if not user_name: user_name = f"video_{random.randint(100, 999)}"
            if not user_name.lower().endswith(".mp4"): user_name += ".mp4"
            final_name = user_name
        else:
            base = os.path.splitext(os.path.basename(input_path))[0]
            final_name = f"{base}_UNIQUE_{random.randint(1000, 9999)}.mp4"

        out_path = os.path.join(output_dir, final_name)
        self.log(f"-> Рендеринг в: {final_name}...", "WARN")

        video.write_videofile(
            out_path,
            codec="libx264",
            audio_codec="aac",
            bitrate=f"{random.randint(4000, 6000)}k",
            preset="ultrafast",
            threads=4,
            ffmpeg_params=['-pix_fmt', 'yuv420p'],
            logger=None
        )
        video.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoUniquifierApp(root)
    root.mainloop()
import tkinter as tk
import time
from tkinter import messagebox

from helpers.properties_interaction import read_property, write_property

classes = ["sit", "lie", "fall"]

class StatusTimerApp:
    def __init__(self, root):
        status = str(read_property("sensor_status")).upper()

        self.root = root
        self.root.title("Status Timer App")
        self.root.geometry("400x400")  # Increased window size

        # Lắng nghe sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Status Display
        self.status_label = tk.Label(root, text="CURRENT STATUS: " + status, font=("Arial", 20, "bold"), fg="red")
        self.status_label.pack(pady=20)

        # Timer Display
        self.timer_label = tk.Label(root, text="00:00:000", font=("Arial", 24, "bold"), fg="blue")
        self.timer_label.pack(pady=10)

        # Input Box
        current_id = str(read_property("selected_folder")).upper()
        self.id_label = tk.Label(root, text="CURRENT FOLDER: " + current_id, font=("Arial", 20, "bold"), fg="red")
        self.id_label.pack(pady=25)
        self.id_label = tk.Label(root, text="Nhập tên file không cần .csv (Ví dụ: 1_sit): ", font=("Arial", 12, "bold"),
                                 fg="black")
        self.id_label.pack(pady=5)
        self.id_label = tk.Label(root, text="**Lưu ý** File trùng tên sẽ tiếp tục ghi dữ liệu", font=("Arial", 12, "bold"),
                                 fg="red")
        self.id_label.pack(pady=5)
        self.input_box = tk.Entry(root, font=("Arial", 15), width=20, justify="center")
        self.input_box.pack(pady=5)

        # Toggle Button
        is_on = read_property("sensor_status") == "on"
        btn_text = "CLICK TO TURN " + ("OFF" if is_on else "ON")
        self.toggle_button = tk.Button(root, text=btn_text, font=("Arial", 16), width=20,
                                       bg="red" if is_on else "green",
                                       fg="white", command=self.toggle_status)
        self.toggle_button.pack(pady=10)

        # Timer Variables
        self.start_time = None
        self.running = False
        self.update_timer()

    def toggle_status(self):
        if read_property("sensor_status") == "off":
            if self.input_box.get().strip() == "":
                messagebox.showwarning("Cảnh báo!", "Nhập tên file!")
                return
            else:
                write_property("saved_file", self.input_box.get() + ".csv")
                write_property("sensor_status", "on")
                self.status_label.config(text="CURRENT STATUS: ON", fg="green")
                self.toggle_button.config(text="CLICK TO TURN OFF", bg="red")
                self.start_time = time.time()  # Reset timer when switching to "on"
                self.running = True
        else:
            write_property("sensor_status", "off")
            self.status_label.config(text="CURRENT STATUS: OFF", fg="red")
            self.toggle_button.config(text="CLICK TO TURN ON", bg="green")
            self.running = False

    def update_timer(self):
        if self.running and self.start_time:
            elapsed_time = int((time.time() - self.start_time) * 1000)  # Milliseconds
            minutes, ms = divmod(elapsed_time, 60000)
            seconds, ms = divmod(ms, 1000)
            self.timer_label.config(text=f"{minutes:02}:{seconds:02}:{ms:03}")

        self.root.after(10, self.update_timer)  # Update every 10ms

    def on_close(self):
        """Xử lý khi người dùng đóng cửa sổ"""
        if read_property("sensor_status") == "on":
            write_property("sensor_status", "off")  # Cập nhật trạng thái về "off"

        self.root.destroy()  # Đóng cửa sổ


def select_folder():
    # Tạo cửa sổ chọn folder
    folder_window = tk.Tk()
    folder_window.title("Chọn thư mục")
    folder_window.geometry("300x200")

    label = tk.Label(folder_window, text="Bạn muốn lưu vào folder nào?", font=("Arial", 14))
    label.pack(pady=10)

    def save_choice(choice):
        write_property("selected_folder", choice)
        folder_window.destroy()  # Đóng cửa sổ chọn folder
        main_app()  # Mở GUI chính

    for folder in classes:
        btn = tk.Button(folder_window, text=folder.upper(), font=("Arial", 14), width=10,
                        command=lambda f=folder: save_choice(f))
        btn.pack(pady=5)

    folder_window.mainloop()


def main_app():
    root = tk.Tk()
    app = StatusTimerApp(root)
    root.mainloop()


# Chạy chọn folder trước, sau đó mở GUI chính
select_folder()

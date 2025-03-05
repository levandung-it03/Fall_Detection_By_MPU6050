import threading
import tkinter as tk
import time
from tkinter import messagebox

from helpers.properties_interaction import read_property, write_property

classes = ["sit", "lie", "fall"]
app_instance = None


class StatusTimerApp:
    def __init__(self, root):
        self.countdown_thread = None
        self.monitor_thread = None
        self.stop_monitoring = False
        global app_instance
        app_instance = self
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
        self.id_label = tk.Label(root, text="**Lưu ý** File trùng tên sẽ tiếp tục ghi dữ liệu",
                                 font=("Arial", 12, "bold"),
                                 fg="red")
        self.id_label.pack(pady=5)
        self.input_box = tk.Entry(root, font=("Arial", 15), width=20, justify="center")
        self.input_box.pack(pady=5)

        # Toggle Button
        write_property("sensor_status", "off")
        btn_text = "CLICK TO TURN ON"
        self.toggle_button = tk.Button(root, text=btn_text, font=("Arial", 16), width=20, bg="green", fg="white",
                                       command=self.toggle_status)
        self.toggle_button.pack(pady=10)

        # Timer Variables
        self.start_time = None
        self.running = False
        self.update_timer()

        # Start monitoring thread
        self.start_monitoring_thread()

    def toggle_status(self):
        if read_property("sensor_status") == "off":
            if self.input_box.get().strip() == "":
                messagebox.showwarning("Cảnh báo!", "Nhập tên file!")
                return
            else:
                self.toggle_button.config(state="disabled")  # Vô hiệu hóa nút trong khi đếm ngược
                self.status_label.config(text="BẮT ĐẦU SAU: 2s", fg="orange")

                def countdown():
                    for i in range(2, 0, -1):
                        self.status_label.config(text=f"BẮT ĐẦU SAU: {i}s")
                        time.sleep(1)

                    # Switch Sensor on after countdown.
                    write_property("saved_file", self.input_box.get() + ".csv")
                    write_property("sensor_status", "on")
                    self.status_label.config(text="CURRENT STATUS: ON", fg="green")
                    self.toggle_button.config(text="CLICK TO TURN OFF", bg="red", state="normal")
                    self.start_time = time.time()  # Reset timer khi bật
                    self.running = True

                self.countdown_thread = threading.Thread(target=countdown, daemon=True).start()
        else:
            write_property("sensor_status", "off")
            self.status_label.config(text="CURRENT STATUS: OFF", fg="red")
            self.toggle_button.config(text="CLICK TO TURN ON", bg="green")
            self.running = False

    def update_timer(self):
        if self.running and self.start_time:
            if not self.timer_label.winfo_exists():  # Kiểm tra nếu label đã bị xóa
                return
            elapsed_time = int((time.time() - self.start_time) * 1000)  # Milliseconds
            minutes, ms = divmod(elapsed_time, 60000)
            seconds, ms = divmod(ms, 1000)
            self.timer_label.config(text=f"{minutes:02}:{seconds:02}:{ms:03}")

        if self.root.winfo_exists():  # Kiểm tra nếu cửa sổ còn tồn tại
            self.root.after(10, self.update_timer)

    def start_monitoring_thread(self):
        """Tạo một thread chạy ngầm để giám sát thay đổi của sensor_status"""

        def monitor_status():
            last_status = read_property("sensor_status")  # Lưu trạng thái ban đầu
            while not self.stop_monitoring:
                time.sleep(1)  # Kiểm tra mỗi giây để tránh tiêu tốn tài nguyên CPU
                current_status = read_property("sensor_status")

                if last_status == "on" and current_status == "off":  # Nếu trạng thái chuyển từ on -> off mà không nhấn nút
                    self.running = False
                    self.start_time = None
                    self.status_label.config(text="CURRENT STATUS: OFF", fg="red")
                    self.toggle_button.config(text="CLICK TO TURN ON", bg="green", state="normal")

                last_status = current_status  # Cập nhật trạng thái mới nhất

        self.monitor_thread = threading.Thread(target=monitor_status, daemon=True)
        self.monitor_thread.start()

    def on_close(self):
        """Xử lý khi người dùng đóng cửa sổ"""
        if read_property("sensor_status") == "on":
            write_property("sensor_status", "off")  # Cập nhật trạng thái về "off"

        self.stop_monitoring = True  # Dừng thread giám sát
        self.root.destroy()


def select_folder():
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

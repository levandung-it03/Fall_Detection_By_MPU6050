import os
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk

# Định nghĩa thư mục gốc
BASE_DIR = os.path.join(os.getcwd(), "dataset")
FOLDERS = ["sit", "fall", "lie"]

for folder in FOLDERS:
    folder_path = os.path.join(BASE_DIR, folder)
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        print(f"📂 {folder_path} - {len(files)} files:", files)
    else:
        print(f"🚫 Không tìm thấy thư mục: {folder_path}")

class CSVViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 CSV File Viewer")
        self.root.geometry("500x600")

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.create_main_menu()

    def create_main_menu(self):
        """Hiển thị danh sách thư mục"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.main_frame, text="📂 Chọn thư mục", font=("Arial", 14, "bold")).pack(pady=10)

        for folder in FOLDERS:
            folder_path = os.path.join(BASE_DIR, folder)
            if os.path.exists(folder_path):  # Kiểm tra nếu thư mục tồn tại
                btn = ttk.Button(self.main_frame, text=f"📁 {folder}", command=lambda f=folder: self.show_files(f))
                btn.pack(pady=5, padx=20, fill="x")

    def show_files(self, folder):
        """Hiển thị danh sách file trong thư mục"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.main_frame, text=f"📂 {folder}", font=("Arial", 14, "bold")).pack(pady=10)

        folder_path = os.path.join(BASE_DIR, folder)
        files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

        if not files:
            ttk.Label(self.main_frame, text="(Không có file CSV)", font=("Arial", 12)).pack(pady=5)

        for file in files:
            file_path = os.path.join(folder_path, file)
            btn = ttk.Button(self.main_frame, text=file, command=lambda f=file_path: self.plot_csv(f))
            btn.pack(pady=2, padx=10, fill="x")

        ttk.Button(self.main_frame, text="🔙 Quay lại", command=self.create_main_menu).pack(pady=10)

    def plot_csv(self, file_path):
        df = pd.read_csv(file_path)

        # Convert milliseconds to relative time in seconds
        df["time"] = (df["millis"] - df["millis"].min()) / 1000

        # Tạo figure với 2 subplot (2 hàng, 1 cột)
        fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

        # Plot Acceleration Components
        axes[0].plot(df["time"], df["accX"], label="X Acceleration", color="red", marker="o")
        axes[0].plot(df["time"], df["accY"], label="Y Acceleration", color="green", marker="o")
        axes[0].plot(df["time"], df["accZ"], label="Z Acceleration", color="blue", marker="o")
        if "totalAcc" in df.columns:
            axes[0].plot(df["time"], df["totalAcc"], label="Total Acceleration", color="black", linestyle="dashed",
                         marker="o")

        axes[0].set_ylabel("Acceleration (m/s²)")
        axes[0].set_title("MPU6050 Acceleration Data")
        axes[0].legend()
        axes[0].grid(True)

        # Plot Gyroscope Components
        axes[1].plot(df["time"], df["gyroX"], label="X Gyroscope", color="purple", marker="o")
        axes[1].plot(df["time"], df["gyroY"], label="Y Gyroscope", color="orange", marker="o")
        axes[1].plot(df["time"], df["gyroZ"], label="Z Gyroscope", color="brown", marker="o")

        axes[1].set_xlabel("Time (seconds)")
        axes[1].set_ylabel("Gyroscope (°/s)")
        axes[1].set_title("MPU6050 Gyroscope Data")
        axes[1].legend()
        axes[1].grid(True)

        # Điều chỉnh khoảng cách giữa các biểu đồ
        plt.tight_layout()

        # Hiển thị đồ thị
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = CSVViewerApp(root)
    root.mainloop()

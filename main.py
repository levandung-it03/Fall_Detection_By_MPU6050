import json
import os
from tkinter import messagebox

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from helpers import csv_interaction
from helpers.properties_interaction import read_property, write_property

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"Hello": "World"}


@app.websocket("/total-acceleration-by-mpu")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        status = str(read_property("sensor_status"))
        await websocket.send_text(status)
        data = await websocket.receive_text()
        if data != "ping":
            data = json.loads(data)
            if data.get("offStatus") == 1 or data.get("offStatus") == "1":
                print("Turning-off Sensor!")
                write_property("sensor_status", "off")
                messagebox.showwarning("Chú ý!", "Đã dừng ghi dữ liệu sau 3s!")
            elif data.get("m") is not None:
                print(data)
                csv_interaction.append_to_csv(
                    os.getcwd() + "/dataset/" + read_property("selected_folder") + "/" + read_property("saved_file"),
                    {
                        "millis": int(data.get("m")),
                        "accX": float(data.get("ax")),
                        "accY": float(data.get("ay")),
                        "accZ": float(data.get("az")),
                        "gyroX": float(data.get("gx")),
                        "gyroY": float(data.get("gy")),
                        "gyroZ": float(data.get("gz")),
                    },
                    ["millis", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ"]
                )

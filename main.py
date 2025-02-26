import json
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from helpers import csv_interaction
from helpers.properties_interaction import read_property

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
    try:
        while True:
            status = str(read_property("sensor_status"))
            await websocket.send_text(status)
            data = await websocket.receive_text()

            if data != "ping":
                data = json.loads(data)
                print({
                    "millis": int(data.get("m")),
                    "accX": float(data.get("ax")),
                    "accY": float(data.get("ay")),
                    "accZ": float(data.get("az")),
                    "gyroX": float(data.get("gx")),
                    "gyroY": float(data.get("gy")),
                    "gyroZ": float(data.get("gz")),
                })
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
                    }
                )
    except Exception as e:
        print(f"Error: {e}")

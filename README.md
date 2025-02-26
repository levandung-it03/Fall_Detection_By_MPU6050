## Features ##
+ [GUI] for managing MPU6050 Sensor Status
+ [GUI] for showing Plots of .csv data

## How to use it ##
### 1. CSV Plots: ###

- Open > Run "tkinters/tkinter_plots.py" to use it.

### 2. MPU6050 Sensor Status: ###

- Run server in terminal with command line as (.venv) administration:
> uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 60
- Open > Run "gui/tkinter_mpu_status.py" to use it.

### 3. Others Command ###
> uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug

> uvicorn main:app --host 0.0.0.0 --port 8000 --reload
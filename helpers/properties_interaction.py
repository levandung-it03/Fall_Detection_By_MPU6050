import os
from fileinput import filename

filename = os.path.join(os.getcwd(), "properties.txt")

def read_property(key):
    """Reads a property value from a .txt file"""
    try:
        with open(filename, "r") as file:
            for line in file:
                if line.startswith(key + "="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        print("File not found!")
    return None


def write_property(key, value):
    """Writes or updates a property in a .txt file"""
    lines = []
    found = False
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        pass  # If file doesn't exist, we create a new one

    with open(filename, "w") as file:
        for line in lines:
            if line.startswith(key + "="):
                file.write(f"{key}={value}\n")
                found = True
            else:
                file.write(line)
        if not found:
            file.write(f"{key}={value}\n")  # Add new key if not found

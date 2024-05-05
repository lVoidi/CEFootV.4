import serial
import time

port = "/dev/ttyACM0"
baudrate = 115200
serial_connection = serial.Serial(port, baudrate)
def update_data() -> None:
    with open("data_transfer.txt", "wb") as file:
        while True:
            data = serial_connection.read(128)
            if data == b"EOF":
                break 
            print(data)
            file.write(data)
            time.sleep(0.5)
            
    serial_connection.close()

update_data()

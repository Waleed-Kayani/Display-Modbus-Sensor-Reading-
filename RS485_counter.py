import serial
import time
import struct
import tkinter as tk
from tkinter import ttk

def calculate_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def create_request_command(device_address, function_code, start_address, num_registers):
    request = struct.pack('>BBHH', device_address, function_code, start_address, num_registers)
    crc = calculate_crc(request)
    return request + struct.pack('<H', crc)

class SensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sensor Data")

        # Configure the serial connection
        self.ser = serial.Serial(
            port='COM8',       # Replace with your port
            baudrate=9600,     # Replace with your sensor's baudrate
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        
        # Create and place widgets
        self.temperature_label = ttk.Label(root, text="Temperature: --°C", font=("Helvetica", 16))
        self.temperature_label.pack(pady=10)
        
        self.humidity_label = ttk.Label(root, text="Humidity: --%", font=("Helvetica", 16))
        self.humidity_label.pack(pady=10)

        self.update_data()  # Start the initial data update
        
    def read_sensor_data(self):
        device_address = 1  # Replace with your sensor's device address
        function_code = 3   # Function code for reading holding registers
        start_address = 0   # Starting register address
        num_registers = 2   # Number of registers to read

        request_command = create_request_command(device_address, function_code, start_address, num_registers)

        self.ser.write(request_command)
        time.sleep(1)  # Wait for a response
        response = self.ser.read(9)  # Read the response (number of bytes depends on your sensor's response format)

        if response and len(response) >= 9:
            # Process the response to extract humidity and temperature values
            raw_temperature = int.from_bytes(response[3:5], byteorder='big')
            humidity = int.from_bytes(response[5:7], byteorder='big') / 10.0
            
            # Adjust the formula based on sensor datasheet
            # Example: Assuming a 16-bit raw value maps linearly to -40°C to 125°C
            temperature = (raw_temperature / 1650.0) * 165.0 - 40.0
            
            return temperature, humidity
        
        return None, None

    def update_data(self):
        temperature, humidity = self.read_sensor_data()
        if temperature is not None and humidity is not None:
            self.temperature_label.config(text=f"Temperature: {temperature:.1f}°C")
            self.humidity_label.config(text=f"Humidity: {humidity:.1f}%")
        
        # Schedule the next update in 3000 milliseconds (3 seconds)
        self.root.after(3000, self.update_data)  # Update every 3 seconds

    def close(self):
        self.ser.close()

if __name__ == "__main__":
    root = tk.Tk()
    gui = SensorGUI(root)
    
    def on_closing():
        gui.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
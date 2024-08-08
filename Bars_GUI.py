import serial
import time
import struct
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

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
        self.root.geometry("600x600")
        self.root.configure(bg='black')

        # Add Heading
        self.heading_label = ttk.Label(root, text="RS-485 Temperature and Humidity Sensor", font=("Helvetica", 24, 'bold'), foreground='white', background='black')
        self.heading_label.pack(pady=10)

        # Configure the serial connection
        self.ser = serial.Serial(
            port='COM8',       # Replace with your port
            baudrate=9600,     # Replace with your sensor's baudrate
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

        # Create frame for top readings display
        self.top_frame = tk.Frame(root, bg='black')
        self.top_frame.pack(side=tk.TOP, pady=10)

        # Temperature and humidity labels
        self.temperature_display_label = ttk.Label(self.top_frame, text="Temperature: --°C", font=("Helvetica", 20), foreground='white', background='black')
        self.temperature_display_label.pack(pady=5)

        self.humidity_display_label = ttk.Label(self.top_frame, text="Humidity: --%", font=("Helvetica", 20), foreground='white', background='black')
        self.humidity_display_label.pack(pady=5)

        # Create frame for circular gauges and labels
        self.main_frame = tk.Frame(root, bg='black')
        self.main_frame.pack(expand=True, pady=20)

        # Temperature gauge
        self.temp_frame = tk.Frame(self.main_frame, bg='black')
        self.temp_frame.pack(side=tk.LEFT, padx=20)

        self.temp_fig = Figure(figsize=(3, 3), dpi=100)
        self.temp_ax = self.temp_fig.add_subplot(111)
        self.temp_canvas = FigureCanvasTkAgg(self.temp_fig, self.temp_frame)
        self.temp_canvas.get_tk_widget().pack()

        self.temperature_label = ttk.Label(self.temp_frame, text="Temperature", font=("Helvetica", 16, 'bold'), foreground='white', background='black')
        self.temperature_label.pack(pady=5)

        # Humidity gauge
        self.hum_frame = tk.Frame(self.main_frame, bg='black')
        self.hum_frame.pack(side=tk.LEFT, padx=20)

        self.hum_fig = Figure(figsize=(3, 3), dpi=100)
        self.hum_ax = self.hum_fig.add_subplot(111)
        self.hum_canvas = FigureCanvasTkAgg(self.hum_fig, self.hum_frame)
        self.hum_canvas.get_tk_widget().pack()

        self.humidity_label = ttk.Label(self.hum_frame, text="Humidity", font=("Helvetica", 16, 'bold'), foreground='white', background='black')
        self.humidity_label.pack(pady=5)

        # Load icons
        self.temp_icon_image = Image.open("C:/Users/kayan/OneDrive/Desktop/Sensor_Reading/Temperature_icon.png")  # Replace with your temperature icon path
        self.temp_icon_image = self.temp_icon_image.resize((50, 50), Image.LANCZOS)  # Resize icon
        self.temp_icon_photo = ImageTk.PhotoImage(self.temp_icon_image)

        self.hum_icon_image = Image.open("C:/Users/kayan/OneDrive/Desktop/Sensor_Reading/Humidity_icon.png")  # Replace with your humidity icon path
        self.hum_icon_image = self.hum_icon_image.resize((50, 50), Image.LANCZOS)  # Resize icon
        self.hum_icon_photo = ImageTk.PhotoImage(self.hum_icon_image)

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
            self.temperature_display_label.config(text=f"Temperature: {temperature:.1f}°C")
            self.humidity_display_label.config(text=f"Humidity: {humidity:.1f}%")

            # Update temperature gauge
            self.temp_ax.clear()
            self.temp_ax.set_aspect('equal')
            self.temp_ax.set_xlim(-1.5, 1.5)
            self.temp_ax.set_ylim(-1.5, 1.5)
            temp_value = max(0, min(temperature, 100))  # Clamping the value between 0 and 100
            theta = np.linspace(0, 2 * np.pi * temp_value / 100, 100)
            x = np.cos(theta)
            y = np.sin(theta)
            self.temp_ax.plot(x, y, color="red", lw=3)  # Border of the circle

            # Overlay temperature icon in the center
            self.temp_ax.imshow(np.array(self.temp_icon_image), extent=[-0.5, 0.5, -0.5, 0.5], aspect='auto', alpha=0.8)

            self.temp_ax.axis('off')
            self.temp_canvas.draw()

            # Update humidity gauge
            self.hum_ax.clear()
            self.hum_ax.set_aspect('equal')
            self.hum_ax.set_xlim(-1.5, 1.5)
            self.hum_ax.set_ylim(-1.5, 1.5)
            hum_value = max(0, min(humidity, 100))  # Clamping the value between 0 and 100
            theta = np.linspace(0, 2 * np.pi * hum_value / 100, 100)
            x = np.cos(theta)
            y = np.sin(theta)
            self.hum_ax.plot(x, y, color="blue", lw=3)  # Border of the circle

            # Overlay humidity icon in the center
            self.hum_ax.imshow(np.array(self.hum_icon_image), extent=[-0.5, 0.5, -0.5, 0.5], aspect='auto', alpha=0.8)

            self.hum_ax.axis('off')
            self.hum_canvas.draw()
        
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

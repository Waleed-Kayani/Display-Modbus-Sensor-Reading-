import sys
import time
import struct
import serial
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

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

# Configure the serial connection
ser = serial.Serial(
    port='COM8',       # Replace with your port
    baudrate=9600,     # Replace with your sensor's baudrate
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

class SensorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(3000)  # Update every 3 seconds

    def initUI(self):
        self.setWindowTitle('Temperature and Humidity Monitor')
        self.setGeometry(100, 100, 500, 550)

        layout = QVBoxLayout()

        # Create temperature plot
        self.temperaturePlot = pg.PlotWidget()
        self.temperaturePlot.setTitle('Temperature (°C)')
        self.temperaturePlot.setLabel('left', 'Temperature (°C)')
        self.temperaturePlot.setLabel('bottom', 'Time', units='s')
        self.temperaturePlot.showGrid(x=True, y=True)
        self.temperatureLabel = QLabel('Temperature: 0.0°C')
        layout.addWidget(self.temperaturePlot)
        layout.addWidget(self.temperatureLabel)

        # Create humidity plot
        self.humidityPlot = pg.PlotWidget()
        self.humidityPlot.setTitle('Humidity (%)')
        self.humidityPlot.setLabel('left', 'Humidity (%)')
        self.humidityPlot.setLabel('bottom', 'Time', units='s')
        self.humidityPlot.showGrid(x=True, y=True)
        self.humidityLabel = QLabel('Humidity: 0.0%')
        layout.addWidget(self.humidityPlot)
        layout.addWidget(self.humidityLabel)

        self.setLayout(layout)

    def update_data(self):
        device_address = 1  # Replace with your sensor's device address
        function_code = 3   # Function code for reading holding registers
        start_address = 0   # Starting register address
        num_registers = 2   # Number of registers to read

        request_command = create_request_command(device_address, function_code, start_address, num_registers)

        ser.write(request_command)
        time.sleep(1)  # Wait for a response
        response = ser.read(9)  # Read the response (number of bytes depends on your sensor's response format)

        if response and len(response) >= 9:
            # Process the response to extract humidity and temperature values
            raw_temperature = int.from_bytes(response[3:5], byteorder='big')
            humidity = int.from_bytes(response[5:7], byteorder='big') / 10.0
            
            # Adjust the formula based on sensor datasheet
            temperature = (raw_temperature / 1650.0) * 165.0 - 40.0
            
            self.temperatureLabel.setText(f'Temperature: {temperature:.2f}°C')
            self.humidityLabel.setText(f'Humidity: {humidity:.2f}%')

            # Update plots
            self.update_plot(self.temperaturePlot, temperature, 'Temperature (°C)', -40, 125, 'Temperature')
            self.update_plot(self.humidityPlot, humidity, 'Humidity (%)', 0, 100, 'Humidity')

    def update_plot(self, plot, value, title, min_value, max_value, label):
        plot.clear()
        color = 'g' if value < (min_value + max_value) / 2 else 'r'
        bg = pg.BarGraphItem(x=[1], height=[value], width=0.3, brush=color)
        plot.addItem(bg)
        plot.setTitle(title)
        plot.setYRange(min_value, max_value)
        plot.setLabel('left', label)
        plot.setLabel('bottom', 'Time', units='s')
        plot.showGrid(x=True, y=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sensorApp = SensorApp()
    sensorApp.show()
    sys.exit(app.exec_())

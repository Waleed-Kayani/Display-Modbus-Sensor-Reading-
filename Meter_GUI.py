import sys
import time
import struct
import serial
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QDial
from PyQt5.QtCore import QTimer, Qt

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
        self.timer.start(5000)  # Update every 5 seconds

    def initUI(self):
        self.setWindowTitle('Temperature and Humidity Monitor')
        self.setGeometry(100, 100, 500, 550)

        layout = QVBoxLayout()

        # Create temperature gauge
        self.temperatureGauge = QDial()
        self.temperatureGauge.setMinimum(-40)
        self.temperatureGauge.setMaximum(125)
        self.temperatureGauge.setNotchesVisible(True)
        self.temperatureLabel = QLabel('Temperature: 0.0°C', alignment=Qt.AlignCenter)
        layout.addWidget(self.temperatureGauge)
        layout.addWidget(self.temperatureLabel)

        # Create humidity gauge
        self.humidityGauge = QDial()
        self.humidityGauge.setMinimum(0)
        self.humidityGauge.setMaximum(100)
        self.humidityGauge.setNotchesVisible(True)
        self.humidityLabel = QLabel('Humidity: 0.0%', alignment=Qt.AlignCenter)
        layout.addWidget(self.humidityGauge)
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

            # Convert to integer for the dial
            self.temperatureGauge.setValue(int(temperature))
            self.humidityGauge.setValue(int(humidity))

            # Update gauge colors based on value
            self.update_gauge_color(self.temperatureGauge, temperature, 20, 30)
            self.update_gauge_color(self.humidityGauge, humidity, 30, 60)

    def update_gauge_color(self, gauge, value, low, high):
        if value < low:
            gauge.setStyleSheet("QDial { background-color: green; }")
        elif low <= value <= high:
            gauge.setStyleSheet("QDial { background-color: yellow; }")
        else:
            gauge.setStyleSheet("QDial { background-color: red; }")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sensorApp = SensorApp()
    sensorApp.show()
    sys.exit(app.exec_())

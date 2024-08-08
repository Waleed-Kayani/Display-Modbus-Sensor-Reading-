import serial
import time
import struct

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

def read_sensor_data(ser):
    device_address = 1  # Replace with your sensor's device address
    function_code = 3   # Function code for reading holding registers
    start_address = 0   # Starting register address
    num_registers = 2   # Number of registers to read

    request_command = create_request_command(device_address, function_code, start_address, num_registers)
    ser.write(request_command)
    time.sleep(1)  # Wait for a response
    response = ser.read(9)  # Read the response (number of bytes depends on your sensor's response format)

    if response and len(response) >= 9:
        raw_temperature = int.from_bytes(response[3:5], byteorder='big')
        humidity = int.from_bytes(response[5:7], byteorder='big') / 10.0

        # Adjust the formula based on sensor datasheet
        # Example: Assuming a 16-bit raw value maps linearly to -40°C to 125°C
        temperature = (raw_temperature / 1650.0) * 165.0 - 40.0

        return temperature, humidity

    return None, None

def main():
    # Configure the serial connection
    ser = serial.Serial(
        port='COM9',       # Replace with your port
        baudrate=9600,     # Replace with your sensor's baudrate
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    try:
        while True:
            temperature, humidity = read_sensor_data(ser)
            if temperature is not None and humidity is not None:
                print(f"Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%")
            else:
                print("Failed to read data from sensor.")

            time.sleep(3)  # Wait for 3 seconds before the next read
    except KeyboardInterrupt:
        print("Terminating the program.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()

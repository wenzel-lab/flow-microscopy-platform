import spidev
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(24, GPIO.OUT)
# GPIO.output(26, GPIO.LOW)

# Initialize SPI0 as Master
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0 (SPI0 CE0)
spi.max_speed_hz = 5000
spi.mode = 0b00

try:
    while True:
        data_to_send = [0x01, 0x02, 0x03]  # Example data
        print(f"Master sending: {data_to_send}")
        response = spi.xfer2(data_to_send)
        print(f"Master received: {response}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    spi.close()

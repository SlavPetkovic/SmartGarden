# Import Dependencies
import sqlite3
import time
import board
from busio import I2C
import adafruit_bme680
import adafruit_veml7700
import datetime
import RPi.GPIO as GPIO
import atexit

# GPIO setup
rc1 = 23
rc2 = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(rc1, GPIO.OUT)
GPIO.output(rc1, False)
GPIO.setup(rc2, GPIO.OUT)
GPIO.output(rc2, False)


# Clean up GPIO pins when the script exits
def cleanup_gpio():
    GPIO.cleanup()


atexit.register(cleanup_gpio)

# I2C initialization for both sensors
i2c = board.I2C()

# Sensor initialization
veml7700 = adafruit_veml7700.VEML7700(i2c)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
bme680.sea_level_pressure = 1013.25

dbname = 'Neutrino.db'


def store_data(timestamp, temperature, gas, humidity, pressure, altitude, luminosity):
    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(dbname)
        curs = conn.cursor()

        # Insert a row of data
        curs.execute('''INSERT INTO SensorsData 
                     (timestamp, temperature, gas, humidity, pressure, altitude, luminosity) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (timestamp, temperature, gas, humidity, pressure, altitude, luminosity))

        # Commit the changes and close the connection
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def read_sensors():
    timestamp = datetime.datetime.now()
    temperature = round(bme680.temperature, 2)
    gas = round(bme680.gas, 2)
    humidity = round(bme680.humidity, 2)
    pressure = round(bme680.pressure, 2)
    altitude = round(bme680.altitude, 2)
    luminosity = round(veml7700.light, 2)
    return timestamp, temperature, gas, humidity, pressure, altitude, luminosity


def control_led(luminosity):
    if luminosity >= 20:
        print("Lights Off")
        GPIO.output(rc1, False)
    else:
        print("Lights On")
        GPIO.output(rc1, True)


def main_loop():
    while True:
        try:
            data = read_sensors()
            control_led(data[-1])  # Luminosity is the last item in the tuple returned by read_sensors
            store_data(*data)
            print(f"{data[0]}, {data[1]}, {data[2]}, {data[3]}, {data[4]}, {data[5]}, {data[6]}")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            # Handle or log error, then optionally continue or break
            break


if __name__ == "__main__":
    main_loop()

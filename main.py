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
from adafruit_seesaw.seesaw import Seesaw

# GPIO setup

rc1 = 24
rc2 = 23
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
ss = Seesaw(i2c, addr=0x36)

dbname = 'data/Neutrino.db'


def store_data(timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature):
    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(dbname)
        curs = conn.cursor()

        # Insert a row of data
        curs.execute('''INSERT INTO SensorsData 
                     (timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature))

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
    soil_moisture = round(ss.moisture_read(), 2)
    soil_temperature = round(ss.get_temp(), 2)
    return timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture,soil_temperature


def control_led(luminosity):
    if luminosity >= 200:
        print("Lights Is Off")
        GPIO.output(rc1, False)
    else:
        print("Lights Is On")
        GPIO.output(rc1, True)

def control_pump(soil_moisture):
    if soil_moisture <= 400:
        print("Pump Is Off")
        GPIO.output(rc2, False)
    else:
        print("Pump Is On")
        GPIO.output(rc2, True)

def main_loop():
    while True:
        try:
            # Read data
            data = read_sensors()
            # Control lights based on luminosity level
            control_led(data[-3])
            # Control water pump based on soil moisture level
            control_pump(data[-2])
            # Write data into database
            store_data(*data)
            # Print data into console
            print(f"{data[0]}, {data[1]}, {data[2]}, {data[3]}, {data[4]}, {data[5]}, {data[6]}, {data[7]}, {data[8]}")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main_loop()

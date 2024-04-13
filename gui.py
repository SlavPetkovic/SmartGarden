import tkinter
import customtkinter
import board
from busio import I2C
import adafruit_bme680
import adafruit_veml7700
import datetime
import RPi.GPIO as GPIO
import atexit
from adafruit_seesaw.seesaw import Seesaw
import sqlite3
import time

# GPIO setup and cleanup
rc1 = 24
rc2 = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(rc1, GPIO.OUT)
GPIO.output(rc1, False)
GPIO.setup(rc2, GPIO.OUT)
GPIO.output(rc2, False)

def cleanup_gpio():
    GPIO.cleanup()

atexit.register(cleanup_gpio)

# I2C initialization for both sensors
i2c = board.I2C()
veml7700 = adafruit_veml7700.VEML7700(i2c)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
bme680.sea_level_pressure = 1013.25
ss = Seesaw(i2c, addr=0x36)

dbname = 'data/Neutrino.db'

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Garden")
        self.geometry("1200x635")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Sensor reading variables
        self.temperature = tkinter.DoubleVar()
        self.pressure = tkinter.DoubleVar()
        self.humidity = tkinter.DoubleVar()
        self.luminosity = tkinter.DoubleVar()
        self.soil_moisture = tkinter.DoubleVar()
        self.soil_temperature = tkinter.DoubleVar()

        # Setup sensor frames
        self.create_sensor_frame("Temperature (\N{DEGREE CELSIUS})", self.temperature, 0, 0, "#c45134")
        self.create_sensor_frame("Pressure (in Hg)", self.pressure, 0, 1, "#5e9720")
        self.create_sensor_frame("Humidity (%)", self.humidity, 1, 0, "#029cff")
        self.create_sensor_frame("Luminosity (lx)", self.luminosity, 1, 1, "#fed981")
        self.create_sensor_frame("Soil Moisture (%)", self.soil_moisture, 2, 0, "#7f7f7f")
        self.create_sensor_frame("Soil Temperature (\N{DEGREE CELSIUS})", self.soil_temperature, 2, 1, "#e67300")

        self.after(1000, self.update_sensors)

    def create_sensor_frame(self, label_text, var, row, column, color):
        frame = customtkinter.CTkFrame(self)
        frame.grid(row=row, column=column, padx=(10, 10), pady=(10, 10), sticky="nsew")
        label = customtkinter.CTkLabel(master=frame, text=label_text)
        label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        value_label = customtkinter.CTkLabel(master=frame, textvariable=var,
                                             font=customtkinter.CTkFont(size=40, weight="bold"),
                                             text_color=color)
        value_label.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    def update_sensors(self):
        # Read sensor data
        timestamp = datetime.datetime.now()
        temperature = round(bme680.temperature, 2)
        gas = round(bme680.gas, 2)
        humidity = round(bme680.humidity, 2)
        pressure = round(bme680.pressure, 2)
        altitude = round(bme680.altitude, 2)
        luminosity = round(veml7700.light, 2)
        soil_moisture = round(ss.moisture_read(), 2)
        soil_temperature = round(ss.get_temp(), 2)

        # Update the GUI
        self.temperature.set(temperature)
        self.humidity.set(humidity)
        self.pressure.set(pressure)
        self.luminosity.set(luminosity)
        self.soil_moisture.set(soil_moisture)
        self.soil_temperature.set(soil_temperature)

        # Control devices based on sensor values
        self.control_led(luminosity)
        self.control_pump(soil_moisture)

        # Store data in the database
        self.store_data(timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature)

        # Schedule the next sensor update
        self.after(1000, self.update_sensors)

    def control_led(self, luminosity):
        if luminosity >= 100:
            GPIO.output(rc1, True)
        else:
            GPIO.output(rc1, False)

    def control_pump(self, soil_moisture):
        if soil_moisture <= 400:
            GPIO.output(rc2, True)
        else:
            GPIO.output(rc2, False)

    def store_data(self, timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature):
        conn = None
        try:
            conn = sqlite3.connect(dbname)
            curs = conn.cursor()
            curs.execute('''INSERT INTO SensorsData 
                         (timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (timestamp, temperature, gas, humidity, pressure, altitude, luminosity, soil_moisture, soil_temperature))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    app = App()
    app.mainloop()

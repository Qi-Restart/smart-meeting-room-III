import time
import json
import threading
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import board
import adafruit_dht
import RPi.GPIO as GPIO
from smbus2 import SMBus


# ============================================================
# 1. Server configuration
# ============================================================

HOST = "0.0.0.0"
PORT = 8081


# ============================================================
# 2. GPIO configuration
# ============================================================

DHT_PIN = board.D4

TRIG_PIN = 23
ECHO_PIN = 24


# ============================================================
# 3. PCF8591 configuration
# ============================================================

PCF8591_ADDRESS = 0x48
LIGHT_CHANNEL = 0

# Light sensor direction correction
# True means:
# darker environment -> lower percentage
# brighter environment -> higher percentage
LIGHT_REVERSED = True


# ============================================================
# 4. Automatic door configuration
# ============================================================

# Open the 3D door when distance <= 10 cm
DOOR_TRIGGER_CM = 10.0

# Allow another trigger after distance >= 20 cm
DOOR_REARM_CM = 20.0

# Keep the 3D door open for 5 seconds
DOOR_OPEN_SECONDS = 5.0


# ============================================================
# 5. Hardware initialization
# ============================================================

GPIO.setmode(GPIO.BCM)

GPIO.setup(
    TRIG_PIN,
    GPIO.OUT
)

GPIO.setup(
    ECHO_PIN,
    GPIO.IN
)

GPIO.output(
    TRIG_PIN,
    GPIO.LOW
)


dht = adafruit_dht.DHT11(
    DHT_PIN,
    use_pulseio=False
)


try:
    i2c_bus = SMBus(1)

except Exception as e:
    print(
        "PCF8591 init failed:",
        e
    )

    i2c_bus = None


# ============================================================
# 6. Room state
# ============================================================

room_state = {
    "room_id": "R01",

    "temperature": None,

    "humidity": None,

    "light_intensity": None,

    "distance_cm": None,

    "door_status": "closed",

    "air_conditioner_status": "off",

    "dht_status": "offline",

    "light_sensor_status": "offline",

    "ultrasonic_status": "offline",

    "timestamp": None
}


state_lock = threading.Lock()
stop_event = threading.Event()


# ============================================================
# 7. Door internal state
# ============================================================

door_open_until = 0.0
door_armed = True


# ============================================================
# 8. Read PCF8591
# ============================================================

def read_pcf8591(channel):

    if i2c_bus is None:
        return None

    if channel < 0 or channel > 3:
        return None

    try:

        control_byte = (
            0x40
            | channel
        )

        i2c_bus.write_byte(
            PCF8591_ADDRESS,
            control_byte
        )

        # First read is the previous conversion result
        i2c_bus.read_byte(
            PCF8591_ADDRESS
        )

        value = i2c_bus.read_byte(
            PCF8591_ADDRESS
        )

        return value

    except Exception as e:

        print(
            "PCF8591 read failed:",
            e
        )

        return None


# ============================================================
# 9. Read light intensity
# ============================================================

def read_light_percent():

    raw_value = read_pcf8591(
        LIGHT_CHANNEL
    )

    if raw_value is None:
        return None

    percent = (
        raw_value
        / 255.0
        * 100.0
    )

    if LIGHT_REVERSED:

        percent = (
            100.0
            - percent
        )

    percent = max(
        0.0,
        min(
            100.0,
            percent
        )
    )

    return round(
        percent,
        1
    )


# ============================================================
# 10. Read ultrasonic distance
# ============================================================

def read_distance():

    try:

        GPIO.output(
            TRIG_PIN,
            GPIO.LOW
        )

        time.sleep(
            0.000002
        )

        GPIO.output(
            TRIG_PIN,
            GPIO.HIGH
        )

        time.sleep(
            0.00001
        )

        GPIO.output(
            TRIG_PIN,
            GPIO.LOW
        )


        wait_start = (
            time.monotonic()
        )


        # Wait for ECHO to become HIGH
        while (
            GPIO.input(ECHO_PIN)
            == GPIO.LOW
        ):

            if (
                time.monotonic()
                - wait_start
                > 0.03
            ):

                return None


        pulse_start = (
            time.monotonic()
        )


        wait_start = (
            time.monotonic()
        )


        # Wait for ECHO to become LOW
        while (
            GPIO.input(ECHO_PIN)
            == GPIO.HIGH
        ):

            if (
                time.monotonic()
                - wait_start
                > 0.03
            ):

                return None


        pulse_end = (
            time.monotonic()
        )


        pulse_duration = (
            pulse_end
            - pulse_start
        )


        distance = (
            pulse_duration
            * 34300
            / 2
        )


        # Ignore invalid values
        if (
            distance < 2
            or distance > 400
        ):

            return None


        return round(
            distance,
            1
        )

    except Exception as e:

        print(
            "Ultrasonic read failed:",
            e
        )

        return None


# ============================================================
# 11. Read DHT11
# ============================================================

def read_dht():

    try:

        temperature = (
            dht.temperature
        )

        humidity = (
            dht.humidity
        )


        if (
            temperature is None
            or humidity is None
        ):

            return None, None


        return (
            round(
                float(temperature),
                1
            ),

            round(
                float(humidity),
                1
            )
        )


    except RuntimeError:

        # Occasional DHT11 read failure is normal
        return None, None


    except Exception as e:

        print(
            "DHT11 read failed:",
            e
        )

        return None, None


# ============================================================
# 12. Automatic door logic
# ============================================================

def update_door_logic(distance):

    global door_open_until
    global door_armed


    now = time.monotonic()


    if distance is not None:

        # Person enters trigger range
        if (
            door_armed
            and
            distance <= DOOR_TRIGGER_CM
        ):

            print(
                f"Person detected: {distance} cm"
            )

            print(
                "3D door opened for 5 seconds"
            )


            door_open_until = (
                now
                + DOOR_OPEN_SECONDS
            )


            door_armed = False


            # Turn AC state on when door opens
            with state_lock:

                room_state[
                    "air_conditioner_status"
                ] = "on"


        # Rearm after the person moves away
        elif (
            not door_armed
            and
            distance >= DOOR_REARM_CM
        ):

            door_armed = True


    if now < door_open_until:

        door_status = "open"

    else:

        door_status = "closed"


    with state_lock:

        room_state[
            "door_status"
        ] = door_status


# ============================================================
# 13. Sensor loop
# ============================================================

def sensor_loop():

    last_dht_read = 0.0


    while not stop_event.is_set():

        now = time.monotonic()


        # ----------------------------------------------------
        # Ultrasonic sensor
        # ----------------------------------------------------

        distance = read_distance()


        with state_lock:

            if distance is not None:

                room_state[
                    "distance_cm"
                ] = distance

                room_state[
                    "ultrasonic_status"
                ] = "normal"

            else:

                room_state[
                    "distance_cm"
                ] = None

                room_state[
                    "ultrasonic_status"
                ] = "offline"


        update_door_logic(
            distance
        )


        # ----------------------------------------------------
        # Light sensor
        # ----------------------------------------------------

        light = read_light_percent()


        with state_lock:

            if light is not None:

                room_state[
                    "light_intensity"
                ] = light

                room_state[
                    "light_sensor_status"
                ] = "normal"

            else:

                room_state[
                    "light_intensity"
                ] = None

                room_state[
                    "light_sensor_status"
                ] = "offline"


        # ----------------------------------------------------
        # DHT11
        # ----------------------------------------------------

        if (
            now
            - last_dht_read
            >= 2.0
        ):

            last_dht_read = now


            temperature, humidity = (
                read_dht()
            )


            with state_lock:

                if (
                    temperature is not None
                    and
                    humidity is not None
                ):

                    room_state[
                        "temperature"
                    ] = temperature

                    room_state[
                        "humidity"
                    ] = humidity

                    room_state[
                        "dht_status"
                    ] = "normal"

                else:

                    room_state[
                        "dht_status"
                    ] = "offline"


        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        with state_lock:

            room_state[
                "timestamp"
            ] = (
                datetime.now()
                .astimezone()
                .isoformat(
                    timespec="seconds"
                )
            )


        time.sleep(
            0.25
        )


# ============================================================
# 14. HTTP API
# ============================================================

class SensorHandler(
    BaseHTTPRequestHandler
):

    def end_headers(self):

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        super().end_headers()


    def do_GET(self):

        path = urlparse(
            self.path
        ).path


        if (
            path
            == "/api/rooms/R01/state"
        ):

            with state_lock:

                data = (
                    room_state.copy()
                )


            response = json.dumps(
                data,
                ensure_ascii=False
            ).encode(
                "utf-8"
            )


            self.send_response(
                200
            )

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(response))
            )

            self.end_headers()


            self.wfile.write(
                response
            )

            return


        response = json.dumps(
            {
                "error":
                "API not found"
            }
        ).encode(
            "utf-8"
        )


        self.send_response(
            404
        )

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()


        self.wfile.write(
            response
        )


    # Disable default HTTP logs
    def log_message(
        self,
        format,
        *args
    ):

        return


# ============================================================
# 15. Start server
# ============================================================

def main():

    sensor_thread = threading.Thread(
        target=sensor_loop,
        daemon=True
    )

    sensor_thread.start()


    server = ThreadingHTTPServer(
        (
            HOST,
            PORT
        ),
        SensorHandler
    )


    print("")
    print(
        "======================================"
    )

    print(
        "Smart Meeting Room sensor server started"
    )

    print(
        "======================================"
    )

    print("")

    print(
        "Port: 8081"
    )

    print(
        "API: /api/rooms/R01/state"
    )

    print("")

    print(
        "DHT11: GPIO4"
    )

    print(
        "Ultrasonic: GPIO23 / GPIO24"
    )

    print(
        "PCF8591: I2C 0x48 / AIN0"
    )

    print("")

    print(
        "Door trigger: <= 10 cm"
    )

    print(
        "Door rearm: >= 20 cm"
    )

    print(
        "Door open time: 5 seconds"
    )

    print("")

    print(
        "Press Ctrl+C to stop"
    )

    print("")


    try:

        server.serve_forever()


    except KeyboardInterrupt:

        print("")

        print(
            "Stopping..."
        )


    finally:

        stop_event.set()

        server.server_close()


        try:

            dht.exit()

        except Exception:

            pass


        try:

            if i2c_bus is not None:

                i2c_bus.close()

        except Exception:

            pass


        GPIO.cleanup()


        print(
            "Sensor server stopped"
        )


if __name__ == "__main__":

    main()
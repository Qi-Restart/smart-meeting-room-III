#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import random
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import board
import adafruit_dht
import RPi.GPIO as GPIO
from smbus2 import SMBus
import websockets

import cv2
import numpy as np
from picamera2 import Picamera2


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "face_dataset"
TRAINER_DIR = BASE_DIR / "trainer"
LABEL_FILE = TRAINER_DIR / "labels.json"
MODEL_FILE = TRAINER_DIR / "trainer.yml"

DATASET_DIR.mkdir(exist_ok=True)
TRAINER_DIR.mkdir(exist_ok=True)

DHT_PIN = board.D17
PIR_PIN = 27
TRIG_PIN = 23
ECHO_PIN = 24
SERVO_PIN = 18

PCF8591_ADDR = 0x48

SMOKE_THRESHOLD = 100
HIGH_TEMP_THRESHOLD = 28
LOW_LIGHT_THRESHOLD = 90
DOOR_DISTANCE_THRESHOLD = 30

FACE_AUTH_CONFIDENCE = 70
FACE_OPEN_SECONDS = 8

CAMERA_HTTP_PORT = 8081

is_running = True
last_presence_time = time.time()
door_status = "closed"
servo_current_angle = None
face_access_until = 0

last_dht_data = {
    "temperature": 25.0,
    "humidity": 50.0
}

recognition_thread = None
enroll_thread = None
recognition_stop_event = threading.Event()

face_state = {
    "available": True,
    "enrolling": False,
    "recognizing": False,
    "trained": MODEL_FILE.exists(),
    "authorized": False,
    "name": "",
    "confidence": None,
    "message": "Face access standby",
    "enroll_progress": 0,
    "samples_needed": 30,
    "samples_done": 0,
    "last_seen": ""
}


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.output(TRIG_PIN, GPIO.LOW)

GPIO.setup(SERVO_PIN, GPIO.OUT)
servo_pwm = GPIO.PWM(SERVO_PIN, 50)
servo_pwm.start(2.5)


try:
    dht_device = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
    has_dht = True
    print("DHT11 初始化成功")
except Exception as e:
    dht_device = None
    has_dht = False
    print("DHT11 初始化失败，将使用模拟数据：", e)


try:
    bus = SMBus(1)
    has_pcf8591 = True
    print("PCF8591 初始化成功，地址 0x48")
except Exception as e:
    bus = None
    has_pcf8591 = False
    print("PCF8591 初始化失败，将使用模拟数据：", e)


class CameraManager:
    def __init__(self):
        self.picam2 = None
        self.running = False
        self.lock = threading.Lock()
        self.latest_frame = None
        self.latest_jpeg = None
        self.face_box = None
        self.thread = None

    def start(self):
        if self.running:
            return

        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
            self.picam2.configure(config)
            self.picam2.start()
            time.sleep(0.8)

            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            print("摄像头视频流已启动")

        except Exception as e:
            self.running = False
            face_state["available"] = False
            face_state["message"] = f"Camera error: {e}"
            print("摄像头启动失败：", e)

    def _capture_loop(self):
        while self.running:
            try:
                frame = self.picam2.capture_array()

                with self.lock:
                    self.latest_frame = frame.copy()
                    preview = frame.copy()

                    if self.face_box is not None:
                        x, y, w, h = self.face_box
                        cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    text = face_state.get("message", "Camera")
                    cv2.putText(
                        preview,
                        text[:42],
                        (16, 34),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0) if face_state.get("authorized") else (255, 255, 255),
                        2
                    )

                    ok, jpg = cv2.imencode(
                        ".jpg",
                        preview,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    )

                    if ok:
                        self.latest_jpeg = jpg.tobytes()

                time.sleep(0.04)

            except Exception as e:
                print("摄像头采集异常：", e)
                time.sleep(0.2)

    def get_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()

    def get_jpeg(self):
        with self.lock:
            return self.latest_jpeg

    def set_face_box(self, box):
        with self.lock:
            self.face_box = box

    def stop(self):
        self.running = False
        time.sleep(0.2)
        try:
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
        except Exception:
            pass


camera_manager = CameraManager()


class CameraStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request_path = urlparse(self.path).path

        if request_path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <head><meta charset="utf-8"><title>Camera Stream</title></head>
            <body style="margin:0;background:#000;">
            <img src="/video_feed" style="width:100vw;height:100vh;object-fit:contain;">
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
            return

        if request_path != "/video_feed":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        while True:
            try:
                jpg = camera_manager.get_jpeg()

                if jpg is None:
                    time.sleep(0.1)
                    continue

                self.wfile.write(b"--frame\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpg)))
                self.end_headers()
                self.wfile.write(jpg)
                self.wfile.write(b"\r\n")
                time.sleep(0.08)

            except Exception:
                break

    def log_message(self, format, *args):
        return


def start_camera_http_server():
    server = ThreadingHTTPServer(("0.0.0.0", CAMERA_HTTP_PORT), CameraStreamHandler)
    print(f"摄像头视频流地址：http://0.0.0.0:{CAMERA_HTTP_PORT}/video_feed")
    server.serve_forever()


def load_labels():
    if not LABEL_FILE.exists():
        return {}

    try:
        with open(LABEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_labels(labels):
    with open(LABEL_FILE, "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)


def get_next_label_id(labels):
    if not labels:
        return 1
    return max(int(k) for k in labels.keys()) + 1


def sanitize_name(name):
    name = str(name).strip()
    if not name:
        return "unknown"
    safe = re.sub(r"[^\w\u4e00-\u9fa5-]+", "_", name)
    return safe[:30] if safe else "unknown"


def get_face_cascade():
    candidates = [
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/local/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
        str(BASE_DIR / "haarcascade_frontalface_default.xml")
    ]

    if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
        candidates.insert(0, cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    for cascade_path in candidates:
        cascade = cv2.CascadeClassifier(cascade_path)
        if not cascade.empty():
            print("已加载人脸检测模型：", cascade_path)
            return cascade

    raise RuntimeError("无法加载 Haar 人脸检测模型，请执行：sudo apt install -y opencv-data")


def detect_largest_face(gray, cascade):
    gray_eq = cv2.equalizeHist(gray)

    faces = cascade.detectMultiScale(
        gray_eq,
        scaleFactor=1.12,
        minNeighbors=3,
        minSize=(45, 45)
    )

    if len(faces) == 0:
        camera_manager.set_face_box(None)
        return None

    faces = sorted(faces, key=lambda box: box[2] * box[3], reverse=True)
    camera_manager.set_face_box(faces[0])
    return faces[0]


def train_face_model():
    labels = load_labels()

    if not labels:
        raise RuntimeError("没有已录入的人脸标签，无法训练")

    face_images = []
    face_ids = []

    for label_id_str, name in labels.items():
        person_dir = DATASET_DIR / f"person_{label_id_str}"

        if not person_dir.exists():
            continue

        for img_path in person_dir.glob("*.jpg"):
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)

            if img is None:
                continue

            img = cv2.resize(img, (200, 200))
            face_images.append(img)
            face_ids.append(int(label_id_str))

    if len(face_images) < 5:
        raise RuntimeError("有效人脸样本太少，至少需要 5 张")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(face_images, np.array(face_ids))
    recognizer.write(str(MODEL_FILE))

    face_state["trained"] = True
    print(f"人脸模型训练完成，样本数：{len(face_images)}")


def enroll_face_worker(name, samples_needed=30):
    global enroll_thread

    safe_name = sanitize_name(name)
    labels = load_labels()
    label_id = None

    for k, v in labels.items():
        if v == safe_name:
            label_id = int(k)
            break

    if label_id is None:
        label_id = get_next_label_id(labels)
        labels[str(label_id)] = safe_name
        save_labels(labels)

    person_dir = DATASET_DIR / f"person_{label_id}"
    person_dir.mkdir(exist_ok=True)

    face_state["enrolling"] = True
    face_state["recognizing"] = False
    face_state["authorized"] = False
    face_state["name"] = safe_name
    face_state["confidence"] = None
    face_state["message"] = f"Enrolling {safe_name}: look at camera"
    face_state["samples_needed"] = samples_needed
    face_state["samples_done"] = 0
    face_state["enroll_progress"] = 0

    recognition_stop_event.set()

    try:
        cascade = get_face_cascade()
        saved = 0
        start_time = time.time()

        while saved < samples_needed and time.time() - start_time < 90:
            frame = camera_manager.get_frame()

            if frame is None:
                face_state["message"] = "Camera not ready"
                time.sleep(0.2)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            face = detect_largest_face(gray, cascade)

            if face is None:
                face_state["message"] = f"Enrolling {safe_name}: no face detected"
                time.sleep(0.15)
                continue

            x, y, w, h = face
            face_img = gray[y:y + h, x:x + w]
            face_img = cv2.resize(face_img, (200, 200))

            filename = person_dir / f"{int(time.time() * 1000)}_{saved + 1:03d}.jpg"
            cv2.imwrite(str(filename), face_img)

            saved += 1
            face_state["samples_done"] = saved
            face_state["enroll_progress"] = int(saved / samples_needed * 100)
            face_state["message"] = f"Enrolling {safe_name}: {saved}/{samples_needed}"
            print(face_state["message"])
            time.sleep(0.18)

        camera_manager.set_face_box(None)

        if saved >= 5:
            face_state["message"] = "Samples captured, training model"
            train_face_model()
            face_state["message"] = f"{safe_name} enrollment complete"
            face_state["enroll_progress"] = 100
        else:
            face_state["message"] = "Enrollment failed: too few valid samples"

    except Exception as e:
        face_state["message"] = f"Enrollment failed: {e}"
        print("人脸录入异常：", e)

    finally:
        face_state["enrolling"] = False
        enroll_thread = None


def start_enroll_face(name, samples=30):
    global enroll_thread

    if face_state["enrolling"]:
        face_state["message"] = "Enrollment is already running"
        return

    samples = int(samples)
    samples = max(10, min(samples, 80))

    enroll_thread = threading.Thread(
        target=enroll_face_worker,
        args=(name, samples),
        daemon=True
    )
    enroll_thread.start()


def recognition_worker():
    global face_access_until

    face_state["recognizing"] = True
    face_state["authorized"] = False
    face_state["message"] = "Recognition on: look at camera"

    try:
        if not MODEL_FILE.exists():
            face_state["message"] = "No trainer.yml, enroll face first"
            face_state["recognizing"] = False
            return

        labels = load_labels()

        if not labels:
            face_state["message"] = "No labels.json, enroll face first"
            face_state["recognizing"] = False
            return

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(str(MODEL_FILE))
        cascade = get_face_cascade()

        while not recognition_stop_event.is_set():
            frame = camera_manager.get_frame()

            if frame is None:
                face_state["message"] = "Camera not ready"
                time.sleep(0.2)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            face = detect_largest_face(gray, cascade)

            if face is None:
                face_state["authorized"] = False
                face_state["name"] = ""
                face_state["confidence"] = None
                face_state["message"] = "Recognizing: no face detected"
                time.sleep(0.25)
                continue

            x, y, w, h = face
            face_img = gray[y:y + h, x:x + w]
            face_img = cv2.resize(face_img, (200, 200))

            label_id, confidence = recognizer.predict(face_img)
            name = labels.get(str(label_id), "unknown")

            face_state["confidence"] = round(float(confidence), 1)
            face_state["last_seen"] = datetime.now().strftime("%H:%M:%S")

            if confidence <= FACE_AUTH_CONFIDENCE:
                face_state["authorized"] = True
                face_state["name"] = name
                face_state["message"] = f"Access granted: {name}, confidence {confidence:.1f}"
                face_access_until = time.time() + FACE_OPEN_SECONDS
                set_servo_angle(90)
            else:
                face_state["authorized"] = False
                face_state["name"] = name
                face_state["message"] = f"Access denied: {name}, confidence {confidence:.1f}"

            time.sleep(0.3)

        camera_manager.set_face_box(None)

    except Exception as e:
        face_state["message"] = f"Recognition error: {e}"
        print("人脸识别异常：", e)

    finally:
        face_state["recognizing"] = False
        camera_manager.set_face_box(None)


def start_recognition():
    global recognition_thread

    if face_state["enrolling"]:
        face_state["message"] = "Cannot recognize while enrolling"
        return

    if recognition_thread and recognition_thread.is_alive():
        face_state["message"] = "Recognition already running"
        return

    recognition_stop_event.clear()
    recognition_thread = threading.Thread(target=recognition_worker, daemon=True)
    recognition_thread.start()


def stop_recognition():
    recognition_stop_event.set()
    face_state["recognizing"] = False
    face_state["authorized"] = False
    face_state["message"] = "Recognition stopped"
    camera_manager.set_face_box(None)


def read_dht11():
    global last_dht_data

    if not has_dht or dht_device is None:
        last_dht_data["temperature"] += random.uniform(-0.2, 0.2)
        last_dht_data["humidity"] += random.uniform(-0.5, 0.5)
        return {
            "temperature": round(last_dht_data["temperature"], 1),
            "humidity": round(last_dht_data["humidity"], 1)
        }

    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        if temperature is not None and humidity is not None:
            last_dht_data = {
                "temperature": float(temperature),
                "humidity": float(humidity)
            }

        return {
            "temperature": round(last_dht_data["temperature"], 1),
            "humidity": round(last_dht_data["humidity"], 1)
        }

    except Exception:
        return {
            "temperature": round(last_dht_data["temperature"], 1),
            "humidity": round(last_dht_data["humidity"], 1)
        }


def read_pcf8591_channel(channel):
    if not has_pcf8591 or bus is None:
        return None

    try:
        control = 0x40 + channel
        bus.write_byte(PCF8591_ADDR, control)
        bus.read_byte(PCF8591_ADDR)
        value = bus.read_byte(PCF8591_ADDR)
        return value
    except Exception:
        return None


def read_light_sensor():
    value = read_pcf8591_channel(0)

    if value is None:
        return random.randint(80, 180)

    light = 255 - value
    return int(max(0, min(255, light)))


def read_smoke_sensor():
    value = read_pcf8591_channel(1)

    if value is None:
        return random.randint(5, 30)

    return int(max(0, min(255, value)))


def read_pir_sensor():
    try:
        return GPIO.input(PIR_PIN) == GPIO.HIGH
    except Exception:
        return False


def read_distance_sensor():
    try:
        GPIO.output(TRIG_PIN, GPIO.LOW)
        time.sleep(0.000002)

        GPIO.output(TRIG_PIN, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, GPIO.LOW)

        timeout_start = time.time()
        while GPIO.input(ECHO_PIN) == GPIO.LOW:
            if time.time() - timeout_start > 0.05:
                return 400.0
        pulse_start = time.time()

        timeout_start = time.time()
        while GPIO.input(ECHO_PIN) == GPIO.HIGH:
            if time.time() - timeout_start > 0.05:
                return 400.0
        pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 34300 / 2

        if distance < 2 or distance > 400:
            return 400.0

        return round(distance, 1)

    except Exception:
        return 400.0


def set_servo_angle(angle):
    global servo_current_angle

    try:
        angle = int(max(0, min(180, angle)))

        if servo_current_angle == angle:
            return True

        duty_cycle = 2.5 + (angle / 180.0) * 10
        servo_pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.18)
        servo_pwm.ChangeDutyCycle(0)
        servo_current_angle = angle
        return True

    except Exception as e:
        print("舵机控制失败：", e)
        return False


def read_all_sensors():
    global last_presence_time, door_status

    dht = read_dht11()
    light = read_light_sensor()
    smoke = read_smoke_sensor()
    presence = read_pir_sensor()
    distance = read_distance_sensor()

    if presence:
        last_presence_time = time.time()
        no_presence_duration = 0
    else:
        no_presence_duration = int(time.time() - last_presence_time)

    face_door_open = time.time() < face_access_until

    if distance < DOOR_DISTANCE_THRESHOLD or face_door_open:
        door_status = "open"
        set_servo_angle(90)
    else:
        door_status = "closed"
        set_servo_angle(0)

    temperature = dht["temperature"]
    humidity = dht["humidity"]

    ac_on = temperature >= HIGH_TEMP_THRESHOLD
    light_on = light <= LOW_LIGHT_THRESHOLD
    alarm_on = smoke >= SMOKE_THRESHOLD
    energy_saving = no_presence_duration >= 60

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "temperature": temperature,
        "humidity": humidity,
        "light": light,
        "smoke": smoke,
        "presence": presence,
        "no_presence_duration": no_presence_duration,
        "distance": distance,
        "door": door_status,

        "face": dict(face_state),

        "device_status": {
            "ac_on": ac_on,
            "light_on": light_on,
            "alarm_on": alarm_on,
            "energy_saving": energy_saving,
            "door_open": door_status == "open",
            "face_access": face_door_open
        },

        "rooms": {
            "room_a": {
                "name": "标准会议室",
                "ac": ac_on,
                "light": light_on,
                "alarm": alarm_on,
                "door": door_status,
                "face_access": face_door_open,
                "mode": "normal" if not energy_saving else "energy_saving"
            },
            "room_b": {
                "name": "培训会议室",
                "ac": temperature >= 26,
                "light": light <= 130,
                "alarm": alarm_on,
                "door": door_status,
                "face_access": face_door_open,
                "mode": "presentation" if presence else "energy_saving"
            },
            "room_c": {
                "name": "小型洽谈室",
                "ac": temperature >= 30,
                "light": light <= 70,
                "alarm": alarm_on,
                "door": door_status,
                "face_access": face_door_open,
                "mode": "private" if presence else "standby"
            }
        }
    }

    return data


async def handle_client_command(message):
    global face_access_until

    try:
        cmd = json.loads(message)
    except Exception:
        face_state["message"] = "Invalid command"
        return

    cmd_type = cmd.get("type")

    if cmd_type == "enroll_face":
        name = cmd.get("name", "").strip()
        samples = int(cmd.get("samples", 30))

        if not name:
            face_state["message"] = "Enrollment failed: empty name"
            return

        start_enroll_face(name, samples)

    elif cmd_type == "start_face_recognition":
        start_recognition()

    elif cmd_type == "stop_face_recognition":
        stop_recognition()

    elif cmd_type == "open_door":
        face_access_until = time.time() + FACE_OPEN_SECONDS
        set_servo_angle(90)
        face_state["message"] = "Door opened manually"

    else:
        face_state["message"] = f"Unknown command: {cmd_type}"


async def sensor_server(websocket):
    print("浏览器客户端已连接")
    history = []

    async def sender():
        nonlocal history

        while is_running:
            data = read_all_sensors()

            history.append({
                "timestamp": data["timestamp"],
                "temperature": data["temperature"],
                "humidity": data["humidity"],
                "light": data["light"],
                "smoke": data["smoke"]
            })

            if len(history) > 100:
                history = history[-100:]

            send_data = {
                "type": "sensor_update",
                "current": data,
                "history": history
            }

            print(
                f"[{data['timestamp']}] "
                f"T={data['temperature']}℃ "
                f"H={data['humidity']}% "
                f"Light={data['light']} "
                f"Smoke={data['smoke']} "
                f"PIR={data['presence']} "
                f"Distance={data['distance']}cm "
                f"Door={data['door']} "
                f"Face={data['face']['message']}"
            )

            await websocket.send(json.dumps(send_data, ensure_ascii=False))
            await asyncio.sleep(2)

    async def receiver():
        async for message in websocket:
            await handle_client_command(message)

    try:
        await asyncio.gather(sender(), receiver())
    except websockets.exceptions.ConnectionClosed:
        print("浏览器客户端断开连接")
    except Exception as e:
        print("WebSocket 服务异常：", e)


async def main():
    camera_manager.start()

    http_thread = threading.Thread(target=start_camera_http_server, daemon=True)
    http_thread.start()

    print("正在启动 WebSocket 服务器...")
    print("WebSocket 服务地址：ws://0.0.0.0:8775")
    print(f"前端摄像头地址：http://树莓派IP:{CAMERA_HTTP_PORT}/video_feed")
    print("支持命令：enroll_face / start_face_recognition / stop_face_recognition / open_door")

    async with websockets.serve(sensor_server, "0.0.0.0", 8775, ping_interval=None):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("用户停止服务器")

    finally:
        try:
            recognition_stop_event.set()
        except Exception:
            pass

        try:
            camera_manager.stop()
        except Exception:
            pass

        try:
            servo_pwm.stop()
        except Exception:
            pass

        try:
            GPIO.cleanup()
        except Exception:
            pass

        try:
            if dht_device:
                dht_device.exit()
        except Exception:
            pass

        print("服务器已关闭")
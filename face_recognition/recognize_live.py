from pathlib import Path

import argparse
import json
import shutil
import tempfile

import cv2

from preprocess import preprocess_face


# ============================================================
# 命令行参数
# ============================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--once",
    action="store_true",
    help="识别成功后自动退出"
)

args = parser.parse_args()


# ============================================================
# 项目路径
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


MODEL_DIR = (
    PROJECT_ROOT
    / "face_recognition"
    / "models"
)


CASCADE_SOURCE = (
    MODEL_DIR
    / "haarcascade_frontalface_default.xml"
)


LBPH_MODEL_SOURCE = (
    MODEL_DIR
    / "lbph_model.yml"
)


STATE_FILE = (
    PROJECT_ROOT
    / "frontend"
    / "week6_3d"
    / "state.json"
)

# ============================================================
# 识别参数
# ============================================================

RECOGNITION_THRESHOLD = 50.0

CONFIRM_FRAMES = 10

PERSON_LABEL = 1

PERSON_NAME = "person_01"


# ============================================================
# 更新3D会议室状态
# ============================================================

def update_room_state(
    recognized=False
):

    if recognized:

        room_state = {

            "face_status":
                "recognized",

            "person_id":
                PERSON_NAME,

            "door_status":
                "open",

            "light_status":
                "on",

            "air_conditioner_status":
                "on"

        }

    else:

        room_state = {

            "face_status":
                "unknown",

            "person_id":
                None,

            "door_status":
                "closed",

            "light_status":
                "off",

            "air_conditioner_status":
                "off"

        }


    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    temp_state_file = (
        STATE_FILE.with_suffix(
            ".tmp"
        )
    )


    with open(
        temp_state_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(

            room_state,

            file,

            ensure_ascii=False,

            indent=2

        )


    temp_state_file.replace(
        STATE_FILE
    )


# ============================================================
# 检查模型
# ============================================================

if not CASCADE_SOURCE.exists():

    raise FileNotFoundError(

        f"Haar模型不存在："
        f"{CASCADE_SOURCE}"

    )


if not LBPH_MODEL_SOURCE.exists():

    raise FileNotFoundError(

        f"LBPH模型不存在："
        f"{LBPH_MODEL_SOURCE}"

    )


# ============================================================
# Windows 中文路径兼容
# ============================================================

TEMP_MODEL_DIR = (

    Path(
        tempfile.gettempdir()
    )

    / "smart_meeting_room_models"

)


TEMP_MODEL_DIR.mkdir(

    parents=True,

    exist_ok=True

)


TEMP_CASCADE = (

    TEMP_MODEL_DIR

    / "haarcascade_frontalface_default.xml"

)


TEMP_LBPH_MODEL = (

    TEMP_MODEL_DIR

    / "lbph_model_live.yml"

)


shutil.copyfile(

    CASCADE_SOURCE,

    TEMP_CASCADE

)


shutil.copyfile(

    LBPH_MODEL_SOURCE,

    TEMP_LBPH_MODEL

)


# ============================================================
# Haar
# ============================================================

face_detector = (

    cv2.CascadeClassifier(
        str(
            TEMP_CASCADE
        )
    )

)


if face_detector.empty():

    raise RuntimeError(
        "Haar人脸检测器加载失败。"
    )


# ============================================================
# LBPH
# ============================================================

if not hasattr(
    cv2,
    "face"
):

    raise RuntimeError(

        "当前OpenCV不包含cv2.face，"
        "请安装opencv-contrib-python。"

    )


recognizer = (

    cv2.face
    .LBPHFaceRecognizer_create()

)


recognizer.read(

    str(
        TEMP_LBPH_MODEL
    )

)


# ============================================================
# 摄像头
# ============================================================

camera = (
    cv2.VideoCapture(
        0
    )
)


if not camera.isOpened():

    raise RuntimeError(
        "无法打开电脑摄像头。"
    )


camera.set(

    cv2.CAP_PROP_FRAME_WIDTH,

    1280

)


camera.set(

    cv2.CAP_PROP_FRAME_HEIGHT,

    720

)


# ============================================================
# 状态变量
# ============================================================

success_frames = 0

authorized = False

state_sent = False

recognition_succeeded = False


# 启动识别时先恢复会议室
update_room_state(
    recognized=False
)


print(
    "=" * 60
)

print(
    "智能会议室实时人脸识别"
)

print(
    "=" * 60
)

print(
    f"当前注册对象："
    f"{PERSON_NAME}"
)

print(
    f"临时识别阈值："
    f"{RECOGNITION_THRESHOLD}"
)

print(
    f"连续确认帧数："
    f"{CONFIRM_FRAMES}"
)

print()

print(
    "按 Q 可手动退出"
)

print(
    "=" * 60
)


# ============================================================
# 主循环
# ============================================================

while True:

    ok, frame = (
        camera.read()
    )


    if not ok:

        print(
            "摄像头读取失败。"
        )

        break


    display_frame = (
        frame.copy()
    )


    gray = (
        cv2.cvtColor(

            frame,

            cv2.COLOR_BGR2GRAY

        )
    )


    faces = (

        face_detector.detectMultiScale(

            gray,

            scaleFactor=1.1,

            minNeighbors=5,

            minSize=(
                100,
                100
            )

        )

    )


    frame_recognized = False


    # ========================================================
    # 检测到人脸
    # ========================================================

    if len(faces) > 0:

        x, y, w, h = max(

            faces,

            key=lambda item:
                item[2]
                *
                item[3]

        )


        face_image = (

            frame[

                y:y + h,

                x:x + w

            ]

        )


        processed = (

            preprocess_face(
                face_image
            )

        )


        label, distance = (

            recognizer.predict(
                processed
            )

        )


        # ====================================================
        # 阈值判断
        # ====================================================

        if (

            label
            ==
            PERSON_LABEL

            and

            distance
            <=
            RECOGNITION_THRESHOLD

        ):

            frame_recognized = (
                True
            )


            success_frames += 1


        else:

            success_frames = 0

            authorized = False


        # ====================================================
        # 连续多帧确认
        # ====================================================

        if (

            success_frames
            >=
            CONFIRM_FRAMES

        ):

            if not authorized:

                print()

                print(
                    "=" * 60
                )

                print(
                    "人脸识别成功"
                )

                print(
                    f"身份："
                    f"{PERSON_NAME}"
                )

                print(
                    f"当前LBPH距离："
                    f"{distance:.2f}"
                )

                print(
                    "已发送会议室联动指令"
                )

                print(
                    "=" * 60
                )


            authorized = True


            if not state_sent:

                update_room_state(
                    recognized=True
                )


                state_sent = True

                recognition_succeeded = (
                    True
                )


                if args.once:

                    print()

                    print(
                        "识别完成，"
                        "自动结束摄像头识别。"
                    )

                    break


        # ====================================================
        # 显示框
        # ====================================================

        if authorized:

            box_color = (
                0,
                255,
                0
            )


            status_text = (

                f"AUTHORIZED  "
                f"{PERSON_NAME}  "
                f"{distance:.2f}"

            )


        elif frame_recognized:

            box_color = (
                0,
                255,
                255
            )


            status_text = (

                f"VERIFYING "
                f"{success_frames}/"
                f"{CONFIRM_FRAMES} "
                f"{distance:.2f}"

            )


        else:

            box_color = (
                0,
                0,
                255
            )


            status_text = (

                f"UNKNOWN "
                f"{distance:.2f}"

            )


        cv2.rectangle(

            display_frame,

            (
                x,
                y
            ),

            (
                x + w,
                y + h
            ),

            box_color,

            3

        )


        cv2.putText(

            display_frame,

            status_text,

            (
                x,
                max(
                    y - 15,
                    30
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            box_color,

            2

        )


    # ========================================================
    # 没检测到人脸
    # ========================================================

    else:

        success_frames = 0

        authorized = False


        cv2.putText(

            display_frame,

            "NO FACE",

            (
                30,
                50
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (
                0,
                0,
                255
            ),

            2

        )


    # ========================================================
    # 左上角参数
    # ========================================================

    cv2.putText(

        display_frame,

        f"Threshold: "
        f"{RECOGNITION_THRESHOLD}",

        (
            30,
            90
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (
            255,
            255,
            255
        ),

        2

    )


    cv2.putText(

        display_frame,

        f"Confirm: "
        f"{success_frames}/"
        f"{CONFIRM_FRAMES}",

        (
            30,
            125
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (
            255,
            255,
            255
        ),

        2

    )


    # ========================================================
    # 显示窗口
    # ========================================================

    cv2.imshow(

        "Smart Meeting Room - Face Recognition",

        display_frame

    )


    key = (
        cv2.waitKey(1)
        &
        0xFF
    )


    if key == ord("q"):

        print()

        print(
            "用户结束实时识别。"
        )

        break


# ============================================================
# 清理
# ============================================================

camera.release()

cv2.destroyAllWindows()


# 只有识别没有成功时才恢复关闭状态。
# 如果识别成功，则保持门开、灯开、空调开。
if not recognition_succeeded:

    update_room_state(
        recognized=False
    )


    print(
        "会议室状态已重置。"
    )


print(
    "实时人脸识别程序已退出。"
)
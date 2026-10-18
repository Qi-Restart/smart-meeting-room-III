from pathlib import Path
import cv2


# ============================================================
# 基本配置
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PERSON_ID = "person_01"

SAVE_DIR = (
    PROJECT_ROOT
    / "local_face_data"
    / PERSON_ID
)

SAVE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

TARGET_COUNT = 20


# ============================================================
# Haar 人脸检测器
# ============================================================

import tempfile
import shutil

cascade_source = (
    PROJECT_ROOT
    / "face_recognition"
    / "models"
    / "haarcascade_frontalface_default.xml"
)

# OpenCV 在 Windows 下可能无法正确读取包含中文字符的路径，
# 因此将模型临时复制到系统临时目录后再加载。
temp_model_dir = Path(tempfile.gettempdir()) / "smart_meeting_room_models"

temp_model_dir.mkdir(
    parents=True,
    exist_ok=True
)

cascade_path = (
    temp_model_dir
    / "haarcascade_frontalface_default.xml"
)

if not cascade_path.exists():
    shutil.copyfile(
        cascade_source,
        cascade_path
    )

face_detector = cv2.CascadeClassifier(
    str(cascade_path)
)

if face_detector.empty():
    raise RuntimeError(
        f"Haar 人脸检测器加载失败：{cascade_path}"
    )


# ============================================================
# 统计已有样本
# ============================================================

existing_files = list(
    SAVE_DIR.glob("*.jpg")
)

saved_count = len(existing_files)

print("=" * 60)
print("智能会议室人脸样本采集")
print("=" * 60)

print(f"当前对象：{PERSON_ID}")
print(f"保存位置：{SAVE_DIR}")
print(f"已有样本：{saved_count}")
print(f"目标样本：{TARGET_COUNT}")

print()
print("操作说明：")
print("S：保存当前检测到的人脸")
print("Q：退出采集")
print("=" * 60)


# ============================================================
# 打开电脑摄像头
# ============================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError(
        "无法打开电脑摄像头。"
    )


# 可以根据电脑摄像头情况调整
camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)


# ============================================================
# 保存图片
# ============================================================

def save_image_unicode(
    path,
    image
):
    """
    支持包含中文路径的 Windows 环境保存 JPG。
    """

    success, encoded = cv2.imencode(
        ".jpg",
        image
    )

    if not success:
        return False

    encoded.tofile(
        str(path)
    )

    return True


# ============================================================
# 主循环
# ============================================================

while True:

    success, frame = camera.read()

    if not success:
        print("摄像头读取失败。")
        break

    display_frame = frame.copy()

    # --------------------------------------------------------
    # 灰度化用于 Haar 检测
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    selected_face = None

    # --------------------------------------------------------
    # 如果检测到多张脸，只选择面积最大的一张
    # --------------------------------------------------------

    if len(faces) > 0:

        largest_face = max(
            faces,
            key=lambda item: item[2] * item[3]
        )

        x, y, w, h = largest_face

        selected_face = frame[
            y:y + h,
            x:x + w
        ]

        cv2.rectangle(
            display_frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            display_frame,
            "Face detected",
            (x, max(y - 10, 30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    else:

        cv2.putText(
            display_frame,
            "No face detected",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


    # --------------------------------------------------------
    # 显示当前采集数量
    # --------------------------------------------------------

    cv2.putText(
        display_frame,
        f"Samples: {saved_count}/{TARGET_COUNT}",
        (30, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        display_frame,
        "Press S to save, Q to quit",
        (30, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # --------------------------------------------------------
    # 显示摄像头画面
    # --------------------------------------------------------

    cv2.imshow(
        "Face Collection",
        display_frame
    )


    # --------------------------------------------------------
    # 键盘操作
    # --------------------------------------------------------

    key = cv2.waitKey(1) & 0xFF


    # Q：退出
    if key == ord("q"):

        print()
        print("用户结束采集。")
        break


    # S：保存
    if key == ord("s"):

        if selected_face is None:

            print(
                "未检测到有效人脸，本次未保存。"
            )

            continue

        saved_count += 1

        filename = (
            f"{saved_count:03d}.jpg"
        )

        save_path = (
            SAVE_DIR
            / filename
        )

        result = save_image_unicode(
            save_path,
            selected_face
        )

        if result:

            print(
                f"已保存：{filename}"
            )

        else:

            saved_count -= 1

            print(
                "图片保存失败。"
            )


        # 达到目标数量后自动结束
        if saved_count >= TARGET_COUNT:

            print()
            print(
                f"已达到目标数量："
                f"{TARGET_COUNT} 张"
            )

            break


# ============================================================
# 清理资源
# ============================================================

camera.release()

cv2.destroyAllWindows()

print()
print("=" * 60)
print("人脸样本采集结束")
print(f"最终样本数量：{saved_count}")
print(f"保存目录：{SAVE_DIR}")
print("=" * 60)
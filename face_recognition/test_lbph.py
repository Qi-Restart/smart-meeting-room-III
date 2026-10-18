from pathlib import Path
import shutil
import tempfile

import cv2
import numpy as np

from preprocess import preprocess_face


# ============================================================
# 路径配置
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = (
    PROJECT_ROOT
    / "local_face_data"
    / "person_01"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "face_recognition"
    / "models"
    / "lbph_model.yml"
)


# ============================================================
# 中文路径图片读取
# ============================================================

def read_image_unicode(path):
    data = np.fromfile(
        str(path),
        dtype=np.uint8
    )

    return cv2.imdecode(
        data,
        cv2.IMREAD_COLOR
    )


# ============================================================
# 加载 LBPH 模型
# 中文路径兼容处理
# ============================================================

temp_dir = (
    Path(tempfile.gettempdir())
    / "smart_meeting_room_models"
)

temp_dir.mkdir(
    parents=True,
    exist_ok=True
)

temp_model = (
    temp_dir
    / "lbph_model_test.yml"
)

shutil.copyfile(
    MODEL_FILE,
    temp_model
)

recognizer = (
    cv2.face
    .LBPHFaceRecognizer_create()
)

recognizer.read(
    str(temp_model)
)


# ============================================================
# 测试 016 ~ 020
# ============================================================

print("=" * 60)
print("LBPH 独立测试")
print("=" * 60)

distances = []

for index in range(16, 21):

    image_path = (
        DATA_DIR
        / f"{index:03d}.jpg"
    )

    image = read_image_unicode(
        image_path
    )

    if image is None:
        print(
            f"{image_path.name}：读取失败"
        )
        continue

    processed = preprocess_face(
        image
    )

    label, distance = recognizer.predict(
        processed
    )

    distances.append(
        distance
    )

    print(
        f"{image_path.name} "
        f"→ label={label}, "
        f"LBPH距离={distance:.2f}"
    )


# ============================================================
# 统计
# ============================================================

if distances:

    print()
    print("-" * 60)

    print(
        f"平均距离："
        f"{np.mean(distances):.2f}"
    )

    print(
        f"最小距离："
        f"{np.min(distances):.2f}"
    )

    print(
        f"最大距离："
        f"{np.max(distances):.2f}"
    )

print("=" * 60)

print()
print(
    "说明：LBPH 距离越小，"
    "通常表示与训练对象越相似。"
)

print(
    "当前程序只观察距离，"
    "暂不确定最终识别阈值。"
)
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

MODEL_DIR = (
    PROJECT_ROOT
    / "face_recognition"
    / "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MODEL_FILE = (
    MODEL_DIR
    / "lbph_model.yml"
)


# ============================================================
# 训练配置
# ============================================================

PERSON_LABEL = 1

# 001 ~ 015 用于训练
TRAIN_START = 1
TRAIN_END = 15


# ============================================================
# 支持 Windows 中文路径读取图片
# ============================================================

def read_image_unicode(path):
    data = np.fromfile(
        str(path),
        dtype=np.uint8
    )

    image = cv2.imdecode(
        data,
        cv2.IMREAD_COLOR
    )

    return image


# ============================================================
# 加载训练样本
# ============================================================

faces = []
labels = []

print("=" * 60)
print("智能会议室 LBPH 人脸模型训练")
print("=" * 60)

for index in range(TRAIN_START, TRAIN_END + 1):

    image_path = (
        DATA_DIR
        / f"{index:03d}.jpg"
    )

    if not image_path.exists():
        print(
            f"样本不存在，跳过：{image_path.name}"
        )
        continue

    image = read_image_unicode(
        image_path
    )

    if image is None:
        print(
            f"样本读取失败，跳过：{image_path.name}"
        )
        continue

    # 使用第5周自己完成的预处理流程
    processed = preprocess_face(
        image
    )

    faces.append(
        processed
    )

    labels.append(
        PERSON_LABEL
    )

    print(
        f"已加载：{image_path.name}"
    )


# ============================================================
# 数据检查
# ============================================================

if len(faces) == 0:
    raise RuntimeError(
        "没有可用于训练的人脸样本。"
    )


# ============================================================
# 创建 LBPH 识别器
# ============================================================

if not hasattr(cv2, "face"):
    raise RuntimeError(
        "当前 OpenCV 缺少 cv2.face，"
        "请确认安装的是 opencv-contrib-python。"
    )

recognizer = (
    cv2.face
    .LBPHFaceRecognizer_create()
)


# ============================================================
# 训练模型
# ============================================================

recognizer.train(
    faces,
    np.array(
        labels,
        dtype=np.int32
    )
)


# ============================================================
# 保存模型
#
# OpenCV 在 Windows 下可能无法直接处理包含中文字符的路径，
# 所以先写入系统临时英文路径，再复制回项目。
# ============================================================

temp_model_dir = (
    Path(tempfile.gettempdir())
    / "smart_meeting_room_models"
)

temp_model_dir.mkdir(
    parents=True,
    exist_ok=True
)

temp_model_file = (
    temp_model_dir
    / "lbph_model.yml"
)

recognizer.write(
    str(temp_model_file)
)

shutil.copyfile(
    temp_model_file,
    MODEL_FILE
)


# ============================================================
# 输出结果
# ============================================================

print()
print("=" * 60)
print("LBPH 模型训练完成")
print("=" * 60)

print(
    f"训练对象：person_01"
)

print(
    f"训练样本数量：{len(faces)}"
)

print(
    f"训练样本范围："
    f"{TRAIN_START:03d}.jpg "
    f"~ {TRAIN_END:03d}.jpg"
)

print(
    f"身份标签：{PERSON_LABEL}"
)

print(
    f"模型保存位置：{MODEL_FILE}"
)

print()
print(
    "016.jpg ~ 020.jpg 未参与训练，"
    "后续用于独立识别测试。"
)

print("=" * 60)
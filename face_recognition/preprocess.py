from pathlib import Path

import cv2


# ============================================================
# 人脸预处理参数
# ============================================================

FACE_SIZE = (200, 200)

CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)

GAUSSIAN_KERNEL = (3, 3)
GAUSSIAN_SIGMA_X = 0


# ============================================================
# 人脸预处理函数
# ============================================================

def preprocess_face(image):
    """
    对输入人脸图像进行统一预处理。

    处理流程：
    1. 灰度化
    2. 尺寸统一为 200×200
    3. CLAHE 局部光照增强
    4. 高斯滤波去噪

    参数：
        image: OpenCV 读取的 BGR 彩色图像，
               也可以是已经转换好的灰度图像。

    返回：
        processed: 最终预处理后的灰度人脸图像
    """

    if image is None:
        raise ValueError("输入图像为空，无法进行预处理。")

    # --------------------------------------------------------
    # 1. 灰度化
    # --------------------------------------------------------

    if len(image.shape) == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = image.copy()

    # --------------------------------------------------------
    # 2. 尺寸统一
    # --------------------------------------------------------

    resized = cv2.resize(
        gray,
        FACE_SIZE
    )

    # --------------------------------------------------------
    # 3. CLAHE 局部光照增强
    # --------------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=CLAHE_TILE_GRID_SIZE
    )

    enhanced = clahe.apply(resized)

    # --------------------------------------------------------
    # 4. 高斯去噪
    # --------------------------------------------------------

    processed = cv2.GaussianBlur(
        enhanced,
        GAUSSIAN_KERNEL,
        GAUSSIAN_SIGMA_X
    )

    return processed


# ============================================================
# 返回各阶段结果
# 用于后续生成“处理前后对比图”
# ============================================================

def preprocess_face_with_steps(image):
    """
    执行人脸预处理，并返回每一步中间结果。

    后续生成预处理对比图时使用。
    """

    if image is None:
        raise ValueError("输入图像为空，无法进行预处理。")

    # 原始图像
    original = image.copy()

    # 灰度化
    if len(image.shape) == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = image.copy()

    # 尺寸统一
    resized = cv2.resize(
        gray,
        FACE_SIZE
    )

    # CLAHE 光照增强
    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=CLAHE_TILE_GRID_SIZE
    )

    enhanced = clahe.apply(resized)

    # 高斯滤波
    processed = cv2.GaussianBlur(
        enhanced,
        GAUSSIAN_KERNEL,
        GAUSSIAN_SIGMA_X
    )

    return {
        "original": original,
        "gray": gray,
        "resized": resized,
        "enhanced": enhanced,
        "processed": processed
    }


# ============================================================
# 模块信息
# ============================================================

def print_preprocess_config():
    """
    打印当前预处理参数。
    """

    print("=" * 50)
    print("智能会议室人脸图像预处理模块")
    print("=" * 50)

    print(f"统一尺寸：{FACE_SIZE[0]} × {FACE_SIZE[1]}")

    print(
        f"CLAHE：clipLimit={CLAHE_CLIP_LIMIT}, "
        f"tileGridSize={CLAHE_TILE_GRID_SIZE}"
    )

    print(
        f"高斯滤波：kernel={GAUSSIAN_KERNEL}, "
        f"sigmaX={GAUSSIAN_SIGMA_X}"
    )

    print("=" * 50)


# ============================================================
# 单独运行本文件时
# ============================================================

if __name__ == "__main__":
    print_preprocess_config()

    print()
    print("preprocess.py 已正常加载。")
    print("下一步可使用授权人脸样本进行预处理测试。")
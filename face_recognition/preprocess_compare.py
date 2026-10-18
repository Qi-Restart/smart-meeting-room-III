import os
import cv2
import numpy as np

# =========================
# 路径配置
# =========================
input_path = "local_face_data/person_01/001.jpg"
output_dir = "results/face"
output_path = os.path.join(output_dir, "preprocess_comparison.png")

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# =========================
# 读取原图
# =========================
img = cv2.imread(input_path)

if img is None:
    raise FileNotFoundError(f"无法读取图片：{input_path}")

# =========================
# 预处理流程
# 1. 转灰度
# 2. 统一尺寸 200x200
# 3. CLAHE增强
# 4. 高斯滤波
# =========================
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray_resized = cv2.resize(gray, (200, 200))

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray_resized)

processed = cv2.GaussianBlur(enhanced, (3, 3), 0)

# =========================
# 为了做左右对比：
# 原图也统一成 200x200
# 并转成三通道，方便拼接和写字
# =========================
original_resized = cv2.resize(img, (200, 200))
processed_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

# 在图片上加标题
cv2.putText(original_resized, "Original", (45, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

cv2.putText(processed_bgr, "Processed", (35, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

# 左右拼接
comparison = cv2.hconcat([original_resized, processed_bgr])

# 保存结果
cv2.imwrite(output_path, comparison)

print("预处理前后对比图已生成：")
print(output_path)
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# =========================
# 路径设置
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "clean_sensor_data.csv"
RESULT_DIR = PROJECT_ROOT / "results"

RESULT_DIR.mkdir(exist_ok=True)


# =========================
# 中文字体设置
# =========================
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 读取数据
# =========================
df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["occupancy"] = pd.to_numeric(df["occupancy"], errors="coerce")

# 数据分析时只使用 occupancy 有效的数据
valid_df = df.dropna(subset=["timestamp", "occupancy"]).copy()

valid_df["hour"] = valid_df["timestamp"].dt.hour


print("=" * 60)
print("第4周数据分析")
print("=" * 60)
print(f"读取数据：{len(df)} 条")
print(f"可用于占用分析的数据：{len(valid_df)} 条")


# ============================================================
# 图1：一天中各时段会议室占用率
# 口径：该小时 occupancy=1 的采样数 / 该小时有效采样总数
# ============================================================
hourly_occupancy = (
    valid_df.groupby("hour")["occupancy"]
    .mean()
    .mul(100)
)

plt.figure(figsize=(10, 6))
hourly_occupancy.plot(kind="bar")

plt.title("各时段会议室占用率（有人采样数 / 有效采样总数）")
plt.xlabel("小时")
plt.ylabel("占用率（%）")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    RESULT_DIR / "01_hourly_occupancy.png",
    dpi=200
)
plt.close()

busiest_hour = hourly_occupancy.idxmax()
busiest_rate = hourly_occupancy.max()

print()
print("【图1】各时段会议室占用率")
print(
    f"最繁忙时段：{busiest_hour}:00-{busiest_hour + 1}:00，"
    f"占用率为 {busiest_rate:.2f}%"
)


# ============================================================
# 图2：不同会议室平均利用率
# 口径：各会议室 occupancy=1 的采样数 / 该会议室有效采样总数
# ============================================================
room_utilization = (
    valid_df.groupby("room_id")["occupancy"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 6))
room_utilization.plot(kind="bar")

plt.title("不同会议室平均利用率（有人采样数 / 有效采样总数）")
plt.xlabel("会议室")
plt.ylabel("利用率（%）")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    RESULT_DIR / "02_room_utilization.png",
    dpi=200
)
plt.close()

top_room = room_utilization.idxmax()
top_room_rate = room_utilization.max()

print()
print("【图2】不同会议室平均利用率")
print(
    f"利用率最高的会议室：{top_room}，"
    f"平均利用率为 {top_room_rate:.2f}%"
)


# ============================================================
# 图3：有人/无人状态下设备开启比例
# 灯光、投影：状态为 on 视为开启
# 空调：on 或 auto 视为运行
# ============================================================
device_df = valid_df.copy()

device_df["light_active"] = (
    device_df["light_status"].astype(str).str.lower() == "on"
)

device_df["projector_active"] = (
    device_df["projector_status"].astype(str).str.lower() == "on"
)

device_df["air_conditioner_active"] = (
    device_df["air_conditioner_status"]
    .astype(str)
    .str.lower()
    .isin(["on", "auto"])
)

device_usage = (
    device_df.groupby("occupancy")[
        [
            "light_active",
            "projector_active",
            "air_conditioner_active",
        ]
    ]
    .mean()
    .mul(100)
)

device_usage.index = [
    "无人" if value == 0 else "有人"
    for value in device_usage.index
]

device_usage.columns = [
    "灯光",
    "投影仪",
    "空调",
]

plt.figure(figsize=(9, 6))
device_usage.plot(kind="bar")

plt.title("有人/无人状态下设备开启比例（设备开启采样数 / 对应状态有效采样总数）")
plt.xlabel("会议室人员状态")
plt.ylabel("设备开启比例（%）")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    RESULT_DIR / "03_device_usage.png",
    dpi=200
)
plt.close()

print()
print("【图3】有人/无人状态下设备开启比例（设备开启采样数 / 对应状态有效采样总数）")

for state in device_usage.index:
    print(
        f"{state}时："
        f"灯光 {device_usage.loc[state, '灯光']:.2f}%；"
        f"投影仪 {device_usage.loc[state, '投影仪']:.2f}%；"
        f"空调 {device_usage.loc[state, '空调']:.2f}%"
    )


print()
print("=" * 60)
print("数据分析完成")
print("图表输出目录：")
print(RESULT_DIR)
print("=" * 60)
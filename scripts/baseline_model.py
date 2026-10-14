from pathlib import Path
import pandas as pd

# =========================
# 路径设置
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_sensor_data.csv"
)

RESULT_DIR = PROJECT_ROOT / "results"
RESULT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = RESULT_DIR / "baseline_predictions.csv"


# =========================
# 读取数据
# =========================
df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

df["occupancy"] = pd.to_numeric(
    df["occupancy"],
    errors="coerce"
)

# 去掉时间或 occupancy 缺失的数据
df = df.dropna(
    subset=["timestamp", "occupancy"]
).copy()

df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour


# =========================
# 按时间切分数据
# =========================
dates = sorted(df["date"].unique())

test_date = dates[-1]

train_df = df[df["date"] < test_date].copy()
test_df = df[df["date"] == test_date].copy()


print("=" * 60)
print("第4周占用状态基线预测")
print("=" * 60)

print(
    f"历史数据：{train_df['date'].min()} "
    f"至 {train_df['date'].max()}"
)

print(f"测试数据：{test_date}")
print(f"历史样本量：{len(train_df)}")
print(f"测试样本量：{len(test_df)}")


# =========================
# 计算历史同会议室、同小时占用率
# =========================
history_rate = (
    train_df
    .groupby(["room_id", "hour"])["occupancy"]
    .mean()
    .reset_index()
)

history_rate = history_rate.rename(
    columns={
        "occupancy": "historical_occupancy_rate"
    }
)


# =========================
# 合并测试数据
# =========================
result = test_df.merge(
    history_rate,
    on=["room_id", "hour"],
    how="left"
)


# 如果某时段没有历史记录，用总体占用率补充
global_rate = train_df["occupancy"].mean()

result["historical_occupancy_rate"] = (
    result["historical_occupancy_rate"]
    .fillna(global_rate)
)


# =========================
# 基线规则
# 历史占用率 > 0.5 → 预测有人
# =========================
result["prediction"] = (
    result["historical_occupancy_rate"] > 0.5
).astype(int)


# =========================
# 计算准确率
# =========================
result["correct"] = (
    result["prediction"] == result["occupancy"]
)

accuracy = result["correct"].mean()


actual_occupied = result[
    result["occupancy"] == 1
]

actual_empty = result[
    result["occupancy"] == 0
]

occupied_correct = (
    actual_occupied["prediction"] == 1
).sum()

empty_correct = (
    actual_empty["prediction"] == 0
).sum()


# =========================
# 输出结果
# =========================
print()
print("基线规则：")
print(
    "历史同一会议室、同一小时平均占用率 > 0.5，"
    "预测为有人；否则预测为无人。"
)

print()
print(f"测试样本量：{len(result)}")
print(f"总体准确率：{accuracy * 100:.2f}%")

print(
    f"实际有人样本：{len(actual_occupied)}，"
    f"正确预测：{occupied_correct}"
)

print(
    f"实际无人样本：{len(actual_empty)}，"
    f"正确预测：{empty_correct}"
)


# =========================
# 保存预测结果
# =========================
result[
    [
        "timestamp",
        "room_id",
        "hour",
        "occupancy",
        "historical_occupancy_rate",
        "prediction",
        "correct",
    ]
].to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


print()
print("预测明细已保存：")
print(OUTPUT_FILE)

print("=" * 60)
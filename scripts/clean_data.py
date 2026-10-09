from pathlib import Path

import pandas as pd


# =========================
# 1. 文件路径
# =========================

# 当前文件：
# smart_meeting_room/scripts/clean_data.py

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "会议室教学测试原始数据.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clean_sensor_data.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "docs"
    / "data_quality_report.md"
)


# =========================
# 2. 读取原始数据
# =========================

df = pd.read_csv(RAW_FILE, encoding="utf-8-sig")

before_count = len(df)

print("原始数据条数：", before_count)


# =========================
# 3. 统一字段名称
# =========================

df.columns = [
    column.strip().lower()
    for column in df.columns
]


# =========================
# 4. 统一时间格式
# =========================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce",
    format="mixed"
)

invalid_time_count = df["timestamp"].isna().sum()


# =========================
# 5. 统一会议室编号
# =========================

room_mapping = {
    "room-1": "R01",
    "room_1": "R01",
    "r01": "R01",

    "room-2": "R02",
    "room_2": "R02",
    "r02": "R02",

    "room-3": "R03",
    "room_3": "R03",
    "r03": "R03",
}

df["room_id"] = (
    df["room_id"]
    .astype(str)
    .str.strip()
    .str.lower()
    .replace(room_mapping)
)

# 对已经类似 R01 的值统一大写
df["room_id"] = df["room_id"].str.upper()


# =========================
# 6. 删除重复记录
# =========================

duplicate_count = df.duplicated().sum()

df = df.drop_duplicates()


# =========================
# 7. 数值字段转换
# =========================

for column in [
    "temperature",
    "humidity",
    "occupancy"
]:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# =========================
# 8. 检查并处理温度异常
# =========================

temperature_abnormal = (
    (df["temperature"] < 0)
    | (df["temperature"] > 50)
)

temperature_abnormal_count = (
    temperature_abnormal.sum()
)

df.loc[
    temperature_abnormal,
    "temperature"
] = pd.NA


# =========================
# 9. 检查并处理湿度异常
# =========================

humidity_abnormal = (
    (df["humidity"] < 0)
    | (df["humidity"] > 100)
)

humidity_abnormal_count = (
    humidity_abnormal.sum()
)

df.loc[
    humidity_abnormal,
    "humidity"
] = pd.NA


# =========================
# 10. occupancy 统一为 0 / 1
# =========================

occupancy_abnormal = (
    ~df["occupancy"].isin([0, 1])
    & df["occupancy"].notna()
)

occupancy_abnormal_count = (
    occupancy_abnormal.sum()
)

df.loc[
    occupancy_abnormal,
    "occupancy"
] = pd.NA


# =========================
# 11. 统一预约状态
# =========================

df["booking_status"] = (
    df["booking_status"]
    .astype(str)
    .str.strip()
    .str.lower()
)

booking_mapping = {
    "occupied": "using"
}

df["booking_status"] = (
    df["booking_status"]
    .replace(booking_mapping)
)


# =========================
# 12. 统一设备状态
# =========================

status_columns = [
    "light_status",
    "projector_status",
    "air_conditioner_status",
    "door_status",
    "smoke_status",
]

for column in status_columns:
    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
        .str.lower()
    )

# 少量不同写法统一
df["light_status"] = (
    df["light_status"]
    .replace({
        "1": "on",
        "0": "off"
    })
)

df["projector_status"] = (
    df["projector_status"]
    .replace({
        "1": "on",
        "0": "off"
    })
)


# =========================
# 13. 统计缺失值
# =========================

missing_temperature = (
    df["temperature"].isna().sum()
)

missing_humidity = (
    df["humidity"].isna().sum()
)

missing_occupancy = (
    df["occupancy"].isna().sum()
)


# =========================
# 14. 按时间排序
# =========================

df = df.sort_values(
    by="timestamp"
).reset_index(drop=True)


# =========================
# 15. 统一时间输出格式
# =========================

df["timestamp"] = df[
    "timestamp"
].dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)


# =========================
# 16. 保存清洗后的数据
# =========================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

after_count = len(df)


# =========================
# 17. 输出质量统计
# =========================

print()
print("========== 数据质量统计 ==========")
print(f"原始数据条数：{before_count}")
print(f"清洗后数据条数：{after_count}")
print(f"删除重复记录：{duplicate_count}")
print(f"无效时间记录：{invalid_time_count}")
print(
    f"温度异常记录："
    f"{temperature_abnormal_count}"
)
print(
    f"湿度异常记录："
    f"{humidity_abnormal_count}"
)
print(
    f"occupancy 非法记录："
    f"{occupancy_abnormal_count}"
)
print(
    f"温度缺失值："
    f"{missing_temperature}"
)
print(
    f"湿度缺失值："
    f"{missing_humidity}"
)
print(
    f"occupancy 缺失值："
    f"{missing_occupancy}"
)
print()
print("清洗完成。")
print("输出文件：")
print(OUTPUT_FILE)


# =========================
# 18. 自动生成质量报告
# =========================

report = f"""# 数据质量检查报告

## 1. 数据说明

本数据为智能会议室管理系统第三周实践使用的教学测试数据。

数据来源标记为：

`source = mock`

因此该数据仅用于课程教学、数据清洗和接口测试，不代表真实树莓派历史采集数据。

## 2. 数据规模

- 原始数据条数：{before_count}
- 清洗后数据条数：{after_count}
- 删除重复记录：{duplicate_count}

## 3. 时间字段处理

将 `timestamp` 统一转换为：

`YYYY-MM-DD HH:MM:SS`

无法正确转换的时间记录数量：

- {invalid_time_count}

## 4. 会议室编号统一

将不同形式的会议室编号统一，例如：

- `room-1`
- `room_1`
- `r01`

统一为：

`R01`

其他会议室编号按照相同规则处理。

## 5. 异常值检查

### 温度

将：

- 小于 0℃
- 大于 50℃

的温度记录标记为缺失值。

发现温度异常记录：

- {temperature_abnormal_count}

### 湿度

将：

- 小于 0%
- 大于 100%

的湿度记录标记为缺失值。

发现湿度异常记录：

- {humidity_abnormal_count}

### 人员状态

`occupancy` 仅允许：

- `0`：无人
- `1`：有人

其他数值标记为缺失。

发现非法 occupancy：

- {occupancy_abnormal_count}

## 6. 缺失值统计

清洗后：

- temperature 缺失：{missing_temperature}
- humidity 缺失：{missing_humidity}
- occupancy 缺失：{missing_occupancy}

本阶段保留这些缺失值并进行标记，不直接虚构数据填补。

## 7. 状态字段统一

对以下状态字段统一使用小写形式：

- booking_status
- light_status
- projector_status
- air_conditioner_status
- door_status
- smoke_status

例如：

- `Booked` → `booked`
- `FREE` → `free`
- `occupied` → `using`
- `ON` → `on`

## 8. 清洗结果

清洗后的正式数据文件：

`data/processed/clean_sensor_data.csv`

该文件将作为后续数据分析和状态接口测试的基础数据版本。
"""

REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)

print()
print("质量报告已生成：")
print(REPORT_FILE)
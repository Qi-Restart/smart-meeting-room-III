# 数据质量检查报告

## 1. 数据说明

本数据为智能会议室管理系统第三周实践使用的教学测试数据。

数据来源标记为：

`source = mock`

因此该数据仅用于课程教学、数据清洗和接口测试，不代表真实树莓派历史采集数据。

## 2. 数据规模

- 原始数据条数：305
- 清洗后数据条数：300
- 删除重复记录：5

## 3. 时间字段处理

将 `timestamp` 统一转换为：

`YYYY-MM-DD HH:MM:SS`

无法正确转换的时间记录数量：

- 0

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

- 3

### 湿度

将：

- 小于 0%
- 大于 100%

的湿度记录标记为缺失值。

发现湿度异常记录：

- 1

### 人员状态

`occupancy` 仅允许：

- `0`：无人
- `1`：有人

其他数值标记为缺失。

发现非法 occupancy：

- 2

## 6. 缺失值统计

清洗后：

- temperature 缺失：7
- humidity 缺失：4
- occupancy 缺失：5

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

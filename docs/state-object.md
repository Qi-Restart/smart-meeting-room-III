# 会议室统一状态对象说明

> 文件名：`docs/state-object.md`  
> 适用项目：智能会议室管理系统 III  
> 用途：统一 Web、后端、树莓派和 Three.js 3D 端使用的会议室状态字段。

## 1. 设计目标

第 3 周需要解决综 II 各模块之间字段名称和状态表示不统一的问题，因此本项目设计统一的会议室状态对象，使树莓派采集端、Python 后端、Web 前端和 Three.js 3D 场景使用同一套字段。

统一状态对象至少包含：

- 会议室信息；
- 状态产生时间；
- 人员状态；
- 环境状态；
- 门禁状态；
- 设备状态；
- 数据来源；
- 数据质量。

## 2. 统一状态对象示例

当前项目暂未接入真实实时设备接口时，可使用教学模拟数据进行接口测试，但必须明确标记：

```json
{
  "timestamp": "2026-10-10T10:30:00+08:00",
  "room_id": "R01",
  "occupancy": true,
  "temperature": 24.6,
  "humidity": 48.0,
  "door_status": "closed",
  "devices": {
    "light": "on",
    "projector": "off",
    "air_conditioner": "auto"
  },
  "source": "mock",
  "quality": "normal"
}
```

其中：

- `source = "mock"`：表示当前数据为教学模拟数据；
- `source = "sensor"`：仅在数据确实来自真实树莓派或传感器时使用。

## 3. 字段定义

| 字段名 | 数据类型 | 是否必填 | 含义 | 数据来源 | 异常值处理 | Web / 3D 使用方式 |
|---|---|---|---|---|---|---|
| `timestamp` | string | 是 | 状态产生时间 | 后端 / 传感器 / 模拟接口 | 无法解析时标记为异常，不用于时间分析 | Web 显示更新时间；3D 用于判断数据是否过期 |
| `room_id` | string | 是 | 会议室唯一编号 | 数据库 / 配置文件 | 统一为 `R01`、`R02`、`R03` 等格式；非法编号返回错误 | Web 用于区分会议室；3D 用于定位对应场景 |
| `occupancy` | boolean | 是 | 当前会议室是否有人 | PIR / 系统状态 / 模拟数据 | 非 `true/false` 或无法转换时标记异常 | Web 显示“有人/无人”；3D 显示“使用中/空闲” |
| `temperature` | number / null | 否 | 当前温度 | DHT11 / 模拟数据 | 小于 0℃ 或大于 50℃ 视为异常，可置为 `null` | Web 显示温度；3D 环境面板显示 |
| `humidity` | number / null | 否 | 当前湿度 | DHT11 / 模拟数据 | 小于 0% 或大于 100% 视为异常，可置为 `null` | Web 显示湿度；3D 环境面板显示 |
| `door_status` | string | 是 | 门禁状态 | 舵机 / 后端状态 / 模拟数据 | 仅允许 `open`、`closed`、`error`、`offline` | Web 显示门禁状态；3D 控制门模型状态 |
| `devices` | object | 是 | 会议室设备状态集合 | 后端 / 树莓派 / 模拟数据 | 子字段缺失时保留对象并标记对应设备未知 | Web 设备控制区使用；3D 映射到设备模型 |
| `devices.light` | string | 否 | 灯光状态 | RGB 灯 / 后端 / 模拟数据 | 统一为 `on`、`off`、`error`、`offline` | Web 显示灯光状态；3D 控制灯光效果 |
| `devices.projector` | string | 否 | 投影仪状态 | 后端 / 模拟数据 | 统一为 `on`、`off`、`error`、`offline` | Web 显示投影状态；3D 更新投影模型 |
| `devices.air_conditioner` | string | 否 | 空调状态 | 后端 / 模拟数据 | 统一为 `on`、`off`、`auto`、`error`、`offline` | Web 显示空调状态；3D 更新空调模型 |
| `source` | string | 是 | 当前状态数据来源 | 系统生成 | 仅允许 `sensor` 或 `mock` | Web 可显示数据来源；用于区分真实和模拟数据 |
| `quality` | string | 是 | 当前状态数据质量 | 后端质量检查 | 统一为 `normal` 或 `abnormal` | Web 显示数据质量；3D 可用于异常提示 |

## 4. 字段命名统一规则

项目中不同模块统一使用小写蛇形命名法：

```text
room_id
door_status
light_status
booking_status
air_conditioner
```

避免同时出现以下不同写法：

```text
roomId
roomID
Room_ID
room_id
```

统一使用：

```text
room_id
```

同理：

```text
doorStatus
door_state
door
```

统一为：

```text
door_status
```

## 5. 状态值统一规则

### 5.1 人员状态

统一使用布尔值：

```json
"occupancy": true
```

表示有人。

```json
"occupancy": false
```

表示无人。

### 5.2 门禁状态

允许值：

```text
open
closed
error
offline
```

### 5.3 灯光状态

允许值：

```text
on
off
error
offline
```

### 5.4 投影仪状态

允许值：

```text
on
off
error
offline
```

### 5.5 空调状态

允许值：

```text
on
off
auto
error
offline
```

### 5.6 数据质量

允许值：

```text
normal
abnormal
```

### 5.7 数据来源

允许值：

```text
sensor
mock
```

说明：

- `sensor`：真实树莓派或传感器采集数据；
- `mock`：教学模拟数据或接口测试数据。

## 6. 异常值处理规则

### 6.1 温度

正常范围暂定：

```text
0℃ ～ 50℃
```

超出范围时：

```json
{
  "temperature": null,
  "quality": "abnormal"
}
```

### 6.2 湿度

正常范围：

```text
0% ～ 100%
```

超出范围时将该字段设置为 `null`，同时：

```json
"quality": "abnormal"
```

### 6.3 occupancy

如果原始数据出现：

```text
2
-1
其他非法值
```

不能直接作为有效状态使用，应转换为缺失或异常状态，并将：

```json
"quality": "abnormal"
```

### 6.4 非法会议室编号

如果请求：

```text
R99
```

而系统中不存在该会议室，则接口应返回明确错误，不生成伪造会议室状态。

## 7. Web 端使用方式

Web 前端主要使用统一状态对象完成：

1. 显示会议室编号；
2. 显示当前有人 / 无人；
3. 显示温湿度；
4. 显示门禁状态；
5. 显示灯光、投影仪和空调状态；
6. 显示数据更新时间；
7. 显示当前数据来源和质量；
8. 为后续设备控制闭环提供统一状态依据。

示例：

```text
会议室：R01
人员状态：有人
温度：24.6℃
湿度：48%
门禁：关闭
灯光：开启
投影仪：关闭
空调：自动
数据来源：mock
数据质量：normal
```

## 8. Three.js 3D 端使用方式

Three.js 场景根据统一状态对象更新模型。

| 状态字段 | 3D 场景用途 |
|---|---|
| `room_id` | 找到对应会议室模型 |
| `occupancy` | 显示空闲 / 使用中状态 |
| `temperature` | 环境信息面板 |
| `humidity` | 环境信息面板 |
| `door_status` | 控制门模型开关 |
| `devices.light` | 控制灯光亮灭 |
| `devices.projector` | 控制投影仪模型状态 |
| `devices.air_conditioner` | 控制空调状态 |
| `quality` | 异常状态时显示提示 |

后续 3D 联动原则：

```text
接口返回统一状态
        ↓
Three.js 读取字段
        ↓
找到对应会议室和设备模型
        ↓
更新模型状态
```

## 9. 与第 3 周清洗数据的关系

实践题 1 已生成：

```text
data/processed/clean_sensor_data.csv
```

清洗后的字段可作为统一状态对象的数据来源之一。

例如清洗数据：

```text
timestamp
room_id
temperature
humidity
occupancy
```

可以转换成：

```json
{
  "timestamp": "2026-09-07T09:00:00+08:00",
  "room_id": "R01",
  "occupancy": true,
  "temperature": 24.5,
  "humidity": 48.0,
  "door_status": "closed",
  "devices": {
    "light": "off",
    "projector": "off",
    "air_conditioner": "off"
  },
  "source": "mock",
  "quality": "normal"
}
```

## 10. 当前阶段说明

当前第 3 周阶段主要完成字段统一和接口约定。

由于本阶段使用的会议室测试数据为教学模拟数据，因此当前接口测试时必须：

```json
"source": "mock"
```

后续如果接入真实树莓派和传感器实时数据，再将来源改为：

```json
"source": "sensor"
```

不能将模拟数据标记为真实传感器数据。

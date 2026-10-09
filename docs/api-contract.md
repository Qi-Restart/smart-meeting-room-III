# 会议室状态接口说明

> 文件名：`docs/api-contract.md`  
> 适用项目：智能会议室管理系统 III  
> 用途：统一 Web、后端、树莓派和 Three.js 3D 端之间的会议室状态查询接口。

## 1. 接口目标

第 3 周需要完成统一会议室状态对象，并通过真实接口或模拟接口返回规范 JSON。

本接口主要用于：

- Web 前端查询会议室实时状态；
- Three.js 3D 场景读取会议室状态；
- 后端统一输出会议室状态数据；
- 后续树莓派真实传感器数据接入；
- 接口异常测试和状态字段统一。

当前阶段使用教学模拟数据，因此接口返回中的：

```json
"source": "mock"
```

表示数据并非真实树莓派实时采集数据。

## 2. 接口地址

### 查询指定会议室状态

```http
GET /api/rooms/{room_id}/state
```

示例：

```http
GET /api/rooms/R01/state
```

其中：

- `{room_id}` 为会议室编号；
- 当前示例支持 `R01`、`R02`、`R03`；
- 非法会议室编号应返回明确错误信息。

## 3. 请求方式

请求方法：

```text
GET
```

请求体：

```text
无
```

请求参数：

| 参数 | 位置 | 类型 | 是否必填 | 说明 |
|---|---|---|---|---|
| `room_id` | URL 路径 | string | 是 | 会议室编号，例如 `R01` |

## 4. 正常响应

当会议室存在时，接口返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {
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
}
```

### 正常响应字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `code` | integer | 业务状态码 |
| `message` | string | 返回信息 |
| `data` | object | 会议室状态对象 |
| `data.timestamp` | string | 状态产生时间 |
| `data.room_id` | string | 会议室编号 |
| `data.occupancy` | boolean | 是否有人 |
| `data.temperature` | number / null | 温度 |
| `data.humidity` | number / null | 湿度 |
| `data.door_status` | string | 门禁状态 |
| `data.devices` | object | 设备状态集合 |
| `data.devices.light` | string | 灯光状态 |
| `data.devices.projector` | string | 投影仪状态 |
| `data.devices.air_conditioner` | string | 空调状态 |
| `data.source` | string | 数据来源 |
| `data.quality` | string | 数据质量 |

## 5. 非法会议室编号响应

如果请求不存在的会议室，例如：

```http
GET /api/rooms/R99/state
```

接口返回：

```json
{
  "code": 404,
  "message": "room not found",
  "data": null
}
```

说明：

- 不为不存在的会议室生成虚假状态；
- 前端收到 `404` 后应提示“会议室不存在”；
- Three.js 不应创建或更新不存在的会议室对象。

## 6. 字段缺失处理

如果部分非关键字段缺失，例如温度暂时不可用：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "timestamp": "2026-10-10T10:30:00+08:00",
    "room_id": "R01",
    "occupancy": true,
    "temperature": null,
    "humidity": 48.0,
    "door_status": "closed",
    "devices": {
      "light": "on",
      "projector": "off",
      "air_conditioner": "auto"
    },
    "source": "mock",
    "quality": "abnormal"
  }
}
```

处理原则：

- 非关键环境数据缺失时，可以返回 `null`；
- 同时将 `quality` 标记为 `abnormal`；
- Web 端显示“数据暂不可用”；
- 3D 端保留上一次有效状态或显示异常提示。

## 7. 非法数据处理

### 温度异常

若温度：

```text
temperature < 0
```

或：

```text
temperature > 50
```

则统一处理为：

```json
"temperature": null,
"quality": "abnormal"
```

### 湿度异常

若湿度：

```text
humidity < 0
```

或：

```text
humidity > 100
```

则统一处理为：

```json
"humidity": null,
"quality": "abnormal"
```

### occupancy 非法

`occupancy` 最终统一为布尔值：

```json
true
```

或：

```json
false
```

如果原始值无法正确转换，则应标记为异常，不直接返回非法数值。

## 8. 设备状态约定

### 门禁状态

允许：

```text
open
closed
error
offline
```

### 灯光状态

允许：

```text
on
off
error
offline
```

### 投影仪状态

允许：

```text
on
off
error
offline
```

### 空调状态

允许：

```text
on
off
auto
error
offline
```

## 9. 数据来源约定

### 真实传感器数据

只有在状态确实来自真实树莓派或传感器时，才允许返回：

```json
"source": "sensor"
```

### 教学模拟数据

当前第三周接口测试阶段使用：

```json
"source": "mock"
```

模拟数据仅用于：

- 接口测试；
- Web 联调；
- 3D 状态联调；
- 异常测试；
- 教学演示。

不能将模拟数据描述为真实树莓派实时采集数据。

## 10. Web 端调用方式

Web 前端可以请求：

```javascript
fetch("/api/rooms/R01/state")
```

成功后读取：

```text
data.room_id
data.occupancy
data.temperature
data.humidity
data.door_status
data.devices
data.quality
```

用于页面状态展示。

## 11. Three.js 3D 端调用方式

Three.js 场景获取接口状态后：

```text
room_id
↓
定位会议室模型
↓
读取设备和环境状态
↓
更新门、灯光、人员状态和环境面板
```

主要映射关系：

| 接口字段 | 3D 用途 |
|---|---|
| `room_id` | 定位会议室 |
| `occupancy` | 显示空闲 / 使用中 |
| `temperature` | 温度显示 |
| `humidity` | 湿度显示 |
| `door_status` | 门模型开关 |
| `devices.light` | 灯光效果 |
| `devices.projector` | 投影仪模型状态 |
| `devices.air_conditioner` | 空调状态 |
| `quality` | 异常状态提示 |

## 12. 接口测试要求

第三周至少完成两类测试。

### 正常测试

请求：

```http
GET /api/rooms/R01/state
```

预期：

- HTTP 请求成功；
- `code = 200`；
- `message = "success"`；
- `data` 返回规范会议室状态对象；
- `room_id = "R01"`。

### 异常测试

请求：

```http
GET /api/rooms/R99/state
```

预期返回：

```json
{
  "code": 404,
  "message": "room not found",
  "data": null
}
```

## 13. 测试工具

可以使用：

- 浏览器；
- Postman；
- curl。

后续将把测试结果记录在：

```text
tests/state_api_test.md
```

并保留接口运行截图或响应结果作为过程证据。

## 14. 当前阶段说明

当前接口规范用于第三周“接口和状态对象统一”实践。

目前接口数据来源为教学模拟数据：

```json
"source": "mock"
```

后续真实树莓派接入时，应保持接口字段和返回结构不变，只替换底层数据来源，使 Web、后端、树莓派和 Three.js 继续使用同一套接口约定。

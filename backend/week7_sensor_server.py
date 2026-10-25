from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import os
from datetime import datetime
from urllib.parse import urlparse


# ============================================================
# 1. 基本配置
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

HOST = "0.0.0.0"
PORT = 8080


# ============================================================
# 2. 会议室当前状态
#
# 当前尚未接入树莓派真实传感器，因此传感器数据设为 None。
# 后续接入 DHT11、光照传感器、超声波传感器后，
# 再由真实硬件数据更新这些字段。
# ============================================================

room_state = {
    "room_id": "R01",

    "temperature": None,

    "humidity": None,

    "light_intensity": None,

    "door_status": "closed",

    "air_conditioner_status": "off",

    "timestamp": None
}


# ============================================================
# 3. 获取当前会议室状态
# ============================================================

def get_current_state():

    state = room_state.copy()

    state["timestamp"] = (
        datetime.now()
        .astimezone()
        .isoformat(timespec="seconds")
    )

    return state


# ============================================================
# 4. HTTP 请求处理
# ============================================================

class MeetingRoomHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            directory=BASE_DIR,
            **kwargs
        )


    # --------------------------------------------------------
    # 公共响应头
    # --------------------------------------------------------

    def end_headers(self):

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        super().end_headers()


    # --------------------------------------------------------
    # GET 请求
    # --------------------------------------------------------

    def do_GET(self):

        parsed_url = urlparse(
            self.path
        )

        path = parsed_url.path


        # ====================================================
        # API：获取 R01 会议室实时状态
        # ====================================================

        if path == "/api/rooms/R01/state":

            state = get_current_state()

            response_data = json.dumps(
                state,
                ensure_ascii=False
            ).encode("utf-8")


            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(response_data))
            )

            self.end_headers()

            self.wfile.write(
                response_data
            )

            return


        # ====================================================
        # API 路径不存在
        # ====================================================

        if path.startswith("/api/"):

            response_data = json.dumps(
                {
                    "error": "API not found",
                    "path": path
                },
                ensure_ascii=False
            ).encode("utf-8")


            self.send_response(404)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(response_data))
            )

            self.end_headers()

            self.wfile.write(
                response_data
            )

            return


        # ====================================================
        # 普通网页和静态文件
        # ====================================================

        super().do_GET()


# ============================================================
# 5. 启动服务器
# ============================================================

def start_server():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        MeetingRoomHandler
    )


    print("")
    print("==============================================")
    print("       智能会议室 Week 7 后端服务")
    print("==============================================")
    print("")

    print(
        "3D会议室："
        f"http://127.0.0.1:{PORT}/frontend/week7_3d/"
    )

    print(
        "状态接口："
        f"http://127.0.0.1:{PORT}/api/rooms/R01/state"
    )

    print("")
    print("当前数据源：尚未连接树莓派真实传感器")
    print("温度：暂无数据")
    print("湿度：暂无数据")
    print("光照：暂无数据")
    print("门状态：关闭")
    print("空调状态：关闭")
    print("")
    print("前端轮询间隔：500 ms")
    print("")
    print("按 Ctrl + C 停止服务器")
    print("")
    print("==============================================")
    print("")


    try:

        server.serve_forever()


    except KeyboardInterrupt:

        print("")
        print("正在停止智能会议室服务...")


    finally:

        server.server_close()

        print("服务已停止。")


# ============================================================
# 6. 程序入口
# ============================================================

if __name__ == "__main__":

    start_server()
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json

HOST = "127.0.0.1"
PORT = 8000

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "state.json"


def load_states():
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


class StateAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code, payload):
        body = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # 首页：方便确认模拟接口是否已启动
        if path == "":
            self.send_json(
                200,
                {
                    "code": 200,
                    "message": "mock state api is running",
                    "data": {
                        "example": "/api/rooms/R01/state",
                        "source": "mock"
                    }
                }
            )
            return

        # 目标接口：
        # GET /api/rooms/R01/state
        parts = path.split("/")

        if (
            len(parts) == 5
            and parts[1] == "api"
            and parts[2] == "rooms"
            and parts[4] == "state"
        ):
            room_id = parts[3].upper()

            try:
                states = load_states()
            except FileNotFoundError:
                self.send_json(
                    500,
                    {
                        "code": 500,
                        "message": "state file not found",
                        "data": None
                    }
                )
                return
            except json.JSONDecodeError:
                self.send_json(
                    500,
                    {
                        "code": 500,
                        "message": "invalid state json",
                        "data": None
                    }
                )
                return

            if room_id not in states:
                self.send_json(
                    404,
                    {
                        "code": 404,
                        "message": "room not found",
                        "data": None
                    }
                )
                return

            self.send_json(
                200,
                {
                    "code": 200,
                    "message": "success",
                    "data": states[room_id]
                }
            )
            return

        self.send_json(
            404,
            {
                "code": 404,
                "message": "endpoint not found",
                "data": None
            }
        )

    def log_message(self, format, *args):
        print(
            f"[HTTP] {self.address_string()} "
            f"- {format % args}"
        )


def main():
    if not STATE_FILE.exists():
        print(f"错误：找不到状态文件：{STATE_FILE}")
        return

    server = HTTPServer(
        (HOST, PORT),
        StateAPIHandler
    )

    print("=" * 50)
    print("智能会议室模拟状态接口已启动")
    print(f"服务地址：http://{HOST}:{PORT}")
    print(
        "正常测试："
        f"http://{HOST}:{PORT}/api/rooms/R01/state"
    )
    print(
        "异常测试："
        f"http://{HOST}:{PORT}/api/rooms/R99/state"
    )
    print('数据来源：mock（教学模拟数据）')
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n接口服务已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

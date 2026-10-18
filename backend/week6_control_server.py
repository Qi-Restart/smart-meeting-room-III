from http.server import (
    SimpleHTTPRequestHandler,
    ThreadingHTTPServer
)

from pathlib import Path

import json
import subprocess
import sys


# ============================================================
# 项目目录
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


RECOGNITION_SCRIPT = (
    PROJECT_ROOT
    / "face_recognition"
    / "recognize_live.py"
)


STATE_FILE = (
    PROJECT_ROOT
    / "frontend"
    / "week6_3d"
    / "state.json"
)


HOST = "127.0.0.1"

PORT = 8080


# 当前人脸识别进程
recognition_process = None


# ============================================================
# 恢复会议室初始状态
# ============================================================

def reset_room_state():

    room_state = {
        "face_status": "unknown",
        "person_id": None,
        "door_status": "closed",
        "light_status": "off",
        "air_conditioner_status": "off"
    }


    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            room_state,
            file,
            ensure_ascii=False,
            indent=2
        )


    print(
        "会议室状态已恢复为初始状态。"
    )


# ============================================================
# HTTP Handler
# ============================================================

class MeetingRoomHandler(
    SimpleHTTPRequestHandler
):

    def __init__(
        self,
        *args,
        **kwargs
    ):

        super().__init__(
            *args,
            directory=str(
                PROJECT_ROOT
            ),
            **kwargs
        )


    # ========================================================
    # 返回 JSON
    # ========================================================

    def send_json(
        self,
        status_code,
        data
    ):

        body = (
            json.dumps(
                data,
                ensure_ascii=False
            )
            .encode(
                "utf-8"
            )
        )


        self.send_response(
            status_code
        )


        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )


        self.send_header(
            "Content-Length",
            str(
                len(body)
            )
        )


        self.end_headers()


        self.wfile.write(
            body
        )


    # ========================================================
    # POST 请求
    # ========================================================

    def do_POST(
        self
    ):

        global recognition_process


        # ----------------------------------------------------
        # 启动人脸识别
        # ----------------------------------------------------

        if (
            self.path
            !=
            "/api/recognition/start"
        ):

            self.send_json(
                404,
                {
                    "code": 404,
                    "message": "endpoint not found"
                }
            )

            return


        # ----------------------------------------------------
        # 如果识别程序已经在运行
        # ----------------------------------------------------

        if (
            recognition_process
            is not None
            and
            recognition_process.poll()
            is None
        ):

            self.send_json(
                409,
                {
                    "code": 409,
                    "message": "recognition already running"
                }
            )

            return


        # ----------------------------------------------------
        # 启动 recognize_live.py
        # ----------------------------------------------------

        try:

            recognition_process = (
                subprocess.Popen(
                    [
                        sys.executable,
                        str(
                            RECOGNITION_SCRIPT
                        ),
                        "--once"
                    ],
                    cwd=str(
                        PROJECT_ROOT
                    )
                )
            )


            self.send_json(
                200,
                {
                    "code": 200,
                    "message": "face recognition started"
                }
            )


            print()

            print(
                "已从网页启动人脸识别程序。"
            )


        except Exception as error:

            self.send_json(
                500,
                {
                    "code": 500,
                    "message": str(error)
                }
            )


# ============================================================
# 启动服务器
# ============================================================

if __name__ == "__main__":

    # 每次启动控制服务，
    # 自动恢复会议室初始状态：
    # 未识别 / 门关闭 / 灯关闭 / 空调关闭
    reset_room_state()


    server = (
        ThreadingHTTPServer(
            (
                HOST,
                PORT
            ),
            MeetingRoomHandler
        )
    )


    print(
        "=" * 60
    )


    print(
        "智能会议室第6周控制服务已启动"
    )


    print(
        "=" * 60
    )


    print(
        f"服务地址："
        f"http://{HOST}:{PORT}"
    )


    print(
        "3D会议室："
        f"http://{HOST}:{PORT}"
        "/frontend/week6_3d/"
    )


    print()


    print(
        "现在可以直接在网页点击"
        "“开始人脸识别”。"
    )


    print()


    print(
        "按 Ctrl+C 停止控制服务。"
    )


    print(
        "=" * 60
    )


    try:

        server.serve_forever()


    except KeyboardInterrupt:

        print()

        print(
            "控制服务已停止。"
        )


    finally:

        server.server_close()
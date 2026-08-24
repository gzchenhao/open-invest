"""
集成测试夹具：为依赖真实 HTTP 的集成测试提供运行中的服务端。

集成测试中的 ProtocolClient / GovernmentInvestmentPromotion 通过
requests 访问 http://localhost:8000（见 server/config/config.py），
因此需要一个真实的运行中服务端。本夹具在测试会话内以守护线程方式
启动 uvicorn 服务端；若 8000 端口已有健康实例则直接复用。
"""

import socket
import threading
import time

import pytest
import requests
import uvicorn

SERVER_HOST = "localhost"
SERVER_PORT = 8000
HEALTH_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/health"


def _is_server_healthy() -> bool:
    try:
        resp = requests.get(HEALTH_URL, timeout=1)
        return resp.status_code == 200
    except Exception:
        return False


def _is_port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((SERVER_HOST, SERVER_PORT)) == 0


@pytest.fixture(scope="session", autouse=True)
def live_server():
    """会话级真实服务端：已运行则复用，否则后台线程启动并在结束后关闭。"""
    if _is_server_healthy():
        # 端口上已有健康实例（例如开发者手动启动的服务），直接复用
        yield
        return

    if _is_port_in_use():
        pytest.skip(
            f"Port {SERVER_PORT} is occupied by a non-OpenInvest process; "
            "integration tests requiring a live server are skipped."
        )

    from server.main import app

    config = uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # 等待服务就绪（最多 10 秒）
    deadline = time.time() + 10
    while time.time() < deadline:
        if _is_server_healthy():
            break
        time.sleep(0.1)
    else:
        server.should_exit = True
        thread.join(timeout=5)
        pytest.fail("Failed to start in-process server for integration tests")

    yield

    server.should_exit = True
    thread.join(timeout=5)

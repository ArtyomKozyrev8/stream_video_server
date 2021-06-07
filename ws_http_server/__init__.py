from aiohttp import web, WSMsgType
import aiohttp_jinja2
import jinja2
from typing import Dict, Any
import logging
from weakref import WeakKeyDictionary, WeakValueDictionary
import asyncio
from datetime import datetime, timedelta
from enum import Enum

LOG_LEVEL = logging.INFO


class NotifyCamera(Enum):
    """we send two kind of messages to camera process
    which indicates whether we would like to receive new frames"""
    resume = b'1'
    stop = b'0'


class CamerasHandler:
    """Contains endpoints relates to cameras ws and cameras info API endpoint"""
    @staticmethod
    async def video_remote_source_handler(req: web.Request) -> web.WebSocketResponse:
        """Receives data from remote camera and distribute data to Queues
         associated with websockets (to web browsers) which want to receive data
         from the camera"""
        ws = web.WebSocketResponse()
        await ws.prepare(req)
        cam_id = req.match_info["cam_id"]
        req.app["cameras"][cam_id] = ws
        async for msg in ws:
            # actually we expect only binary from remote camera
            if msg.type == WSMsgType.BINARY:
                try:
                    for cl_ws, val in req.app["to_browser_ws"].items():
                        if cam_id == val[0]:
                            # datetime.now() is used to drop too slow clients
                            val[1].put_nowait((datetime.now(), msg.data, ))
                except RuntimeError as ex:
                    # we going to change number of items in req.app["to_browser_ws"]
                    # so from time to time you gonna get the error
                    req.app["app_log"].error(ex)
        req.app["app_log"].info('websocket connection closed')
        return ws

    @staticmethod
    async def cameras_list(req: web.Request) -> web.Response:
        """Returns list of cameras which are connected to the server at the moment"""
        return web.json_response({"cameras": list(req.app["cameras"].keys())})


class BrowserClientWSHandler:
    """Contains ops which are related to connections with client web browsers"""
    @staticmethod
    async def from_client_browser_websocket_handler(req: web.Request) -> web.WebSocketResponse:
        """Handles incoming websockets from browser-clients, listen for incoming data"""
        ws = web.WebSocketResponse()
        cam_id = req.match_info["cam_id"]
        q = asyncio.Queue()
        # cam_id is used to understand whether the socket should get update
        # from the certain remote camera
        # q is dedicated to each client oriented websocket
        req.app["to_browser_ws"][ws] = (cam_id, q, )
        asyncio.create_task(BrowserClientWSHandler._feed_from_client_browser_websocket(q, ws, ))
        await ws.prepare(req)
        # monitor messages from client
        # if we will not do it, ws will close itself
        async for _ in ws:
            pass
        req.app["app_log"].info('websocket connection closed')
        return ws

    @staticmethod
    async def _feed_from_client_browser_websocket(
            q: asyncio.Queue,
            ws: web.WebSocketResponse,
    ) -> None:
        """Sends frame from remote camera (from async queue to client browser)"""
        while True:
            data = await q.get()
            if not data:
                break
            if ws.closed:
                break
            try:
                if datetime.now() - data[0] > timedelta(seconds=1.5):
                    with open("ws_http_server/static/slow_connection.png", mode="rb") as f:
                        data = f.read()
                    await ws.send_bytes(data)
                    await ws.close()
                    break
                else:
                    await ws.send_bytes(data[1])
            except (ConnectionAbortedError, ConnectionResetError):
                break


class MonitoringOPs:
    def __init__(self, app: web.Application):
        self.app = app

    async def _control_want_to_receive_data_from_camera(self) -> None:
        """We do not need to receive data from remote camera if no client (browser)
        wants to receive the data at the moment, so we need to notify Camera
        Processing Process that we want/don't want to get data at the moment"""
        while True:
            await asyncio.sleep(2)
            try:
                self.app["app_log"].debug(list(self.app["to_browser_ws"].keys()))
                for cam_id, ws in self.app["cameras"].items():
                    for browser_ws, val in self.app["to_browser_ws"].items():
                        if browser_ws.closed:
                            continue
                        if cam_id == val[0]:
                            await ws.send_bytes(NotifyCamera.resume.value)  # resume frames
                            self.app["app_log"].debug(f"asked {cam_id} continue sending frames")
                            break  # no need to continue
                    else:
                        await ws.send_bytes(NotifyCamera.stop.value)  # stop frames
                        self.app["app_log"].debug(f"asked {cam_id} stop sending frames")
            except RuntimeError:
                pass  # number of elements is dictionaries changes
            except Exception as ex:
                self.app["app_log"].debug(f"control_want_to_receive_data_from_camera error: {ex}")
                try:
                    # last one socket freezes in dict in closing state to unknown reason
                    # remove it manually
                    del self.app["cameras"][cam_id]
                except Exception:
                    pass

    async def _monitor_active_coroutines(self) -> None:
        """monitors whether we do garbage collection fine (check if any "zombie" coroutine Tasks"""
        while True:
            tasks = len(asyncio.all_tasks())
            self.app["app_log"].debug(f"Number of active tasks: {tasks}")
            await asyncio.sleep(15)

    async def on_start(self, app: web.Application) -> None:
        """what should be started before server start"""
        asyncio.create_task(self._monitor_active_coroutines())
        asyncio.create_task(self._control_want_to_receive_data_from_camera())


@aiohttp_jinja2.template("main.html")
async def index(req: web.Request) -> Dict[str, Any]:
    """Just index page"""
    return {}


def create_app(args=None) -> web.Application:
    """app factory is used to start app in terminal"""
    app = web.Application()
    app.router.add_get(
        path="/websocket_handler_site/{cam_id}",
        handler=BrowserClientWSHandler.from_client_browser_websocket_handler,
        name="websocket_handler_site",
    )
    app.router.add_get(
        path="/video_remote_source/{cam_id}",
        handler=CamerasHandler.video_remote_source_handler,
        name="video_remote_source",
    )
    app.router.add_get(path="/cameras_list", handler=CamerasHandler.cameras_list, name="cameras_list")
    app.router.add_get(path="/", handler=index, name="index")

    app.on_startup.append(MonitoringOPs(app).on_start)

    app_log = logging.getLogger("app_log")
    app_log_handler = logging.StreamHandler()
    fmt = logging.Formatter("%(levelname)s | %(asctime)s | %(message)s")
    app_log_handler.setFormatter(fmt)
    app_log.addHandler(app_log_handler)
    app_log.setLevel(LOG_LEVEL)
    app_log.propagate = False
    app["app_log"] = app_log

    app["cameras"] = WeakValueDictionary()  # stores cameras which send data to the app
    app["to_browser_ws"] = WeakKeyDictionary()  # stores client (browsers) sockets

    app.add_routes([web.static('/static', "ws_http_server/static")])
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("ws_http_server/templates"))

    return app

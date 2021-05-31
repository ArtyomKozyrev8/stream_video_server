from aiohttp import web, WSMsgType
import aiohttp_jinja2
import jinja2
from typing import Dict, Any
import logging
from weakref import WeakKeyDictionary
import asyncio
from datetime import datetime, timedelta


routes = web.RouteTableDef()


@routes.get("/", name="index")
@aiohttp_jinja2.template("main.html")
async def index(req: web.Request) -> Dict[str, Any]:
    """Just index page"""
    return {}


@routes.get("/video_remote_source/{cam_id}", name="video_remote_source")
async def video_remote_source(req: web.Request) -> web.WebSocketResponse:
    """Receives data from remote camera and distribute data to """
    ws = web.WebSocketResponse()
    await ws.prepare(req)
    cam_id = req.match_info["cam_id"]
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
                logging.info(ex)
    logging.info('websocket connection closed')
    return ws


@routes.get("/websocket_handler_site/{cam_id}", name="websocket_handler_site")
async def websocket_handler_site(req: web.Request) -> web.WebSocketResponse:
    """handles websocket endpoint"""
    ws = web.WebSocketResponse()
    cam_id = req.match_info["cam_id"]
    q = asyncio.Queue()
    # cam_id is used to understand whether the socket should get update
    # from the certain remote camera
    # q is dedicated to each client oriented websocket
    req.app["to_browser_ws"][ws] = (cam_id, q, )
    asyncio.create_task(feed_websocket_handler_site(q, ws, ))
    await ws.prepare(req)
    # monitor messages from client
    # if we will not do it, ws will close itself
    async for _ in ws:
        pass
    logging.info('websocket connection closed')
    return ws


async def feed_websocket_handler_site(
        q: asyncio.Queue,
        ws: web.WebSocketResponse
):
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


async def monitor_active_coroutines():
    """monitors whether we do garbage collection fine"""
    while True:
        tasks = len(asyncio.all_tasks())
        logging.info(f"Number of active tasks{tasks}")
        await asyncio.sleep(15)


async def on_start(app: web.Application):
    """what should be started before server start"""
    asyncio.create_task(monitor_active_coroutines())


def create_app(args=None) -> web.Application:
    """app factory"""
    app = web.Application()
    app.on_startup.append(on_start)

    app["to_browser_ws"] = WeakKeyDictionary()
    app.add_routes([web.static('/static', "ws_http_server/static")])
    app.add_routes(routes)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("ws_http_server/templates"))
    return app

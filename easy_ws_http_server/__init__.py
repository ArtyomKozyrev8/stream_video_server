from aiohttp import web
import aiohttp_jinja2
import jinja2
from typing import Dict, Any
import logging
import cv2 as cv


routes = web.RouteTableDef()


class CameraHandle:
    @staticmethod
    def open_camera_and_get_image(cap: cv.VideoCapture) -> bytes:
        """
        Demonstrates how to stream video with the help of openCV.

        Note:
            The more users watch video, the more static video looks like.
            Video is a sequence of images, and in this implementation
            images are yielded from generator function.
            So part of images goes to one user, part of images goes to another user.
            And the less images are received by one user, the more static picture looks like.
        """
        while True:
            if not cap.isOpened():
                logging.error("Was not able to open camera")
                break
            ret, frame = cap.read()
            if not ret:
                break
            ret, jpeg = cv.imencode('.jpg', frame)
            yield jpeg.tobytes()


@routes.get("/", name="index")
@aiohttp_jinja2.template("main.html")
async def index(req: web.Request) -> Dict[str, Any]:
    """Just index page"""
    return {}


async def write_to_websocket(cap: cv.VideoCapture, ws: web.WebSocketResponse) -> None:
    """sends data from camera and sends it to websocket"""
    for i in CameraHandle.open_camera_and_get_image(cap):
        if ws.closed:
            break
        try:
            await ws.send_bytes(i)
        except (ConnectionAbortedError, ConnectionResetError):
            break


@routes.get("/websocket_handler_site", name="websocket_handler_site")
async def websocket_handler_site(req: web.Request):
    """handles websocket endpoint"""
    ws = web.WebSocketResponse()
    await ws.prepare(req)
    await write_to_websocket(req.app["cap"], ws)
    logging.info('websocket connection closed')

    return ws


def create_app(args=None) -> web.Application:
    """app factory"""
    app = web.Application()
    app.add_routes([web.static('/static', "easy_ws_http_server/static")])
    cap = cv.VideoCapture(0)  # when we start http server, we open default usb camera
    app["cap"] = cap
    app.add_routes(routes)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("easy_ws_http_server/templates"))
    return app

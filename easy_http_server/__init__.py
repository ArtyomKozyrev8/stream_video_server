from aiohttp import web
import aiohttp_jinja2
import jinja2
from typing import Dict, Any
import cv2 as cv
import logging

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
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n'


@routes.get("/", name="index")
@aiohttp_jinja2.template("main.html")
async def index(req: web.Request) -> Dict[str, Any]:
    """Just index page"""
    return {}


@routes.get("/get_one_image", name="get_one_image")
async def get_one_image(req: web.Request) -> web.Response:
    """Returns only one image in a very specific way"""
    headers = {
        "Content-Type": "multipart/x-mixed-replace;boundary=frame"
    }

    with open(r"easy_http_server/static/test_image.jpg", "rb") as image_file:
        data = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image_file.read() + b'\r\n\r\n'

    return web.Response(body=data, status=200, headers=headers)


@routes.get("/stream_video", name="stream_video")
async def stream_video(req: web.Request) -> web.StreamResponse:
    """streams video from web camera"""
    headers = {
        "Content-Type": "multipart/x-mixed-replace;boundary=frame"
    }
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers=headers,
    )
    await response.prepare(req)

    for image in CameraHandle.open_camera_and_get_image(req.app["cap"]):
        await response.write(image)

    await response.write_eof()
    return response


def create_app(args=None) -> web.Application:
    """app factory"""
    app = web.Application()
    cap = cv.VideoCapture(0)  # when we start http server, we open default usb camera
    app["cap"] = cap
    app.add_routes(routes)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("easy_http_server/templates"))
    return app

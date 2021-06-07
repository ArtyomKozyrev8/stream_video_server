import asyncio
from datetime import datetime, timezone
from io import BytesIO
from enum import Enum
import logging
import time

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType
import cv2 as cv
from PIL import Image, ImageFont, ImageDraw

LOG_LEVEL = logging.INFO
# you can choose any (not empty string) CAMERA_NAME, but should be unique if you have several processes
# which get data from camera and send it to http server
CAMERA_NAME = "cam_100500"
URL = f"http://localhost:7474/video_remote_source/{CAMERA_NAME}"
# RTMP should be 0 if you want to use default web camera
# Otherwise you can provide rtmp link
RTMP = 0


# create log handler block
app_log = logging.getLogger("app_log")
app_log_handler = logging.StreamHandler()
fmt = logging.Formatter("%(levelname)s | %(asctime)s | %(message)s")
app_log_handler.setFormatter(fmt)
app_log.addHandler(app_log_handler)
app_log.setLevel(LOG_LEVEL)  # choose appropriate log level
app_log.propagate = False


class NotifyCamera(Enum):
    """we expect two kind of messages from http server
    which indicates whether we should continue sending frames to it"""
    resume = b'1'
    stop = b'0'


class CameraHandle:
    def __init__(self, camera_capture: cv.VideoCapture):
        self.cam_capture = camera_capture

    def get_image_from_camera(self) -> bytes:
        """Captures frame from camera"""
        if not self.cam_capture.isOpened():
            app_log.error("Was not able to open camera")
            return  # raise exception is outer code
        ret, frame = self.cam_capture.read()
        if not ret:
            app_log.error("Was not able to capture video")
            return  # raise exception is outer code
        ret, jpeg = cv.imencode('.jpg', frame)
        return jpeg.tobytes()

    @staticmethod
    def add_timestamp(img: bytes):
        """Adds current timestamp to frame from camera"""
        img = Image.open(BytesIO(img))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial", size=20)
        t = datetime.now().astimezone(timezone.utc).strftime("%Y-%m-%d %Z\n%H:%M:%S\n%f ms.")
        draw.text((10, 10), t, "black", font=font)
        new_image = BytesIO()
        img.save(new_image, format='JPEG')
        return new_image.getvalue()


class AsyncOPs:
    """Contains all async operations in this process"""
    def __init__(self, url: str):
        # we send frames to http server only if some client(browser) would
        # like to receive such messages from http server
        self.do_send = asyncio.Event()
        self.url = url

    async def send_data(self, cap: cv.VideoCapture, ws: ClientWebSocketResponse) -> None:
        """Send video frame to remote http server through websocket"""
        while True:
            image_bytes = CameraHandle(cap).get_image_from_camera()
            image_bytes = CameraHandle.add_timestamp(image_bytes)
            if not image_bytes:
                continue
            try:
                if self.do_send.is_set():
                    await ws.send_bytes(image_bytes)
                else:
                    app_log.debug(f"Skip sending video frame to client")
                    await asyncio.sleep(0)  # otherwise it wil block everything !
            except (ConnectionAbortedError, ConnectionResetError) as ex:
                app_log.error(f"Failed write to websocket: {ex}")
                raise  # cope with it in outer scope

    @staticmethod
    async def monitor_active_coroutines() -> None:
        """monitors whether we do garbage collection fine (do not create "zombie" coroutines)"""
        while True:
            tasks = len(asyncio.all_tasks())
            app_log.debug(f"Number of active tasks: {tasks}")
            await asyncio.sleep(15)

    async def async_main(self) -> None:
        app_log.info("Video Processing Process started")
        asyncio.create_task(AsyncOPs.monitor_active_coroutines())
        while True:
            try:
                self.do_send.set()
                write_to_client_task = None
                async with ClientSession() as session:
                    app_log.info("Starting new session with http server")
                    cap = cv.VideoCapture(RTMP)  # we open default web camera
                    ws = await session.ws_connect(self.url)
                    write_to_client_task = asyncio.create_task(self.send_data(cap=cap, ws=ws))
                    async for msg in ws:
                        if msg.type == WSMsgType.BINARY:
                            # no client would like to get data from the camera
                            if msg.data == NotifyCamera.stop.value:
                                self.do_send.clear()
                                app_log.debug(f"Stopped sending video to http server")
                            # resume sending frames to http server
                            else:
                                self.do_send.set()
                                app_log.debug("Resume sending video to http server")
            except Exception as ex:
                app_log.error(f"Unexpected error: {ex}")
                time.sleep(5)
            # we should release camera and cancel write task even if we had error
            finally:
                if write_to_client_task:
                    try:
                        cap.release()
                        time.sleep(5)
                    except Exception as ex:
                        app_log.error(f"Failed to release camera capture: {ex}")
                    try:
                        write_to_client_task.cancel()
                    except asyncio.CancelledError:
                        app_log.error("Failed to cancel write_to_client_task")
                    else:
                        app_log.warning("write_to_client_task canceled")


if __name__ == '__main__':
    asyncio.run(AsyncOPs(url=URL).async_main())

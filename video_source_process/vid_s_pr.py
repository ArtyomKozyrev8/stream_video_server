import asyncio
from datetime import datetime, timezone
from io import BytesIO
import logging
import time

from aiohttp import ClientSession
import cv2 as cv
from PIL import Image, ImageFont, ImageDraw


URL = "http://localhost:7474/video_remote_source/cam_100500"


class CameraHandle:
    def __init__(self, camera_capture: cv.VideoCapture):
        self.cam_capture = camera_capture

    def get_image_from_camera(self) -> bytes:
        """Captures frame from camera"""
        if not self.cam_capture.isOpened():
            logging.error("Was not able to open camera")
            return  # raise exception is outer code
        ret, frame = self.cam_capture.read()
        if not ret:
            logging.error("Was not able to capture video")
            return  # raise exception is outer code
        ret, jpeg = cv.imencode('.jpg', frame)
        return jpeg.tobytes()

    @staticmethod
    def add_timestamp(img: bytes):
        """Adds current timestamp to frame from camera"""
        img = Image.open(BytesIO(img))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial", size=28)
        t = datetime.now().astimezone(timezone.utc).strftime("%Y-%m-%d %Z\n%H:%M:%S\n%f ms.")
        draw.text((10, 10), t, "black", font=font)
        new_image = BytesIO()
        img.save(new_image, format='JPEG')
        return new_image.getvalue()


async def async_main(url: str):
    """wrapper around all async ops in this process"""
    logging.info("Video Processing Process started")
    while True:
        cap = cv.VideoCapture(0)  # we open default web camera
        async with ClientSession() as session:
            ws = await session.ws_connect(url)
            while True:
                image_bytes = CameraHandle(cap).get_image_from_camera()
                image_bytes = CameraHandle.add_timestamp(image_bytes)
                if not image_bytes:
                    break  # go to outer while
                try:
                    await ws.send_bytes(image_bytes)
                except (ConnectionAbortedError, ConnectionResetError) as ex:
                    logging.error(f"Failed write to websocket: {ex}")
                    # just start another iteration
                except Exception as ex:
                    logging.error(f"Failed to write to websocket. Unexpected error: {ex}")
                    break  # go to outer while
        try:
            cap.release()
        except Exception as ex:
            logging.error(f"Failed to release camera capture: {ex}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            asyncio.run(async_main(URL))
        except Exception as ex:
            logging.error(f"Unexpected error: {ex}")
            time.sleep(5)

# stream_video_server

The project demonstrates some ways how to create video streaming servers with the help of Aiohttp and OpenCV.

**First One: Easy Video Server Implementation:**

_How to run the most simple version of video stream http server:_

1. create venv

2. install all requirement from `requirement.txt`

3. `python -m aiohttp.web -H 0.0.0.0 -P 7474 easy_http_server:create_app`
 or 
 `python3 -m aiohttp.web -H 0.0.0.0 -P 7474 easy_http_server:create_app`

_Easy server PROs:_

1. easy to implement
2. All in one Process

_Cons:_

1. The more users watch video, the more static video looks like. Note that video is a sequence of images, and in this
implementation images are yielded from generator function, so part of images goes to one user, part of images goes
to another user.

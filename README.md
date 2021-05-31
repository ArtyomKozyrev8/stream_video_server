# stream_video_server

The project demonstrates some ways how to create video streaming servers with the help of Aiohttp and OpenCV.
Ways are listed from simplest implementations to more robust solutions

**First One: The Easiest Video Server Implementation:**

_How to run The Easiest Video Server Implementation:_

1. create venv

2. install all requirement from `requirement.txt`

3. `python -m aiohttp.web -H 0.0.0.0 -P 7474 easy_http_server:create_app`
 or 
 `python3 -m aiohttp.web -H 0.0.0.0 -P 7474 easy_http_server:create_app`

_PROs:_

1. Easy to implement
2. All in one Process

_CONs:_

1. The more users watch video, the more static video looks like. Note that video is a sequence of images, and in this
implementation images are yielded from generator function, so part of images goes to one user, part of images goes
to another user.

**Second One: Easy Websocket Video Server Implementation:**

_How to run Easy Websocket Video Server Implementation:_

1. create venv

2. install all requirement from `requirement.txt`

3. `python -m aiohttp.web -H 0.0.0.0 -P 7474 easy_ws_http_server:create_app`
 or 
 `python3 -m aiohttp.web -H 0.0.0.0 -P 7474 easy_ws_http_server:create_app`

_PROs:_

1. easy to implement
2. Use websockets which are modern solution for bidirectional communications with browser

_CONs:_

1. Though websockets are faster, still the more users watch video, the more static video looks like.
Note that video is a sequence of images, and in this implementation images are yielded from generator function,
so part of images goes to one user, part of images goes to another user.

**Third One: Websocket Video Server Implementation:**

_1. How to run Websocket Video Server Implementation:_

1. create venv

2. install all requirement from `requirement.txt`

3. `python -m aiohttp.web -H 0.0.0.0 -P 7474 ws_http_server:create_app`
 or 
 `python3 -m aiohttp.web -H 0.0.0.0 -P 7474 ws_http_server:create_app`

_2. How to run Video Processing Process_

1. create venv

2. install all requirement from `requirement.txt`

3. `python video_source_process/vid_s_pr.py`
 or 
 `python3 video_source_process/vid_s_pr.py`
 
_PROs:_

1. Can handle multiple clients (browsers) and provide all frames to all clients with small delay
2. Can handle slow clients with nearly no negative effect on other clients
3. Use websockets which are modern solution for bidirectional communications with browser
4. Video Processing is done in another process = less CPU bound ops in http server,
can be distributed between several nodes

_Cons:_

1. Do not scale well, only one http process can work simultaneously. 
Though if you give different addresses (ip + port) to http servers, you can scale quite well.
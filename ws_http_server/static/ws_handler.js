window.onload = (event) => {
    const MAX_VIDEO_CONTAINER_NUM = 12;
    const btnRefresh = document.getElementById("refresh"); // refresh list of cameras
    const btnColorMode = document.getElementById("color_mode"); // day/night changer
    const camerasSelect = document.getElementById("cameras"); // select camera to watch
    // div to store video-containers divs
    const videosContainersDiv = document.getElementById("videos_containers");
    const camera_list_box_ops = new CameraListBoxOps();     // ops related to camera selector
    const btnAdd = document.getElementById("addBtn"); // temp btn
    // list of video containers, used to close ws if browser tav is closed
    const videoContainers = new Array();

    camera_list_box_ops.get_cameras(camerasSelect); // fill camerasSelect with option on page load

    // refresh camera list
    btnRefresh.addEventListener("click", ev => {
        camera_list_box_ops.get_cameras(camerasSelect);
    })

    // change color mode
    btnColorMode.addEventListener("click", ev => {
        let start_color = "light";
        let end_color = "dark";
        ev.target.innerHTML = "&#9728";
        if (ev.target.className.includes("dark")) {
            start_color = "dark";
            end_color = "light";
            ev.target.innerHTML = "&#9790";
        }
        let elements = document.getElementsByClassName(start_color);
        let elements_array = Array.from(elements);
        for (let i = 0; i < elements_array.length; i++) {
            elements_array[i].className = elements_array[i].className.replace(start_color, end_color);
        }
    })
    // adds another one VideoContainer
    btnAdd.addEventListener("click", ev => {
        // check if we already have
        let continueWork = true;
        let n = 0;
        // calculate number of active video containers
        for (let i=0; i<videoContainers.length; i++) {
            if (videoContainers[i].state === "active") {
                n += 1;
            }
        }
        if (n >= MAX_VIDEO_CONTAINER_NUM) {
            continueWork = false;
            let tooMuchVideoContainersElement = new TooMuchVideoContainers(
                `You are not allowed to have more than ${MAX_VIDEO_CONTAINER_NUM} video containers in one Tab!`
            )
            tooMuchVideoContainersElement.create()
        }
        // check active video containers names
        if (continueWork) {
            for (let i = 0; i < videoContainers.length; i++) {
                if (videoContainers[i].state === "active" && videoContainers[i].camera === "cam_100500") {
                    let alert = new DuplicatedCamIDMessage(
                        "cam_100500 video is already displayed. Do you want another video container?",
                    );
                    alert.create(videoContainers);
                    continueWork = false;
                    break
                }
            }
        }
        // if okay, add another one video container
        if (continueWork) {
            let vContainer = new VideoContainer("cam_100500")
            let vContainerDiv = vContainer.create_element();
            videosContainersDiv.appendChild(vContainerDiv);
            // is used on tab close
            videoContainers.push(vContainer);
        }
    })

    // close sockets on tab close
    window.addEventListener("beforeunload", function(e){
        for (let i=0; i<videoContainers.length; i++) {
            // check state of video container
            if (videoContainers[i].state === "active") {
                videoContainers[i].close_ws();
            }
        }
    }, false);
};

class VideoContainer {
    constructor(camera) {
        this.camera = camera;
        this.ws = VideoContainer.create_ws(camera);
        this.state = "active"; // used on tab close
    }

    static create_ws(camera) {
        /**
         * creates websocket
         * @type {URL}
         */
        const socket_url = new URL(`websocket_handler_site/${camera}`, window.location.href);
        socket_url.protocol = socket_url.protocol.replace('http', 'ws');
        return new WebSocket(socket_url)
    }

    close_ws() {
        /**
         * closed websocket
         */
        this.ws.close();
        this.state = "inactive";
    }

    static handle_web_socket_data(event, image)
    /**
     * get image from websocket and display it
     * @param event socket message event
     * @param image - image element to display video
     */
    {
        let reader = new FileReader();
        reader.readAsDataURL(event.data);
        reader.onloadend = function () {
            let base64data = reader.result;
            image.src = "data:image/png;base64" + base64data;
        }
    }

    create_element() {
        /**
         * Creates elements in a div and returns the div
         * @type {HTMLDivElement}
         */
        let div = document.createElement("div");
        div.className = "video_container";
        let removeBtn = document.createElement("button");
        removeBtn.innerText = "x";
        removeBtn.className = "remove_btn";
        div.appendChild(removeBtn);
        let video_img = document.createElement("img");
        const btnColorMode = document.getElementById("color_mode");
        if (btnColorMode.className.includes("dark")) {
            video_img.className = "dark";
        } else {
            video_img.className = "light";
        }

        div.appendChild(video_img);

        removeBtn.addEventListener("click", ev => {
            this.close_ws();
            ev.target.parentElement.parentElement.removeChild(ev.target.parentElement);
        })
        this.ws.addEventListener('message', ev => {
            VideoContainer.handle_web_socket_data(ev, video_img);
        })
        return div
    }
}

class TooMuchVideoContainers {
    /**
     * Message which informs us that we have too much video Containers in One Page
     * @param text - What you would like to say
     */
    constructor(text) {
        this.text = text;
    }
    create() {
        const div = document.createElement("div");
        const btnColorMode = document.getElementById("color_mode");
        let colorMode = "dark";
        if (btnColorMode.className.includes("dark")) {
            colorMode = "dark";
        } else {
            colorMode = "light";
        }
        div.className = `alert ${colorMode}`;
        div.innerHTML = "<h2>" + this.text + "</h2>";
        const btnClose = document.createElement("button");
        btnClose.className = `alert_btn ${colorMode}`;
        btnClose.innerText = "Fine";
        div.appendChild(btnClose);
        document.body.appendChild(div);

        btnClose.addEventListener("click", ev => {
            ev.target.parentElement.parentElement.removeChild(ev.target.parentElement);
        })
    }
}

class DuplicatedCamIDMessage {
    /**
     * Message which informs us that camera with the certain name already displayed in on of Video Containers
     * @param text - What you would like to say
     */
    constructor(text) {
        this.text = text;
    }
    create(containers) {
        const div = document.createElement("div");
        const btnColorMode = document.getElementById("color_mode");
        let colorMode = "dark";
        if (btnColorMode.className.includes("dark")) {
            colorMode = "dark";
        } else {
            colorMode = "light";
        }
        div.className = `alert ${colorMode}`;
        div.innerHTML = "<h2>" + this.text + "</h2>";
        const btnYes = document.createElement("button");
        btnYes.className = `alert_btn ${colorMode}`;
        btnYes.innerText = "Yes"
        const btnNo = document.createElement("button");
        btnNo.className = `alert_btn ${colorMode}`;
        btnNo.innerText = "No"
        div.appendChild(btnYes);
        div.appendChild(btnNo);
        document.body.appendChild(div);

        btnNo.addEventListener("click", ev => {
            ev.target.parentElement.parentElement.removeChild(ev.target.parentElement);
        })

        btnYes.addEventListener("click", ev => {
            const videosContainersDiv = document.getElementById("videos_containers");
            let vContainer = new VideoContainer("cam_100500");
            let vContainerDiv = vContainer.create_element();
            videosContainersDiv.appendChild(vContainerDiv);

            ev.target.parentElement.parentElement.removeChild(ev.target.parentElement);
            // is used on tab close
            containers.push(vContainer);
        })
    }
}

class CameraListBoxOps {
    constructor() {};

    get_cameras(camerasSelect)
    /**
     * Applies to backend to create camera list
     */
    {
        fetch('/cameras_list')
            .then(response => response.json())
            .then(
                data => CameraListBoxOps.create_camera_list(data, camerasSelect)
            );
    }

    static create_camera_list(data, camerasSelect)
    /**
     * creates options for select element
     * @param data - data from backend to create camera list
     */
    {
        let cameras = data["cameras"];
        camerasSelect.innerHTML = "<option disabled selected value> --- select camera to watch --- </option>";
        for (let i = 0; i < cameras.length; i++) {
            let option = document.createElement("option");
            option.value = cameras[i];
            option.innerText = cameras[i];
            camerasSelect.appendChild(option);
        }
    }
}

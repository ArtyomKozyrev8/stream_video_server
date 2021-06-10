window.onload = (event) => {
    const btnRefresh = document.getElementById("refresh");
    const btnColorMode = document.getElementById("color_mode");
    const camerasSelect = document.getElementById("cameras");
    let camera_list_box_ops = new CameraListBoxOps();

    camera_list_box_ops.get_cameras(camerasSelect); // fill camerasSelect with option on page load

    let ws_ops = new WsOps(); // handle all websocket ops on the page

    // close socket on folder close
    window.addEventListener("beforeunload", function(e){
       if (ws_ops.socket !== null) {
           ws_ops.socket.close();
       }
    }, false);

    // when select change handle new websocket
    camerasSelect.addEventListener("change", ev => {
        ws_ops.create_web_socket_connection(ev.target.value);
    })

    // refresh camera list
    btnRefresh.addEventListener("click", ev => {
        camera_list_box_ops.get_cameras(camerasSelect);
    })

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
};

class WsOps {
    constructor() {
        this.socket = null;
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

    create_web_socket_connection(camera)
    /**
     * handles websocket connection with server
     * @param camera name of camera - reveive from current select elemnt option
     */
    {
        const socket_url = new URL(`websocket_handler_site/${camera}`, window.location.href);
        socket_url.protocol = socket_url.protocol.replace('http', 'ws');
        const imgDiv = document.getElementById("video");
        imgDiv.innerHTML = "";
        const img = document.createElement("img");
        const btnColorMode = document.getElementById("color_mode");
        if (btnColorMode.className.includes("dark")) {
            img.className = "dark";
        } else {
            img.className = "light";
        }

        imgDiv.appendChild(img);

        if (this.socket !== null) {
            this.socket.close();
            this.socket.removeEventListener("message", WsOps.handle_web_socket_data);
        }
        this.socket = new WebSocket(socket_url);
        this.socket.addEventListener('message', ev => {
           WsOps.handle_web_socket_data(ev, img);
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

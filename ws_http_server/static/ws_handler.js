let socket = null;  // global variable to to handle websocket
const btnRefresh = document.getElementById("refresh");
const camerasSelect = document.getElementById("cameras");
get_cameras(); // fill camerasSelect with option on page load


// close socket on folder close
window.addEventListener("beforeunload", function(e){
   if (socket !== null) {
       socket.close();
   }
}, false);

function handle_web_socket_data(event, image)
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

function create_web_socket_connection(camera)
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
    imgDiv.appendChild(img);

    if (socket !== null) {
        socket.close();
        socket.removeEventListener("message", handle_web_socket_data);
    }
    socket = new WebSocket(socket_url);
    socket.addEventListener('message', ev => {
        handle_web_socket_data(ev, img);
    })
}

// when select change handle new websocket
camerasSelect.addEventListener("change", ev => {
    create_web_socket_connection(ev.target.value);
})

// refresh camera list
btnRefresh.addEventListener("click", ev => {
    get_cameras();
})


function create_camera_list(data)
/**
 * creates options for select element
 * @param data - data from backend to create camera list
 */
{
    let cameras = data["cameras"];
    camerasSelect.innerHTML = "<option disabled selected value> -- select camera to watch -- </option>";
    for (let i = 0; i < cameras.length; i++) {
        let option = document.createElement("option");
        option.value = cameras[i];
        option.innerText = cameras[i];
        camerasSelect.appendChild(option);
    }
}

function get_cameras()
/**
 * Applies to backend to create camera list
 */
{
    fetch('/cameras_list')
        .then(response => response.json())
        .then(
            data => create_camera_list(data)
        );
}
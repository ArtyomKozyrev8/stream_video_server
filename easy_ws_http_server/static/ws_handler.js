let img = document.getElementById("video");

const socket_url = new URL("websocket_handler_site", window.location.href);
socket_url.protocol = socket_url.protocol.replace('http', 'ws');

let socket = new WebSocket(socket_url);


socket.addEventListener('message', function (event) {
    let reader = new FileReader();
    reader.readAsDataURL(event.data);
    reader.onloadend = function() {
        let base64data = reader.result;
        img.src = "data:image/png;base64" + base64data
    }
});
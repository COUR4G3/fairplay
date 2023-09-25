import Toast from 'bootstrap/js/dist/toast';


var reconnectTimeout = 250;
var socket;


document.addEventListener('htmx:load', (ev) => {
  const toastElList = ev.detail.elt.querySelectorAll('.toast');
  [...toastElList].map((toastEl) => {
    const toast = new Toast(toastEl);
    toast.show();
  });

  if (ev.detail.elt.classList.contains('toast')) {
    const toast = new Toast(ev.detail.elt);
    toast.show();
  }
});


function notify(message, ...args) {
  const toastTemplate = document.querySelector('template.toast');
  const toastNode = toastTemplate.content.cloneNode(true);
  const toastEl = toastNode.querySelector('div');

  const toastMessage = toastNode.querySelector('.toast-message');
  toastMessage.innerText = message;

  if (args.icon) {
    const toastIcon = toastNode.querySelector('.toast-icon');
    toastIcon.classList.add(`fa-${args.icon}`);
    toastIcon.style.display = 'inline-block';
  }

  if (args.level) {
    toastEl.classList.add(`text-bg-${args.level}`);
  }

  if (args.title) {
    const toastTitle = toastNode.querySelector('.toast-title');
    toastTitle.innerText = args.title;
    toastTitle.style.display = 'block';
  }

  const toastContainer = document.querySelector('.toast-container');
  toastContainer.appendChild(toastEl);

  const toast = new Toast(toastEl, { autohide: (!args.sticky) });
  toast.show();
}


function connect() {
  socket = new WebSocket('/notifications');

  socket.addEventListener('close', (ev) => {
    console.debug("Disconnected", ev);

    if (!ev.wasClean) {
      setTimeout(connect, Math.max(reconnectTimeout+=reconnectTimeout, 5000));
    }
  });

  socket.addEventListener('error', (ev) => {
    console.debug("Connection error", ev);
  });

  socket.addEventListener('message', (ev) => {
    // reset reconnection timeout on first successful message
    reconnectTimeout = 250;

    console.debug("Received message", ev);

    ev.data.text().then((data) => {
      decodedData = JSON.parse(data);
      console.debug("Decoded message", decodedData);
      notify(...decodedData);
    });
  });

  socket.addEventListener('open', (ev) => {
    console.debug("Connected", ev);
  });
}


window.addEventListener('DOMContentLoaded', (ev) => {
  // connect();
});

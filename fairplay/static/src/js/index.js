import Dropdown from 'bootstrap/js/dist/dropdown';
import Modal from 'bootstrap/js/dist/modal';
import Offcanvas from 'bootstrap/js/dist/offcanvas';
import Toast from 'bootstrap/js/dist/toast';
import Tooltip from 'bootstrap/js/dist/tooltip';

import * as htmx from 'htmx.org';

import './confirm';
import './editor';
import './icons';
import './notifications';
import './table';
import './time';


document.addEventListener('htmx:load', (ev) => {
  const dropdownTriggerList = ev.detail.elt.querySelectorAll('[data-bs-toggle="dropdown"]');
  [...dropdownTriggerList].map((dropdownTriggerEl) => new Dropdown(dropdownTriggerEl));

  const offcanvasTriggerList = ev.detail.elt.querySelectorAll('[data-bs-toggle="offcanvas"]');
  [...offcanvasTriggerList ].map((offcanvasTriggerEl) => new Offcanvas(offcanvasTriggerEl));

  const tooltipTriggerList = ev.detail.elt.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList ].map((tooltipTriggerEl) => new Tooltip(tooltipTriggerEl));
});


const bootstrap = { Dropdown, Modal, Offcanvas, Toast, Tooltip }

window.bootstrap = bootstrap;
window.htmx = htmx;

export {
  bootstrap,
  htmx,
}

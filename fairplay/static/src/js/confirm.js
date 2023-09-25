import Modal from 'bootstrap/js/dist/modal';

const confirmDialog = document.querySelector('#confirm-dialog');

if (confirmDialog) {
  document.body.addEventListener('htmx:confirm', function(ev) {
    if (ev.detail.elt.getAttribute('hx-confirm') === null) {
      return
    }

    ev.preventDefault();

    const confirmDialogModal = Modal.getOrCreateInstance(confirmDialog);

    const confirmDialogText = confirmDialog.querySelector('#confirm-dialog-text');
    confirmDialogText.innerText = ev.detail.elt.getAttribute('hx-confirm');

    const confirmDialogTitle = confirmDialog.querySelector('#confirm-dialog-title');
    confirmDialogTitle.innerText = ev.detail.elt.dataset.hxConfirmTitle || 'Warning!';

    const confirmDialogCancelBtn = confirmDialog.querySelector('#confirm-dialog-cancel-btn');
    const confirmDialogConfirmBtn = confirmDialog.querySelector('#confirm-dialog-confirm-btn');

    function cancelRequest() {
      confirmDialog.removeEventListener('hide.bs.modal', cancelRequest);
      confirmDialogCancelBtn.removeEventListener('click', cancelRequest);
      confirmDialogConfirmBtn.removeEventListener('click', confirmRequest);
      confirmDialogModal.hide();
    }

    function confirmRequest() {
      confirmDialog.removeEventListener('hide.bs.modal', cancelRequest);
      confirmDialogCancelBtn.removeEventListener('click', cancelRequest);
      confirmDialogModal.hide();
      ev.detail.elt.setAttribute('hx-confirm', '');
      ev.detail.issueRequest();
    }

    confirmDialog.addEventListener('hide.bs.modal', cancelRequest, { once: true });
    confirmDialogCancelBtn.addEventListener('click', cancelRequest, { once: true });
    confirmDialogConfirmBtn.addEventListener('click', confirmRequest, { once: true });

    confirmDialogModal.show();
  });
}

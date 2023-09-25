import Quill from 'quill';

document.addEventListener('htmx:load', (ev) => {
    const editorElList = ev.detail.elt.querySelectorAll('.editor');
    [...editorElList].map((editorEl) => {
        let actualEditorEl = editorEl;

        if (editorEl.tagName == 'INPUT' || editorEl.tagName == 'TEXTAREA') {
            actualEditorEl = document.createElement('div');
            editorEl.parentNode.insertBefore(actualEditorEl, editorEl.nextSibling);

            editorEl.closest('form').addEventListener('submit', (ev) => {
                const htmlContent = actualEditorEl.children[0].innerHTML;
                editorEl.value = htmlContent;
            });
        }

        const options = {
            modules: { toolbar: true },
            placeholder: editorEl.getAttribute('placeholder'),
            theme: 'bubble',
        }

        const editor = new Quill(actualEditorEl, options);

        if (editorEl !== actualEditorEl) {
            editorEl.style.display = 'none';
        }
    });
});

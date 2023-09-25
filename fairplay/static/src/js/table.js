document.addEventListener('htmx:load', (ev) => {
  const selectAllCheckboxes = ev.detail.elt.querySelectorAll('.table-select-all');
  [...selectAllCheckboxes ].map((selectAllCheckbox) => {
    selectAllCheckbox.addEventListener('change', (ev) => {
      const table = selectAllCheckbox.closest('table');
      const selectCheckboxes = table.querySelectorAll('.table-select');

      [...selectCheckboxes ].map((selectCheckbox) => selectCheckbox.checked = selectAllCheckbox.checked);
    });
  });
});

function showFileName(input) {
  const label = document.getElementById('file-name');
  const btn = document.getElementById('submit-btn');
  if (input.files && input.files[0]) {
    label.textContent = '✓ ' + input.files[0].name;
    btn.disabled = false;
  }
}

const dropZone = document.getElementById('drop-zone');
if (dropZone) {
  ['dragenter', 'dragover'].forEach(e => {
    dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('dragover'); });
  });
  ['dragleave', 'drop'].forEach(e => {
    dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('dragover'); });
  });
  dropZone.addEventListener('drop', ev => {
    const file = ev.dataTransfer.files[0];
    if (file) {
      const input = document.getElementById('file-input');
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      showFileName(input);
    }
  });
  dropZone.addEventListener('click', () => document.getElementById('file-input').click());
}

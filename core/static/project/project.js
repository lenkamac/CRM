// Functions used from inline onclick="" handlers must be global (outside DOMContentLoaded)

function toggleDescEdit() {
    const display = document.getElementById('descDisplay');
    const form = document.getElementById('descForm');
    const btn = document.getElementById('descEditBtn');
    const isEditing = !form.classList.contains('d-none');
    display.classList.toggle('d-none', !isEditing);
    form.classList.toggle('d-none', isEditing);
    btn.textContent = isEditing ? 'Edit' : 'Cancel';
}

function openConversationPopup(url, title) {
    const popup = document.getElementById('conversationPopup');
    const frame = document.getElementById('conversationPopupFrame');
    const titleEl = document.getElementById('conversationPopupTitle');

    titleEl.textContent = title || 'Conversation';
    popup.classList.add('show');
    popup.classList.remove('minimized');

    if (url) {
        frame.src = url;
    }

    const modalEl = document.getElementById('newConversationModal');
    const modal = bootstrap.Modal.getInstance(modalEl);

    if (modal) {
        modal.hide();
    }
}

function toggleConversationPopupMinimize() {
    const popup = document.getElementById('conversationPopup');
    popup.classList.toggle('minimized');
}

function closeConversationPopup() {
    const popup = document.getElementById('conversationPopup');
    const frame = document.getElementById('conversationPopupFrame');

    popup.classList.remove('show');
    popup.classList.remove('minimized');
    frame.src = '';
}

document.addEventListener('DOMContentLoaded', function () {
    // Clicking the header of a minimized popup restores it
    const popup = document.getElementById('conversationPopup');
    popup.querySelector('.conversation-popup-header').addEventListener('click', function (event) {
        if (popup.classList.contains('minimized') && !event.target.closest('button')) {
            popup.classList.remove('minimized');
        }
    });

    const deleteConvModal = document.getElementById('deleteConvModal');
    // URL template comes from data-delete-url in the HTML ({% url %} doesn't work in static files)
    const deleteUrl = deleteConvModal.dataset.deleteUrl;

    deleteConvModal.addEventListener('show.bs.modal', function (event) {
        const btn = event.relatedTarget;
        const convPk = btn.getAttribute('data-conv-pk');
        const convTitle = btn.getAttribute('data-conv-title');
        document.getElementById('deleteConvTitle').textContent = convTitle;
        document.getElementById('deleteConvForm').action = deleteUrl.replace('/0/', '/' + convPk + '/');
    });
});

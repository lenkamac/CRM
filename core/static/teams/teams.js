document.addEventListener('DOMContentLoaded', function() {

    const csrfToken = document.querySelector('#newConversationForm [name=csrfmiddlewaretoken]').value;
            // URL templates come from data-* attributes on #chatWindow ({% url %} doesn't work in static files)
            const chatWin = document.getElementById('chatWindow');
            const messagesUrl = chatWin.dataset.messagesUrl;
            const messageAddUrl = chatWin.dataset.messageAddUrl;
            const deleteUrl = chatWin.dataset.deleteUrl;
            const urlFor = (tpl, pk) => tpl.replace('/0/', '/' + pk + '/');

            const win = document.getElementById('chatWindow');
            const titleEl = document.getElementById('chatWindowTitle');
            const thread = document.getElementById('chatThread');
            const form = document.getElementById('chatForm');
            const input = document.getElementById('chatInput');
            let currentConv = null;
            let lastMessageId = 0;
            let pollTimer = null;

            function renderMessage(msg) {
                const empty = thread.querySelector('.chat-empty');
                if (empty) empty.remove();

                const wrap = document.createElement('div');
                wrap.className = 'chat-msg ' + (msg.is_mine ? 'chat-msg-mine' : '');
                const bubble = document.createElement('div');
                bubble.className = 'chat-bubble';
                bubble.textContent = msg.body;
                const meta = document.createElement('div');
                meta.className = 'chat-meta';
                meta.textContent = msg.sender + ' · ' + msg.created_at;
                wrap.append(bubble, meta);
                thread.appendChild(wrap);
                lastMessageId = Math.max(lastMessageId, msg.id);
            }

            function scrollToBottom() {
                thread.scrollTop = thread.scrollHeight;
            }

            async function loadMessages(initial) {
                if (!currentConv) return;
                const resp = await fetch(urlFor(messagesUrl, currentConv), {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                if (!resp.ok) return;
                const data = await resp.json();
                titleEl.textContent = data.title;
                if (initial) {
                    thread.innerHTML = '';
                    lastMessageId = 0;
                    if (!data.messages.length) {
                        thread.innerHTML = '<p class="chat-empty text-muted text-center small my-3">No messages yet. Say hello!</p>';
                    }
                }
                const atBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight < 40;
                data.messages.filter(m => m.id > lastMessageId).forEach(renderMessage);
                if (initial || atBottom) scrollToBottom();
            }

            function openChat(convPk) {
                currentConv = convPk;
                win.classList.remove('d-none', 'minimized');
                thread.innerHTML = '<p class="text-muted text-center small my-3">Loading…</p>';
                loadMessages(true);
                clearInterval(pollTimer);
                // Poll for new messages from other team members
                pollTimer = setInterval(() => {
                    if (!win.classList.contains('minimized')) loadMessages(false);
                }, 5000);
                input.focus();
            }

            function closeChat() {
                win.classList.add('d-none');
                clearInterval(pollTimer);
                currentConv = null;
            }

            function toggleMinimize() {
                win.classList.toggle('minimized');
                if (!win.classList.contains('minimized')) {
                    loadMessages(false);
                    input.focus();
                }
            }

            document.getElementById('chatCloseBtn').addEventListener('click', (e) => { e.stopPropagation(); closeChat(); });
            document.getElementById('chatMinimizeBtn').addEventListener('click', (e) => { e.stopPropagation(); toggleMinimize(); });
            // Clicking the header of a minimized window restores it
            document.getElementById('chatWindowHeader').addEventListener('click', () => {
                if (win.classList.contains('minimized')) toggleMinimize();
            });

            // "Open" buttons in the conversations table
            document.getElementById('conversationRows').addEventListener('click', (e) => {
                const btn = e.target.closest('.js-open-chat');
                if (!btn) return;
                e.preventDefault();
                openChat(btn.dataset.convPk);
            });

            // Send message
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const body = input.value.trim();
                if (!body || !currentConv) return;
                const resp = await fetch(urlFor(messageAddUrl, currentConv), {
                    method: 'POST',
                    headers: {'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest'},
                    body: new URLSearchParams({body}),
                });
                if (!resp.ok) return;
                input.value = '';
                renderMessage(await resp.json());
                scrollToBottom();
            });
            // Enter sends, Shift+Enter makes a new line
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    form.requestSubmit();
                }
            });

            function addConversationRow(conv) {
                const placeholder = document.getElementById('noConversationsRow');
                if (placeholder) placeholder.remove();

                const tr = document.createElement('tr');
                const cells = [conv.title, conv.created_by, conv.created_at].map(text => {
                    const td = document.createElement('td');
                    td.textContent = text;
                    return td;
                });
                const actions = document.createElement('td');
                actions.className = 'text-end';

                const openBtn = document.createElement('a');
                openBtn.href = '#';
                openBtn.className = 'btn btn-sm btn-outline-primary js-open-chat me-1';
                openBtn.dataset.convPk = conv.id;
                openBtn.textContent = 'Open';

                const delBtn = document.createElement('button');
                delBtn.type = 'button';
                delBtn.className = 'btn btn-sm btn-outline-danger';
                delBtn.dataset.bsToggle = 'modal';
                delBtn.dataset.bsTarget = '#deleteConvModal';
                delBtn.dataset.convPk = conv.id;
                delBtn.dataset.convTitle = conv.title;
                delBtn.textContent = 'Delete';

                actions.append(openBtn, delBtn);
                tr.append(...cells, actions);
                document.getElementById('conversationRows').prepend(tr);
            }

            // New conversation: create via AJAX, then open it in the popup
            const newConvForm = document.getElementById('newConversationForm');
            const newConvError = document.getElementById('newConversationError');
            newConvForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                newConvError.classList.add('d-none');
                const resp = await fetch(newConvForm.action, {
                    method: 'POST',
                    headers: {'X-Requested-With': 'XMLHttpRequest'},
                    body: new FormData(newConvForm),
                });
                if (!resp.ok) {
                    newConvError.classList.remove('d-none');
                    return;
                }
                const conv = await resp.json();
                bootstrap.Modal.getOrCreateInstance(document.getElementById('newConversationModal')).hide();
                newConvForm.reset();
                addConversationRow(conv);
                openChat(conv.id);
            });

            const deleteConvModal = document.getElementById('deleteConvModal');
            deleteConvModal.addEventListener('show.bs.modal', function (event) {
                const btn = event.relatedTarget;
                const convPk = btn.getAttribute('data-conv-pk');
                const convTitle = btn.getAttribute('data-conv-title');
                document.getElementById('deleteConvTitle').textContent = convTitle;
                document.getElementById('deleteConvForm').action = urlFor(deleteUrl, convPk);
            });

});

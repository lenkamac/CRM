document.addEventListener('DOMContentLoaded', function () {
    // Task search autocomplete
    (function () {
        const input = document.getElementById('task-search');
        if (!input) return;

        const list = document.getElementById('task-autocomplete-list');
        const form = document.getElementById('task-search-form');
        const autocompleteUrl = input.dataset.autocompleteUrl;

        let activeIndex = -1;
        let suggestions = [];

        function closeList() {
            list.innerHTML = '';
            list.style.display = 'none';
            activeIndex = -1;
        }

        function selectSuggestion(label) {
            input.value = label;
            closeList();
            form.submit();
        }

        function setActive(items) {
            items.forEach(function (el, i) {
                el.classList.toggle('active', i === activeIndex);
            });
        }

        function fetchSuggestions(q) {
            closeList();
            suggestions = [];

            if (!q) return;

            fetch(autocompleteUrl + '?q=' + encodeURIComponent(q))
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    if (!data.length) return;

                    suggestions = data;

                    data.forEach(function (item) {
                        const li = document.createElement('li');

                        li.className = 'list-group-item list-group-item-action';
                        li.style.cursor = 'pointer';
                        li.textContent = item.label;

                        li.addEventListener('mousedown', function (e) {
                            e.preventDefault();
                            selectSuggestion(item.label);
                        });

                        list.appendChild(li);
                    });

                    list.style.display = 'block';
                    activeIndex = -1;
                });
        }

        input.addEventListener('input', function () {
            fetchSuggestions(this.value.trim());
        });

        input.addEventListener('keydown', function (e) {
            const items = [...list.querySelectorAll('li')];

            if (e.key === 'Enter') {
                if (activeIndex >= 0 && suggestions[activeIndex]) {
                    e.preventDefault();
                    selectSuggestion(suggestions[activeIndex].label);
                }
                return;
            }

            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, items.length - 1);
                setActive(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                setActive(items);
            } else if (e.key === 'Escape') {
                closeList();
            }
        });

        document.addEventListener('click', function (e) {
            if (!list.contains(e.target) && e.target !== input) {
                closeList();
            }
        });
    })();

    $(document).ready(function () {

            const taskComments = $("#task-comments");

                if (!taskComments.length) return;

                const editUrlTemplate = taskComments.data("edit-url-template");
                const deleteUrlTemplate = taskComments.data("delete-url-template");
                const refreshUrl = taskComments.data("refresh-url");

                function getCookie(name) {
                  let cookieValue = null;

                  if (document.cookie && document.cookie !== "") {
                    const cookies = document.cookie.split(";");

                    for (let i = 0; i < cookies.length; i++) {
                      const cookie = cookies[i].trim();

                      if (cookie.substring(0, name.length + 1) === (name + "=")) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                      }
                    }
                  }

                  return cookieValue;
                }


            // Handle Edit Button Click
            $("#task-comments").on("click", ".edit-comment-btn", function () {
              var commentId = $(this).data("comment-id");
              $("#edit-comment-form-" + commentId).show();
              $("#comment-content-" + commentId).hide();
              $(this).hide();
            });

            // Handle Cancel Button Click
            $("#task-comments").on("click", ".cancel-comment-btn", function () {
              var commentId = $(this).data("comment-id");
              $("#edit-comment-form-" + commentId).hide();
              $("#comment-content-" + commentId).show();
              $(".edit-comment-btn[data-comment-id='" + commentId + "']").show();
            });

            // Handle Save Button Click
            taskComments.on("click", ".save-comment-btn", function () {
                  var commentId = $(this).data("comment-id");
                  var newContent = $("#edit-comment-textarea-" + commentId).val();

                  $.ajax({
                    url: editUrlTemplate.replace("0", commentId),
                    type: "POST",
                    data: {
                      content: newContent
                    },
                    headers: {
                      "X-CSRFToken": getCookie("csrftoken")
                    },
                    success: function () {
                      refreshComments();
                    },
                    error: function (xhr) {
                      const message = xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : "An error occurred. Please try again.";

                      alert(message);
                    }
                  });
                });

            // Handle Delete Button Click
            taskComments.on("click", ".delete-comment-btn", function () {
                  var commentId = $(this).data("comment-id");

                  if (confirm("Are you sure you want to delete this comment?")) {
                    $.ajax({
                      url: deleteUrlTemplate.replace("0", commentId),
                      type: "POST",
                      headers: {
                        "X-CSRFToken": getCookie("csrftoken")
                      },
                      success: function () {
                        refreshComments();
                      },
                      error: function () {
                        alert("An error occurred. Please try again.");
                      }
                    });
                  }
                });

                function refreshComments() {
                  $.get(refreshUrl, function(data) {
                    taskComments.html(data);
                  });
                }
            });

            const leadSelect = document.getElementById('id_lead');
            const clientSelect = document.getElementById('id_client');

            if (leadSelect && clientSelect) {
                leadSelect.addEventListener('change', () => { if (leadSelect.value) clientSelect.value = ''; });
                clientSelect.addEventListener('change', () => { if (clientSelect.value) leadSelect.value = ''; });
            }


});

function updateStatusText() {
    const checkboxes = document.querySelectorAll('input[name=status]:checked');
    const allCheckbox = document.getElementById('status-all');
    const statusText = document.getElementById('statusFilterText');

    if (checkboxes.length === 0 || allCheckbox.checked) {
        statusText.textContent = 'All';
    } else {
        const labels = Array.from(checkboxes).map(cb => {
            return document.querySelector(`label[for="${cb.id}"]`).textContent;
        });

        statusText.textContent = labels.join(', ');
    }
}
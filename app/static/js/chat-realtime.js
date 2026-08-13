document.addEventListener('DOMContentLoaded', async () => {
  const root = document.getElementById('realtimeChat');
  if (!root) return;

  const channelId = Number(root.dataset.channelId);
  const currentUserId = Number(root.dataset.currentUserId);
  const container = document.getElementById('chatMessages');
  const form = document.getElementById('sendMessageForm');
  const input = document.getElementById('messageInput');

  const appendMessage = (message) => {
    if (document.getElementById(`msg-${message.id}`)) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message';
    wrapper.classList.toggle('mine', Number(message.user_id) === currentUserId);
    wrapper.id = `msg-${message.id}`;

    const header = document.createElement('div');
    header.className = 'msg-header';
    const username = document.createElement('strong');
    username.textContent = message.username || 'Unknown';
    const time = document.createElement('span');
    time.className = 'msg-time';
    time.textContent = new Date(message.created_at).toLocaleTimeString([], {
      hour: '2-digit', minute: '2-digit',
    });
    const content = document.createElement('div');
    content.className = 'msg-content';
    content.textContent = message.content || '';
    header.append(username, time);
    wrapper.append(header, content);
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
  };

  if (window.TriviaSupabase) {
    try {
      await window.TriviaSupabase.connectPrivateChannel(
        `chat:${channelId}:messages`,
        {
          message_created: appendMessage,
          message_deleted: ({ id }) => document.getElementById(`msg-${id}`)?.remove(),
          message_edited: ({ id, content }) => {
            const target = document.querySelector(`#msg-${id} .msg-content`);
            if (target) target.textContent = content;
          },
        },
      );
    } catch (error) {
      console.error('Realtime connection failed', error);
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const content = input.value.trim();
    if (!content) return;
    const response = await fetch(root.dataset.sendUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': root.dataset.csrfToken,
      },
      body: JSON.stringify({ content, channel_id: channelId }),
    });
    const result = await response.json();
    if (!response.ok) {
      window.alert(result.error || 'Failed to send message');
      return;
    }
    input.value = '';
    appendMessage(result.message);
  });
});

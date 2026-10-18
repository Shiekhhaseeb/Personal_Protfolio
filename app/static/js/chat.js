/** Portfolio chat widget — POST /api/chat */

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/** Safe, minimal formatting for bot replies. */
function formatBotMessage(text) {
  let html = escapeHtml(text);

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="chat-strong">$1</strong>');
  html = html.replace(/\*\*/g, '');
  html = html.replace(/\n/g, '<br>');

  return html;
}

function appendMessage(container, text, role, assistantInitials = 'Hz') {
  const wrap = document.createElement('div');
  wrap.className = role === 'user' ? 'chat-message-row chat-message-user' : 'chat-message-row chat-message-bot';

  if (role !== 'user') {
    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar-sm shrink-0';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = assistantInitials;
    wrap.appendChild(avatar);
  }

  const el = document.createElement('div');
  el.className = `chat-bubble ${role}`;

  if (role.startsWith('bot')) {
    el.innerHTML = formatBotMessage(text);
  } else {
    el.textContent = text;
  }

  wrap.appendChild(el);
  container.appendChild(wrap);
  scrollMessagesToBottom(container);
}

function scrollMessagesToBottom(container) {
  requestAnimationFrame(() => {
    container.scrollTop = container.scrollHeight;
  });
}

function resizeChatInput(textarea) {
  if (!textarea) return;
  const maxHeight = 120;
  const minHeight = 36;
  textarea.style.height = '0';
  const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
}

function showTypingIndicator(container, assistantInitials, assistantName = 'Assistant') {
  removeTypingIndicator();

  const wrap = document.createElement('div');
  wrap.id = 'chat-typing';
  wrap.className = 'chat-message-row chat-message-bot';
  wrap.setAttribute('aria-label', `${assistantName} is typing`);

  const avatar = document.createElement('div');
  avatar.className = 'chat-avatar-sm shrink-0';
  avatar.setAttribute('aria-hidden', 'true');
  avatar.textContent = assistantInitials;

  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble bot chat-typing-bubble';
  bubble.innerHTML = `
    <span class="chat-typing-text">${assistantName} is thinking</span>
    <span class="chat-typing-dots" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
  `;

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  container.appendChild(wrap);
  scrollMessagesToBottom(container);
}

function removeTypingIndicator() {
  document.getElementById('chat-typing')?.remove();
}

function createSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-IN';
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;
  return recognition;
}

document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('chat-root');
  if (!root) return;

  const assistantName = root.dataset.assistantName || 'Haze';
  const assistantInitials = root.dataset.assistantInitials || 'Hz';
  const panel = document.getElementById('chat-panel');
  const launcher = document.getElementById('chat-launcher');
  const closeBtn = document.getElementById('chat-close');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');
  const sendBtn = document.getElementById('chat-send');
  const micBtn = document.getElementById('chat-mic');
  const suggestions = document.getElementById('chat-suggestions');
  const heroAskBtn = document.getElementById('hero-ask-haze');

  let isOpen = false;
  let isLoading = false;
  let isListening = false;
  let recognition = createSpeechRecognition();
  const voiceSupported = Boolean(recognition);

  const teaser = document.getElementById('chat-teaser');
  const teaserClose = document.getElementById('chat-teaser-close');

  if (micBtn) {
    if (!voiceSupported) {
      micBtn.classList.add('chat-mic-unsupported');
      micBtn.setAttribute('title', 'Voice input is not supported in this browser (try Chrome/Edge)');
      micBtn.setAttribute('aria-label', 'Voice input unsupported in this browser');
    }
  }

  // Teaser bubble: auto-opens after 8 seconds, dismissible, once per session
  const TEASER_STORAGE_KEY = 'haze_chat_teaser_shown';
  function dismissTeaser() {
    if (!teaser) return;
    teaser.classList.add('hidden');
    try {
      sessionStorage.setItem(TEASER_STORAGE_KEY, 'true');
    } catch {
      // ignore storage errors
    }
  }

  if (teaser && !sessionStorage.getItem(TEASER_STORAGE_KEY)) {
    const teaserTimer = setTimeout(() => {
      if (!isOpen && !sessionStorage.getItem(TEASER_STORAGE_KEY)) {
        teaser.classList.remove('hidden');
      }
    }, 8000);

    teaserClose?.addEventListener('click', (e) => {
      e.stopPropagation();
      clearTimeout(teaserTimer);
      dismissTeaser();
    });

    teaser.addEventListener('click', (e) => {
      if (e.target !== teaserClose) {
        dismissTeaser();
        togglePanel(true);
      }
    });
  }

  function stopListening() {
    if (!isListening || !recognition) return;
    isListening = false;
    recognition.stop();
    micBtn?.classList.remove('chat-mic-active');
    if (input && !input.value.trim()) {
      input.placeholder = 'Type or tap the mic to speak…';
    }
  }

  function updateMicState() {
    if (!micBtn) return;
    const disabled = isLoading || isListening;
    micBtn.disabled = isLoading;
    if (!voiceSupported) {
      micBtn.setAttribute('title', 'Voice input is not supported in this browser (try Chrome/Edge)');
    } else if (isLoading) {
      micBtn.setAttribute('title', `Wait for ${assistantName} to reply…`);
    } else if (isListening) {
      micBtn.setAttribute('title', 'Listening… tap to stop');
    } else {
      micBtn.setAttribute('title', 'Speak your question');
    }
  }

  function togglePanel(open) {
    isOpen = open;
    panel.classList.toggle('hidden', !open);
    launcher.classList.toggle('chat-launcher-active', open);
    launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      dismissTeaser();
      input.focus();
    } else {
      stopListening();
    }
  }

  function hideSuggestions() {
    suggestions?.classList.add('hidden');
  }

  const conversationHistory = [];

  async function sendMessage(message) {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;

    hideSuggestions();
    appendMessage(messages, trimmed, 'user', assistantInitials);
    input.value = '';
    resizeChatInput(input);
    isLoading = true;
    sendBtn.disabled = true;
    updateMicState();
    showTypingIndicator(messages, assistantInitials, assistantName);

    // Prepare conversation memory payload (up to last 4 turns)
    const historyPayload = conversationHistory.slice(-4);
    // Record user turn locally
    conversationHistory.push({ role: 'user', content: trimmed });

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history: historyPayload }),
      });

      const data = await res.json().catch(() => ({}));
      removeTypingIndicator();

      if (!res.ok) {
        // Rollback failed user turn so it does not poison future requests
        conversationHistory.pop();
        let errorMsg = 'Something went wrong. Please try again.';
        if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errorMsg = data.detail.map((err) => err.msg || JSON.stringify(err)).join(', ');
        } else if (data.detail && typeof data.detail === 'object') {
          errorMsg = data.detail.msg || JSON.stringify(data.detail);
        }
        appendMessage(messages, errorMsg, 'bot error', assistantInitials);
      } else {
        appendMessage(messages, data.reply, 'bot', assistantInitials);
        // Record assistant turn in memory
        conversationHistory.push({ role: 'assistant', content: data.reply });
        if (conversationHistory.length > 8) {
          conversationHistory.splice(0, conversationHistory.length - 8);
        }
      }
    } catch {
      conversationHistory.pop();
      removeTypingIndicator();
      appendMessage(messages, 'Network error. Please check your connection.', 'bot error', assistantInitials);
    } finally {
      isLoading = false;
      sendBtn.disabled = false;
      updateMicState();
    }
  }

  if (recognition && micBtn) {
    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('chat-mic-active');
      input.placeholder = 'Listening… speak now';
      updateMicState();
    };

    recognition.onresult = (event) => {
      let interim = '';
      let finalText = '';

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interim += transcript;
        }
      }

      input.value = (finalText || interim).trim();
      resizeChatInput(input);
      scrollMessagesToBottom(messages);
    };

    recognition.onend = () => {
      const spoken = input.value.trim();
      const wasListening = isListening;
      isListening = false;
      micBtn.classList.remove('chat-mic-active');
      input.placeholder = 'Type or tap the mic to speak…';
      updateMicState();

      if (wasListening && spoken && !isLoading) {
        sendMessage(spoken);
      }
    };

    recognition.onerror = (event) => {
      isListening = false;
      micBtn.classList.remove('chat-mic-active');
      input.placeholder = 'Type or tap the mic to speak…';
      updateMicState();

      if (event.error === 'not-allowed') {
        appendMessage(
          messages,
          'Microphone access was denied. Allow mic permission in your browser, or type your question.',
          'bot error',
          assistantInitials,
        );
      } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
        appendMessage(
          messages,
          'Could not hear you. Please try again or type your question.',
          'bot error',
          assistantInitials,
        );
      }
    };

    micBtn.addEventListener('click', () => {
      if (isLoading) return;

      if (!voiceSupported) {
        appendMessage(
          messages,
          'Voice input works best in Chrome or Edge. Please type your question, or switch browsers.',
          'bot error',
          assistantInitials,
        );
        return;
      }

      if (isListening) {
        stopListening();
        return;
      }

      input.value = '';
      try {
        recognition.start();
      } catch {
        // start() throws if already started
      }
    });
  } else if (micBtn) {
    micBtn.addEventListener('click', () => {
      appendMessage(
        messages,
        'Voice input works best in Chrome or Edge. Please type your question, or switch browsers.',
        'bot error',
        assistantInitials,
      );
    });
  }

  launcher.addEventListener('click', () => togglePanel(!isOpen));
  closeBtn.addEventListener('click', () => togglePanel(false));

  heroAskBtn?.addEventListener('click', () => togglePanel(true));

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener('input', () => resizeChatInput(input));

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  resizeChatInput(input);

  suggestions?.querySelectorAll('.chat-suggestion-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const question = chip.dataset.question;
      if (question) sendMessage(question);
    });
  });
});

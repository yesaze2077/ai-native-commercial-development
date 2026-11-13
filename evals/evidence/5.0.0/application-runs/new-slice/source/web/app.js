'use strict';
const form = document.querySelector('#ticket-form');
const titleInput = form.elements.title;
const submit = form.querySelector('button');
const filter = document.querySelector('#status-filter');
const list = document.querySelector('#tickets');
const empty = document.querySelector('#empty');
const feedback = document.querySelector('#feedback');
const formError = document.querySelector('#form-error');
const queueError = document.querySelector('#queue-error');
let loadingVersion = 0;

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The request could not be completed.');
    return result;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The local queue took too long. Please try again.');
    if (error instanceof TypeError) throw new Error('Cannot reach the local queue. Check that the server is running, then try again.');
    throw error;
  } finally { clearTimeout(timer); }
}

function announceError(message) {
  document.querySelector('#queue-error-text').textContent = message;
  queueError.hidden = false;
}

function showEmpty(status) {
  empty.hidden = false;
  document.querySelector('#empty-heading').textContent = status === 'all' ? 'A fresh start.' : `No ${status} requests.`;
  document.querySelector('#empty-text').textContent = status === 'all' ? 'Add your first request above to get things moving.' : status === 'open' ? 'Everything is closed. Add a request when you need one.' : 'Completed requests will appear here.';
}

function render(tickets) {
  list.replaceChildren();
  empty.hidden = true;
  if (!tickets.length) showEmpty(filter.value);
  for (const ticket of tickets) {
    const row = document.createElement('li');
    row.className = 'ticket';
    row.dataset.ticketId = ticket.id;
    const main = document.createElement('div');
    main.className = 'ticket-main';
    const title = document.createElement('h3');
    title.className = 'ticket-title';
    title.textContent = ticket.title;
    const meta = document.createElement('div');
    meta.className = 'ticket-meta';
    const badge = document.createElement('span');
    badge.className = `badge ${ticket.status}`;
    badge.textContent = ticket.status;
    const id = document.createElement('span');
    id.textContent = `Request #${ticket.id}`;
    meta.append(badge, id);
    main.append(title, meta);
    row.append(main);
    if (ticket.status === 'open') {
      const close = document.createElement('button');
      close.type = 'button';
      close.dataset.action = 'close';
      close.textContent = 'Close request';
      close.setAttribute('aria-label', `Close request: ${ticket.title}`);
      close.addEventListener('click', async () => {
        close.disabled = true;
        close.textContent = 'Closing…';
        queueError.hidden = true;
        try {
          await api(`/api/tickets/${ticket.id}/close`, { method: 'POST' });
          await load('Request closed.');
          filter.focus();
        } catch (error) {
          close.disabled = false;
          close.textContent = 'Close request';
          announceError(error.message);
        }
      });
      row.append(close);
    }
    list.append(row);
  }
}

async function load(message = '') {
  const version = ++loadingVersion;
  list.setAttribute('aria-busy', 'true');
  queueError.hidden = true;
  feedback.textContent = 'Loading requests…';
  try {
    const tickets = await api(`/api/tickets?status=${encodeURIComponent(filter.value)}`);
    if (version !== loadingVersion) return;
    render(tickets);
    feedback.textContent = message || (tickets.length ? 'Newest requests first.' : '');
  } catch (error) {
    if (version !== loadingVersion) return;
    // Do not leave rows from a different filter looking like fresh results.
    list.replaceChildren();
    empty.hidden = true;
    feedback.textContent = '';
    announceError(error.message);
  } finally {
    if (version === loadingVersion) list.setAttribute('aria-busy', 'false');
  }
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (submit.disabled) return;
  const title = titleInput.value.trim();
  if (!title || Array.from(title).length > 120) {
    titleInput.setAttribute('aria-invalid', 'true');
    formError.textContent = 'Enter a title with 1–120 nonblank characters.';
    formError.hidden = false;
    titleInput.focus();
    return;
  }
  formError.hidden = true;
  titleInput.removeAttribute('aria-invalid');
  submit.disabled = true;
  submit.textContent = 'Saving…';
  try {
    await api('/api/tickets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title }) });
    titleInput.value = '';
    filter.value = 'all';
    await load('Request added.');
    titleInput.focus();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    submit.disabled = false;
    submit.textContent = 'Add request ↗';
  }
});

titleInput.addEventListener('input', () => {
  formError.hidden = true;
  titleInput.removeAttribute('aria-invalid');
});
filter.addEventListener('change', () => load());
document.querySelector('#retry').addEventListener('click', () => load());
load();

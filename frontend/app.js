'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
let review = null;
let busy = false;
const storageKey = 'resume-assistant-document';
function remember(id) { try { sessionStorage.setItem(storageKey, id); } catch { /* UI works without storage. */ } }
function remembered() { try { return sessionStorage.getItem(storageKey); } catch { return null; } }
async function api(path, options = {}) {
  const response = await fetch(path, options);
  let body;
  try { body = await response.json(); } catch { body = {}; }
  if (!response.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}). Check your input and try again.`;
    throw new Error(response.status >= 500 ? 'Unable to complete the request. Check the server logs and database configuration.' : detail);
  }
  return body;
}
function json(method, body) { return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }; }
async function action(operation) {
  if (busy) return;
  busy = true;
  const controls = [...document.querySelectorAll('button, input, select, textarea')].map(el => [el, el.disabled]);
  controls.forEach(([el]) => { el.disabled = true; });
  $('#error').hidden = true;
  try { await operation(); }
  catch (error) { $('#error').textContent = error.message || 'Connection failed. Check that the server is running.'; $('#error').hidden = false; }
  finally { busy = false; controls.forEach(([el, disabled]) => { if (el.isConnected) el.disabled = disabled; }); }
}
function selectedSpan() { return review?.spans.find(span => span.sequence === Number($('#span-select').value)); }
function renderFacts() {
  const span = selectedSpan();
  $('#source-body').textContent = span?.body || '';
  $('#extract').disabled = !span;
  const facts = review.facts.filter(fact => fact.source_sequence === span?.sequence);
  $('#count').textContent = `${facts.length} ${facts.length === 1 ? 'fact' : 'facts'}`;
  $('#empty').hidden = facts.length > 0;
  $('#facts').replaceChildren();
  for (const fact of facts) {
    const card = $('#fact-template').content.firstElementChild.cloneNode(true);
    $('.fact-id', card).textContent = `Fact #${fact.id}`;
    const badge = $('.badge', card);
    badge.textContent = ({ pending: 'Pending', confirmed: 'Confirmed', rejected: 'Rejected' })[fact.status] || fact.status;
    badge.classList.toggle('confirmed', fact.status === 'confirmed');
    badge.classList.toggle('rejected', fact.status === 'rejected');
    $('.claim', card).textContent = fact.claim;
    $('.quote', card).textContent = fact.evidence_quote;
    $('.original p', card).textContent = fact.original_claim;
    $('.eligibility', card).textContent = fact.status === 'confirmed' ? 'Confirmed. Eligible as evidence for generation.' : fact.status === 'rejected' ? 'Rejected. Edit before confirming again.' : 'Confirmation required before use in generation.';
    const fields = [['Source section', String(fact.source_sequence)], ['Extraction run', fact.extraction_run_id ?? 'Not recorded'], ['Confirmed at', fact.confirmed_at ? `${fact.confirmed_at} UTC` : 'Not confirmed'], ['Updated at', `${fact.updated_at} UTC`]];
    for (const [key, value] of fields) {
      const dt = document.createElement('dt'); dt.textContent = key;
      const dd = document.createElement('dd'); dd.textContent = value;
      $('.metadata', card).append(dt, dd);
    }
    const confirm = $('.confirm', card);
    confirm.disabled = fact.status !== 'pending';
    confirm.textContent = fact.status === 'confirmed' ? 'Confirmed' : 'Confirm';
    confirm.onclick = () => action(async () => {
      const response = await api('/fact/', json('POST', { fact_id: fact.id }));
      updateFact(response.fact);
    });
    const reject = $('.reject', card);
    reject.disabled = fact.status === 'rejected';
    reject.textContent = fact.status === 'rejected' ? 'Rejected' : 'Reject';
    reject.onclick = () => action(async () => {
      const response = await api(`/facts/${fact.id}/reject`, {method: 'POST'});
      updateFact(response.fact);
    });
    const form = $('.edit-form', card);
    const textarea = $('textarea', card);
    $('.edit', card).onclick = () => { form.hidden = false; textarea.value = fact.claim; textarea.focus(); };
    $('.cancel', card).onclick = () => { form.hidden = true; };
    form.onsubmit = event => {
      event.preventDefault();
      if (!textarea.value.trim()) { textarea.setCustomValidity('Enter a statement.'); textarea.reportValidity(); return; }
      action(async () => {
        const response = await api(`/facts/${fact.id}`, json('PATCH', { claim: textarea.value }));
        updateFact(response.fact);
      });
    };
    textarea.oninput = () => textarea.setCustomValidity('');
    $('#facts').append(card);
  }
}
function updateFact(fact) { const index = review.facts.findIndex(item => item.id === fact.id); if (index < 0) review.facts.push(fact); else review.facts[index] = fact; renderFacts(); }
async function loadReview(id) {
  const loaded = await api(`/documents/${encodeURIComponent(id)}/review`);
  review = loaded;
  remember(id);
  $('#filename').textContent = review.filename;
  $('#document-id').textContent = id;
  $('#span-select').replaceChildren();
  for (const span of review.spans) { const option = document.createElement('option'); option.value = span.sequence; option.textContent = `${span.sequence}. ${span.section || 'Body'}`; $('#span-select').append(option); }
  $('#workspace').hidden = false;
  renderFacts();
}
$('#span-select').onchange = renderFacts;
let droppedFile = null;
const importForm = $('#import-form');
const fileInput = $('#file');
fileInput.onchange = () => {
  droppedFile = null;
  $('#selected-file').textContent = fileInput.files[0]?.name || 'or drop a file here';
};
importForm.ondragover = event => {
  event.preventDefault();
  if (!busy) importForm.classList.add('drag-over');
};
importForm.ondragleave = () => importForm.classList.remove('drag-over');
importForm.ondrop = event => {
  event.preventDefault();
  importForm.classList.remove('drag-over');
  if (busy) return;
  const file = event.dataTransfer.files[0];
  if (!file) return;
  droppedFile = file;
  fileInput.value = '';
  $('#selected-file').textContent = file.name;
};
importForm.onsubmit = event => {
  event.preventDefault();
  const file = droppedFile || fileInput.files[0];
  if (!file) {
    $('#error').textContent = 'Select or drop a Markdown file first.';
    $('#error').hidden = false;
    return;
  }
  action(async () => {
    const data = new FormData(); data.append('file', file);
    const imported = await api('/documents/import', { method: 'POST', body: data });
    await loadReview(imported.document_id);
  });
};
$('#extract').onclick = () => {
  const span = selectedSpan();
  if (!span) return;
  action(async () => {
    const response = await api(`/documents/${encodeURIComponent(review.document_id)}/spans/${span.sequence}/draft`, { method: 'POST' });
    updateFact(response.fact_draft);
  });
};
const lastDocument = remembered();
if (lastDocument) action(async () => { await loadReview(lastDocument); });

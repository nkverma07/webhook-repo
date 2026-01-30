/*
  Frontend polling logic.

  This file intentionally keeps formatting logic on the client side so that
  the backend can remain a clean JSON API.
*/

const POLL_MS = 15000;

function formatMessage(e) {
  const ts = e.timestamp;

  if (e.action === "PUSH") {
    return `${e.author} pushed to ${e.to_branch} on ${ts}`;
  }
  if (e.action === "PULL_REQUEST") {
    return `${e.author} submitted a pull request from ${e.from_branch} to ${e.to_branch} on ${ts}`;
  }
  if (e.action === "MERGE") {
    return `${e.author} merged branch ${e.from_branch} to ${e.to_branch} on ${ts}`;
  }
  return `Unknown event`;
}

function setStatus(text) {
  const pill = document.getElementById("statusPill");
  pill.textContent = text;
}

function render(events) {
  const list = document.getElementById("eventsList");
  const empty = document.getElementById("emptyState");

  list.innerHTML = "";

  if (!events || events.length === 0) {
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";

  for (const e of events) {
    const li = document.createElement("li");

    const p = document.createElement("p");
    p.className = "msg";
    p.textContent = formatMessage(e);

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `action=${e.action} request_id=${e.request_id}`;

    li.appendChild(p);
    li.appendChild(meta);
    list.appendChild(li);
  }
}

async function fetchEvents() {
  setStatus("Loading…");
  try {
    const res = await fetch("/events");
    if (!res.ok) {
      setStatus(`Error (${res.status})`);
      return;
    }
    const data = await res.json();
    render(data);
    setStatus(`Last updated: ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    setStatus("Network error");
  }
}

function startPolling() {
  fetchEvents();
  setInterval(fetchEvents, POLL_MS);

  const btn = document.getElementById("refreshBtn");
  btn.addEventListener("click", fetchEvents);
}

window.addEventListener("DOMContentLoaded", startPolling);


const BACKEND_URL = (document.body?.dataset?.backendUrl || "").trim() || "http://127.0.0.1:8001";

let sessionId = null;
let lastStage = null;
let uploadHintShown = false;
let allExtracted = {};  // cumulative OCR data across uploads

const chatContainer = document.getElementById("chat_container");
const msgInput = document.getElementById("msg");
const loadingIndicator = document.getElementById("loading_indicator");
const statusText = document.getElementById("upload_status");
const sessionBadge = document.getElementById("session_badge");
const stateBadge = document.getElementById("state_badge");
const workerList = document.getElementById("worker_list");
const loopbackChip = document.getElementById("loopback_chip");
const workerNote = document.getElementById("worker_note");
const extractedBox = document.getElementById("extracted_box");
const extractedItems = document.getElementById("extracted_items");
const downloadBox = document.getElementById("download_box");
const downloadLink = document.getElementById("download_link");

// ---------- UI helpers ----------

function updateBadges(id, state) {
  if (id) {
    sessionBadge.textContent = `Session: ${id}`;
  }
  if (state) {
    stateBadge.textContent = `State: ${state}`;
  }
}

const STATE_ORDER = [
  "GREETING",
  "CONSENT",
  "CUSTOMER_ID",
  "AMOUNT",
  "NEED_DOCS",
  "DOC_UPLOAD",
  "OCR_CONFIRM",
  "UNDERWRITING",
  "DECISION",
  "COMPLETED"
];

const WORKER_FLOW = [
  { label: "Consent worker", states: ["CONSENT"] },
  { label: "Customer ID worker", states: ["CUSTOMER_ID"] },
  { label: "Amount worker", states: ["AMOUNT"] },
  { label: "Document worker", states: ["NEED_DOCS", "DOC_UPLOAD"] },
  { label: "OCR confirmation", states: ["OCR_CONFIRM"] },
  { label: "Underwriting worker", states: ["UNDERWRITING"] },
  { label: "Decision worker", states: ["DECISION", "COMPLETED"] }
];

function resolveStateIndex(state) {
  const idx = STATE_ORDER.indexOf(state || "");
  return idx === -1 ? 0 : idx;
}

function renderWorkers(currentState, stateHistory = []) {
  if (!workerList) return;
  const currentIdx = resolveStateIndex(currentState);
  const historyIdx = stateHistory
    .map(resolveStateIndex)
    .filter((v) => Number.isFinite(v));
  const maxIdx = historyIdx.length ? Math.max(...historyIdx) : currentIdx;
  const loopback = maxIdx > currentIdx;

  if (loopbackChip) {
    loopbackChip.textContent = loopback ? "Loopback" : "Stable";
    loopbackChip.classList.toggle("loopback", loopback);
  }

  if (workerNote) {
    workerNote.textContent = loopback
      ? "Flow looped back to a previous worker."
      : "Workers update as the session progresses.";
  }

  workerList.innerHTML = "";
  WORKER_FLOW.forEach((worker) => {
    const workerIdx = Math.min(
      ...worker.states.map(resolveStateIndex)
    );
    let status = "pending";
    if (worker.states.includes(currentState)) {
      status = "active";
    } else if (workerIdx < currentIdx) {
      status = "done";
    }
    const li = document.createElement("li");
    const name = document.createElement("span");
    name.className = "worker-name";
    name.textContent = worker.label;

    const state = document.createElement("span");
    state.className = "worker-state";
    if (status === "active") state.classList.add("active");
    if (status === "done") state.classList.add("done");
    if (loopback && workerIdx > currentIdx) state.classList.add("loopback");
    state.textContent = status;

    li.appendChild(name);
    li.appendChild(state);
    workerList.appendChild(li);
  });
}

async function refreshSessionState() {
  if (!sessionId) return;
  try {
    const res = await fetch(`${BACKEND_URL}/api/chat/session/${encodeURIComponent(sessionId)}`);
    if (!res.ok) return;
    const data = await res.json();
    const currentState = data?.current_state;
    updateBadges(sessionId, currentState || null);
    renderWorkers(currentState, data?.state_history || []);

    // Show download link when decision PDF exists
    if (currentState === "COMPLETED" || currentState === "DECISION") {
      showDownloadLink();
    }
  } catch {
    // Ignore refresh errors
  }
}

// ---------- Extracted-info box ----------

function renderExtractedBox(docType, extracted) {
  if (!extracted || !Object.keys(extracted).length) return;

  // Merge into cumulative data keyed by docType
  allExtracted[docType] = extracted;

  // Render all accumulated data
  extractedItems.innerHTML = "";
  for (const [dtype, fields] of Object.entries(allExtracted)) {
    const header = document.createElement("div");
    header.className = "extracted-key";
    header.style.gridColumn = "1 / -1";
    header.style.fontWeight = "700";
    header.style.color = "var(--accent)";
    header.style.marginTop = "4px";
    header.textContent = dtype.replace(/_/g, " ").toUpperCase();
    extractedItems.appendChild(header);

    for (const [k, v] of Object.entries(fields)) {
      const row = document.createElement("div");
      row.className = "extracted-row";
      const keySpan = document.createElement("span");
      keySpan.className = "extracted-key";
      keySpan.textContent = k.replace(/_/g, " ") + ":";
      const valSpan = document.createElement("span");
      valSpan.className = "extracted-val";
      valSpan.textContent = v;
      row.appendChild(keySpan);
      row.appendChild(valSpan);
      extractedItems.appendChild(row);
    }
  }
  extractedBox.classList.remove("hide");
}

// ---------- Download link ----------

function showDownloadLink() {
  if (!sessionId || !downloadBox || !downloadLink) return;
  downloadLink.href = `${BACKEND_URL}/api/documents/download/${encodeURIComponent(sessionId)}`;
  downloadBox.classList.remove("hide");
}

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = role === "ai" ? "wrapper ai" : "wrapper user";

  const bubble = document.createElement("div");
  bubble.className = "chat";
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  chatContainer.appendChild(wrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setLoading(isLoading) {
  loadingIndicator.classList.toggle("hide", !isLoading);
  if (isLoading) loadingIndicator.textContent = "TIA is typing…";
}

function handleStageChange(stage) {
  if (!stage || stage === lastStage) return;
  lastStage = stage;

  if ((stage === "NEED_DOCS" || stage === "DOC_UPLOAD") && !uploadHintShown) {
    addMessage("ai", "You can upload your documents using the panel above. Select the document type and click Upload.");
    uploadHintShown = true;
  }
}

// ---------- Chat ----------

function withTimeout(ms) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, cancel: () => clearTimeout(timer) };
}

async function readResponse(res) {
  const text = await res.text();
  if (!text) return { raw: "", json: null };
  try {
    return { raw: text, json: JSON.parse(text) };
  } catch {
    return { raw: text, json: null };
  }
}

async function send() {
  const text = msgInput.value.trim();
  if (!text) return;

  msgInput.value = "";
  addMessage("user", text);
  setLoading(true);

  if (!sessionId) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/chat/new-session`, { method: "POST" });
      const data = await res.json();
      if (res.ok && data?.session_id) {
        sessionId = data.session_id;
        updateBadges(sessionId, null);
      }
    } catch {
      // If session creation fails, fallback to backend auto-create by omitting session_id.
    }
  }

  const t = withTimeout(12000);
  try {
    const res = await fetch(`${BACKEND_URL}/api/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId || undefined,
        message: text
      }),
      signal: t.signal,
    });

    const parsed = await readResponse(res);
    const data = parsed.json;

    if (!res.ok) {
      const detail = data?.detail || parsed.raw || `Request failed (HTTP ${res.status}).`;
      addMessage("ai", String(detail));
      return;
    }

    const reply = data?.response ?? data?.reply;
    const stage = data?.current_state ?? data?.stage;
    sessionId = data?.session_id || sessionId || "default";
    updateBadges(sessionId, stage);
    renderWorkers(stage);
    handleStageChange(stage);
    addMessage("ai", reply ? String(reply) : "(Empty response from backend)");

    // Show download when loan journey completes
    if (stage === "COMPLETED" || stage === "DECISION") {
      showDownloadLink();
    }

    refreshSessionState();

  } catch (e) {
    const msg = e?.name === "AbortError" ? "Request timed out. Is the backend running?" : (e?.message || String(e));
    addMessage("ai", `Request error: ${msg}`);
  } finally {
    t.cancel();
    setLoading(false);
  }
}

document.getElementById("send_btn").onclick = send;
msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

// ---------- Upload ----------

document.getElementById("docForm").onsubmit = async (e) => {
  e.preventDefault();

  if (!sessionId) {
    statusText.textContent = "Creating a session…";
    try {
      const res = await fetch(`${BACKEND_URL}/api/chat/new-session`, { method: "POST" });
      const data = await res.json();
      if (res.ok && data?.session_id) {
        sessionId = data.session_id;
        updateBadges(sessionId, null);
      } else {
        statusText.textContent = "Start the chat first to create a session.";
        return;
      }
    } catch {
      statusText.textContent = "Start the chat first to create a session.";
      return;
    }
  }

  const fileInput = document.getElementById("doc");

  if (!fileInput.files.length) {
    statusText.textContent = "Select a file first.";
    return;
  }

  const fd = new FormData();
  fd.append("file", fileInput.files[0]);

  const docType = document.getElementById("docType").value;

  statusText.textContent = "Uploading…";

  try {
    const res = await fetch(
      `${BACKEND_URL}/api/documents/upload?session_id=${encodeURIComponent(sessionId)}&doc_type=${encodeURIComponent(docType)}`,
      {
        method: "POST",
        body: fd
      }
    );

    const parsed = await readResponse(res);
    const data = parsed.json || {};

    if (!res.ok) {
      statusText.textContent = data.detail || parsed.raw || "Upload failed.";
      return;
    }

    if (data.status === "LOW_CONFIDENCE") {
      statusText.textContent = `Low confidence (${data.confidence}). Please re-upload.`;
      addMessage("ai", data.message || "Document unclear. Please re-upload.");
      return;
    }

    if (data.status && data.status !== "SUCCESS") {
      statusText.textContent = data.message || "Upload failed.";
      return;
    }

    statusText.textContent = `✓ Upload successful (confidence: ${(data.confidence || 0).toFixed(2)}).`;
    let msg = data.message || "Document received and parsed.";
    const extracted = data.extracted_data || {};
    if (Object.keys(extracted).length) {
      const items = Object.entries(extracted)
        .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)
        .join(", ");
      msg += `\nExtracted: ${items}`;
    }
    addMessage("ai", msg);
    renderExtractedBox(docType, extracted);
    updateBadges(sessionId, "DOC_RECEIVED");
    refreshSessionState();

  } catch (e) {
    statusText.textContent = "Upload error.";
  }
};

// frontend/app.js

// Adjust this if your backend is on a different host/port
const BACKEND_URL = "http://127.0.0.1:5000";

const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Simple session id for now (Phase 1: static)
const SESSION_ID = "demo-session-001";

function appendMessage(text, sender = "bot") {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message", sender);
  msgDiv.textContent = text;
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // Show user message
  appendMessage(text, "user");
  userInput.value = "";
  userInput.focus();

  try {
    const response = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: text,
        session_id: SESSION_ID,
      }),
    });

    if (!response.ok) {
      appendMessage("Error: unable to reach server", "bot");
      return;
    }

    const data = await response.json();
    appendMessage(data.reply, "bot");
  } catch (err) {
    console.error(err);
    appendMessage("Error: network issue", "bot");
  }
}

// Event listeners
sendBtn.addEventListener("click", sendMessage);

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});

// Initial bot greeting
appendMessage("Hello! I am TIA-Sales (Phase 1). I will echo whatever you say.");

const audienceEl = document.getElementById("audience");
const taskEl = document.getElementById("task");
const promptEl = document.getElementById("prompt");
const formEl = document.getElementById("chatForm");
const messagesEl = document.getElementById("messages");
const sendBtnEl = document.getElementById("sendBtn");
const sampleBtnEl = document.getElementById("sampleBtn");
const templateEl = document.getElementById("messageTemplate");
const pageSite = document.body.dataset.site || "hub";
const defaultAudience = document.body.dataset.defaultAudience || "auto";

const taskOptions = {
  auto: [{ value: "auto", label: "Auto select" }],
  buyer: [
    { value: "auto", label: "Auto select" },
    { value: "search", label: "Search ads" },
    { value: "explain", label: "Explain match" },
  ],
  seller: [
    { value: "auto", label: "Auto select" },
    { value: "billing", label: "Billing" },
    { value: "ad-ops", label: "Ad lookup" },
    { value: "support", label: "Support" },
  ],
  qa: [{ value: "auto", label: "Auto select" }],
};

const samplePrompts = {
  auto: "Find video ads for cat furniture.",
  buyer: "Find video ads for cat furniture.",
  seller: "Check billing status for seller 0d162d0e-83ca-474d-a17c-8616475d4e99.",
  qa: "Run a quick validation of the MCP tool wiring for the buyer flow.",
};

const introMessages = {
  hub: "Choose Buyer, Seller, or Auto route, then type a request in natural language.",
  buyer: "Ask for ad discovery help here. This page stays in buyer mode.",
  seller: "Ask for billing, ad lookup, or support help here. This page stays in seller mode.",
};

function updateTaskOptions() {
  const audience = audienceEl.value;
  const options = taskOptions[audience] || taskOptions.auto;
  taskEl.innerHTML = "";
  for (const option of options) {
    const node = document.createElement("option");
    node.value = option.value;
    node.textContent = option.label;
    taskEl.appendChild(node);
  }
}

function resolveEndpoint(audience, task) {
  if (audience === "buyer" && task === "search") {
    return pageSite === "buyer" ? "/agent/buyer/video-search" : "/agent/buyer/search";
  }
  if (audience === "buyer" && task === "explain") {
    return "/agent/buyer/explain";
  }
  if (audience === "seller" && task === "billing") {
    return "/agent/seller/billing";
  }
  if (audience === "seller" && task === "ad-ops") {
    return "/agent/seller/ad-ops";
  }
  if (audience === "seller" && task === "support") {
    return "/agent/seller/support";
  }
  if (audience === "qa") {
    return "/agent/qa";
  }
  return "/agent/run";
}

function appendMessage(kind, title, body, toolResults) {
  const fragment = templateEl.content.cloneNode(true);
  const root = fragment.querySelector(".message");
  const meta = fragment.querySelector(".message-meta");
  const bodyEl = fragment.querySelector(".message-body");

  root.classList.add(kind);
  meta.textContent = title;
  bodyEl.textContent = body;

  if (toolResults && toolResults.length) {
    const tools = document.createElement("div");
    tools.className = "tool-summary";
    const names = toolResults
      .map((item) => item.tool_name || item.name || "tool")
      .filter(Boolean)
      .join(", ");
    tools.textContent = `Tools used: ${names}`;
    root.appendChild(tools);
  }

  messagesEl.appendChild(fragment);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function loadSample() {
  promptEl.value = samplePrompts[audienceEl.value] || samplePrompts.auto;
  promptEl.focus();
}

function loadQuickPrompt(prompt) {
  promptEl.value = prompt;
  promptEl.focus();
}

async function submitPrompt(event) {
  event.preventDefault();

  const prompt = promptEl.value.trim();
  if (!prompt) {
    return;
  }

  const audience = audienceEl.value;
  const task = taskEl.value;
  const endpoint = resolveEndpoint(audience, task);

  appendMessage("user", `${audience.toUpperCase()} USER`, prompt);
  promptEl.value = "";
  sendBtnEl.disabled = true;
  sendBtnEl.textContent = "Thinking...";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    });

    const payload = await response.json();
    if (!response.ok || payload.error) {
      appendMessage(
        "error",
        "AGENT ERROR",
        payload.error || `Request failed with status ${response.status}.`,
        payload.tool_results,
      );
      return;
    }

    const domain = payload.domain || "auto";
    const specialist = payload.specialist || "router";
    appendMessage(
      "assistant",
      `${domain.toUpperCase()} | ${specialist}`,
      payload.response || "No response returned.",
      payload.tool_results,
    );
  } catch (error) {
    appendMessage(
      "error",
      "NETWORK ERROR",
      error instanceof Error ? error.message : "Unknown error",
    );
  } finally {
    sendBtnEl.disabled = false;
    sendBtnEl.textContent = "Send";
    promptEl.focus();
  }
}

if (audienceEl) {
  audienceEl.value = defaultAudience;
  audienceEl.addEventListener("change", updateTaskOptions);
}
if (sampleBtnEl) {
  sampleBtnEl.addEventListener("click", loadSample);
}
if (formEl) {
  formEl.addEventListener("submit", submitPrompt);
}

for (const button of document.querySelectorAll(".quick-chip")) {
  button.addEventListener("click", () => loadQuickPrompt(button.dataset.prompt || ""));
}

updateTaskOptions();
appendMessage("assistant", "SYSTEM", introMessages[pageSite] || introMessages.hub);

type Sender = "user" | "assistant";

type KnowledgeEntry = {
  id: string;
  thread_id: string;
  outcome: string;
  created_at: string;
  reflection: string;
  embedding_dimensions: number;
  embedding_preview: number[];
};

type KnowledgeMessage =
  | { type: "snapshot"; data: KnowledgeEntry[] }
  | { type: "update"; data: KnowledgeEntry }
  | { type: "delete"; data: { id: string } };

// Chat panel references
const chatLog = document.getElementById("chat-log") as HTMLDivElement | null;
const chatForm = document.getElementById("chat-form") as HTMLFormElement | null;
const userInput = document.getElementById("user-input") as HTMLInputElement | null;

// Knowledge base panel references
const knowledgeFeed = document.getElementById("knowledge-feed") as HTMLDivElement | null;
const knowledgeStatus = document.getElementById("knowledge-status") as HTMLSpanElement | null;

const knowledgeState = new Map<string, KnowledgeEntry>();
let knowledgeSocket: WebSocket | null = null;
let reconnectTimer: number | undefined;

function addMessage(sender: Sender, text: string): void {
  if (!chatLog) {
    return;
  }

  const messageElement = document.createElement("div");
  messageElement.classList.add("message", sender);

  const paragraphElement = document.createElement("p");
  paragraphElement.textContent = text;
  messageElement.appendChild(paragraphElement);

  chatLog.appendChild(messageElement);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setKnowledgeStatus(
  state: "connecting" | "connected" | "error" | "closed"
): void {
  if (!knowledgeStatus) {
    return;
  }

  knowledgeStatus.classList.remove(
    "status--connected",
    "status--error",
    "status--closed"
  );

  switch (state) {
    case "connecting":
      knowledgeStatus.textContent = "Connecting...";
      break;
    case "connected":
      knowledgeStatus.textContent = "Connected";
      knowledgeStatus.classList.add("status--connected");
      break;
    case "error":
      knowledgeStatus.textContent = "Error";
      knowledgeStatus.classList.add("status--error");
      break;
    case "closed":
      knowledgeStatus.textContent = "Disconnected";
      knowledgeStatus.classList.add("status--closed");
      break;
  }
}

function formatEmbeddingPreview(values: number[]): string {
  if (!values || values.length === 0) {
    return "n/a";
  }

  const formatted = values.map((value) =>
    Number.isFinite(value) ? value.toFixed(4) : String(value)
  );
  return `[${formatted.join(", ")}]`;
}

function createKnowledgeEntry(entry: KnowledgeEntry): HTMLElement {
  const container = document.createElement("article");
  container.className = "knowledge-entry";

  const header = document.createElement("div");
  header.className = "knowledge-entry__header";

  const title = document.createElement("h3");
  title.textContent = entry.thread_id;
  header.appendChild(title);

  const badge = document.createElement("span");
  badge.className = `tag tag--${entry.outcome}`;
  badge.textContent = entry.outcome.toUpperCase();
  header.appendChild(badge);

  const timestamp = document.createElement("time");
  timestamp.dateTime = entry.created_at;
  const parsedDate = new Date(entry.created_at);
  timestamp.textContent = Number.isNaN(parsedDate.getTime())
    ? entry.created_at
    : parsedDate.toLocaleString();
  header.appendChild(timestamp);

  const body = document.createElement("div");
  body.className = "knowledge-entry__body";

  const reflection = document.createElement("p");
  reflection.textContent = entry.reflection || "(empty reflection)";
  body.appendChild(reflection);

  const meta = document.createElement("dl");
  meta.className = "knowledge-entry__meta";

  const dimsLabel = document.createElement("dt");
  dimsLabel.textContent = "Embedding dims";
  const dimsValue = document.createElement("dd");
  dimsValue.textContent = `${entry.embedding_dimensions}`;

  const previewLabel = document.createElement("dt");
  previewLabel.textContent = "Preview";
  const previewValue = document.createElement("dd");
  previewValue.textContent = formatEmbeddingPreview(entry.embedding_preview);

  meta.append(dimsLabel, dimsValue, previewLabel, previewValue);
  body.appendChild(meta);

  container.append(header, body);
  return container;
}

function renderKnowledgeFeed(): void {
  if (!knowledgeFeed) {
    return;
  }

  knowledgeFeed.innerHTML = "";
  const entries = Array.from(knowledgeState.values()).sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  if (entries.length === 0) {
    knowledgeFeed.classList.add("empty");
    const placeholder = document.createElement("p");
    placeholder.className = "placeholder";
    placeholder.textContent = "Waiting for reflections...";
    knowledgeFeed.appendChild(placeholder);
    return;
  }

  knowledgeFeed.classList.remove("empty");
  for (const entry of entries) {
    knowledgeFeed.appendChild(createKnowledgeEntry(entry));
  }
}

function handleKnowledgeMessage(event: MessageEvent<string>): void {
  let payload: KnowledgeMessage | null = null;
  try {
    payload = JSON.parse(event.data) as KnowledgeMessage;
  } catch (error) {
    console.warn("Failed to parse knowledge base message", error);
    return;
  }

  if (!payload) {
    return;
  }

  switch (payload.type) {
    case "snapshot":
      knowledgeState.clear();
      if (Array.isArray(payload.data)) {
        for (const entry of payload.data) {
          if (entry?.id) {
            knowledgeState.set(entry.id, entry);
          }
        }
      }
      renderKnowledgeFeed();
      break;
    case "update":
      if (payload.data?.id) {
        knowledgeState.set(payload.data.id, payload.data);
        renderKnowledgeFeed();
      }
      break;
    case "delete":
      if (payload.data?.id) {
        knowledgeState.delete(payload.data.id);
        renderKnowledgeFeed();
      }
      break;
    default:
      console.warn("Unknown knowledge base message", payload);
  }
}

function scheduleReconnect(attempt: number): void {
  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
  }
  const cappedAttempt = Math.min(attempt, 6);
  const delay = Math.min(10000, (cappedAttempt + 1) * 1000);
  reconnectTimer = window.setTimeout(() => connectKnowledgeSocket(attempt + 1), delay);
}

function connectKnowledgeSocket(attempt = 0): void {
  if (!knowledgeFeed || !knowledgeStatus) {
    return;
  }

  if (knowledgeSocket) {
    knowledgeSocket.close();
  }

  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = undefined;
  }

  setKnowledgeStatus("connecting");

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const { VITE_KNOWLEDGE_SOCKET_URL, VITE_KNOWLEDGE_SOCKET_PORT } = import.meta
    .env;
  const socketUrl =
    VITE_KNOWLEDGE_SOCKET_URL ||
    `${protocol}://${window.location.hostname}:${
      VITE_KNOWLEDGE_SOCKET_PORT || "8000"
    }/ws/knowledge_base`;

  const socket = new WebSocket(socketUrl);
  knowledgeSocket = socket;

  socket.addEventListener("open", () => {
    if (knowledgeSocket !== socket) {
      return;
    }
    setKnowledgeStatus("connected");
  });

  socket.addEventListener("message", (event) => {
    if (knowledgeSocket !== socket) {
      return;
    }
    handleKnowledgeMessage(event as MessageEvent<string>);
  });

  socket.addEventListener("close", () => {
    if (knowledgeSocket !== socket) {
      return;
    }
    knowledgeSocket = null;
    setKnowledgeStatus("closed");
    scheduleReconnect(attempt + 1);
  });

  socket.addEventListener("error", () => {
    if (knowledgeSocket !== socket) {
      return;
    }
    setKnowledgeStatus("error");
    socket.close();
  });
}

renderKnowledgeFeed();
connectKnowledgeSocket();

if (chatForm && userInput) {
  chatForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const userMessage = userInput.value.trim();
    if (!userMessage) {
      return;
    }

    addMessage("user", userMessage);
    userInput.value = "";

    setTimeout(() => {
      addMessage(
        "assistant",
        `Instruction received: "${userMessage}". Acknowledged. Standby for execution.`
      );
    }, 500);
  });
}

window.addEventListener("beforeunload", () => {
  if (knowledgeSocket) {
    knowledgeSocket.close();
  }
  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
  }
});

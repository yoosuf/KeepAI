import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import type {
  Conversation,
  ConversationSummary,
  ChatMessage,
} from "../types";

const WS_BASE = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/chat`;

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState(
    searchParams.get("system_prompt") || ""
  );
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const [modelName, setModelName] = useState(searchParams.get("model") || "");
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(0.9);
  const [showParams, setShowParams] = useState(false);
  const tokenRef = useRef(localStorage.getItem("keepai_token"));
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const convListRef = useRef<ConversationSummary[]>([]);
  convListRef.current = conversations;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWs = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    const token = tokenRef.current;
    if (!token) return;

    const ws = new WebSocket(`${WS_BASE}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "list_conversations" }));
      if (id) {
        ws.send(JSON.stringify({ type: "get_conversation", conversation_id: parseInt(id) }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case "chat_response":
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: data.response_text },
            ]);
            setLoading(false);
            if (data.conversation_id) {
              ws.send(JSON.stringify({ type: "list_conversations" }));
            }
            break;
          case "conversations":
            setConversations(data.items || []);
            break;
          case "conversation":
            setCurrentConv(data);
            setMessages(
              (data.messages || []).map((m: { role: string; content: string }) => ({
                role: m.role as "user" | "assistant",
                content: m.content,
              }))
            );
            break;
          case "conversation_deleted":
            setConversations((prev) =>
              prev.filter((c) => c.id !== data.conversation_id)
            );
            if (id && parseInt(id) === data.conversation_id) {
              setCurrentConv(null);
              setMessages([]);
              navigate("/chat");
            }
            break;
          case "error":
            alert(data.message);
            setLoading(false);
            break;
        }
      } catch {
        // ignore
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  };

  useEffect(() => {
    connectWs();
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const sendMessage = () => {
    if (!input.trim() || loading || !wsRef.current) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    wsRef.current.send(
      JSON.stringify({
        type: "chat",
        conversation_id: id ? parseInt(id) : undefined,
        message: userMessage,
        model_name: modelName || undefined,
        system_prompt: systemPrompt || undefined,
        temperature,
        top_p: topP,
      })
    );
  };

  const deleteConversation = (convId: number) => {
    if (confirm("Delete this conversation?")) {
      wsRef.current?.send(
        JSON.stringify({ type: "delete_conversation", conversation_id: convId })
      );
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    setCurrentConv(null);
    setMessages([]);
    navigate("/chat");
  };

  return (
    <div className="chat-page">
      {/* Sidebar */}
      <div className="chat-sidebar">
        <div className="chat-sidebar-header">
          <h3>Conversations</h3>
          <button className="btn btn-sm btn-primary" onClick={clearConversation}>
            + New
          </button>
        </div>
        <div className="conv-list">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`conv-item ${id === String(c.id) ? "active" : ""}`}
              onClick={() => navigate(`/chat/${c.id}`)}
            >
              <div className="conv-item-title">{c.title || "Untitled"}</div>
              <div className="conv-item-meta">
                {c.model_name} &middot; {c.message_count} messages
              </div>
              <button
                className="conv-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(c.id);
                }}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="chat-main">
        {/* Controls */}
        <div className="chat-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showSystemPrompt}
              onChange={() => setShowSystemPrompt((v) => !v)}
            />
            System Prompt
          </label>
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => setShowParams((v) => !v)}
          >
            Parameters
          </button>
        </div>

        {showSystemPrompt && (
          <textarea
            className="system-prompt-input"
            placeholder="Optional system prompt..."
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={2}
          />
        )}

        {showParams && (
          <div className="param-row">
            <div className="param-field">
              <label>Model</label>
              <input
                type="text"
                placeholder="llama3"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
              />
            </div>
            <div className="param-field">
              <label>Temperature ({temperature})</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
              />
            </div>
            <div className="param-field">
              <label>Top P ({topP})</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(parseFloat(e.target.value))}
              />
            </div>
          </div>
        )}

        {currentConv && (
          <div className="conv-title-bar">
            Conversation: {currentConv.title || "Untitled"}
          </div>
        )}

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <p>Send a message to start chatting</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message message-${msg.role}`}>
              <div className="message-role">{msg.role}</div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="message message-assistant">
              <div className="message-role">assistant</div>
              <div className="message-content typing">Thinking...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <textarea
            className="chat-input"
            placeholder="Type your message... (Enter to send, Shift+Enter for newline)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            disabled={loading}
          />
          <button
            className="btn btn-primary send-btn"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

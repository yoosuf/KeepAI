import { useEffect, useState } from "react";
import { get, del } from "../api/client";
import type { ConversationSummary } from "../types";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedConv, setExpandedConv] = useState<number | null>(null);
  const [convMessages, setConvMessages] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  const fetchConversations = async () => {
    setLoading(true);
    try {
      const data = await get<ConversationSummary[]>(
        `/conversations?skip=${page * limit}&limit=${limit}`
      );
      setConversations(data);
      setTotal(data.length < limit ? (page * limit) + data.length : (page + 1) * limit + 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [page]);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this conversation?")) return;
    try {
      await del(`/conversations/${id}`);
      fetchConversations();
    } catch (err) {
      console.error(err);
    }
  };

  const handleExpand = async (id: number) => {
    if (expandedConv === id) {
      setExpandedConv(null);
      setConvMessages([]);
      return;
    }
    try {
      const data = await get<{ id: number; title: string; messages: any[] }>(
        `/conversations/${id}`
      );
      setConvMessages(data.messages || []);
      setExpandedConv(id);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExport = async (id: number) => {
    try {
      const data = await get<{ id: number; title: string; messages: any[] }>(
        `/conversations/${id}`
      );
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `conversation-${id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Conversations</h2>
        <a href="/chat" className="btn btn-primary">
          + New Chat
        </a>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : conversations.length === 0 ? (
        <div className="empty-state">
          <p>No conversations yet.</p>
          <a href="/chat" className="btn btn-primary">
            Start a chat
          </a>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Model</th>
                  <th>Messages</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {conversations.map((c) => (
                  <>
                    <tr
                      key={c.id}
                      className="clickable"
                      onClick={() => handleExpand(c.id)}
                    >
                      <td>{c.title || "Untitled"}</td>
                      <td>{c.model_name}</td>
                      <td>{c.message_count}</td>
                      <td>{new Date(c.updated_at).toLocaleString()}</td>
                      <td>
                        <a
                          href={`/chat/${c.id}`}
                          className="btn btn-sm btn-primary"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Open
                        </a>
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExport(c.id);
                          }}
                        >
                          Export
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(c.id);
                          }}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                    {expandedConv === c.id && (
                      <tr key={`${c.id}-messages`}>
                        <td colSpan={5}>
                          <div className="expanded-messages">
                            {convMessages.length === 0 ? (
                              <p>No messages</p>
                            ) : (
                              convMessages.map((m) => (
                                <div
                                  key={m.id}
                                  className={`inline-message inline-message-${m.role}`}
                                >
                                  <strong>{m.role}:</strong>{" "}
                                  {m.content.substring(0, 300)}
                                </div>
                              ))
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span>
                Page {page + 1} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

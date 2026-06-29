import { useState, useEffect } from "react";
import { getPrompts } from "../api/prompts";
import type { Prompt } from "../types";

export default function History() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Prompt | null>(null);
  const limit = 20;

  useEffect(() => {
    setLoading(true);
    getPrompts(skip, limit)
      .then((data) => {
        setPrompts(data.items);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [skip]);

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(skip / limit) + 1;

  return (
    <div className="history-page">
      <h2>Prompt History</h2>

      {loading ? (
        <p>Loading...</p>
      ) : prompts.length === 0 ? (
        <p className="empty-state">No prompts yet. Start a conversation in Chat.</p>
      ) : (
        <div className="history-layout">
          <div className="history-list">
            {prompts.map((p) => (
              <div
                key={p.id}
                className={`history-item ${selected?.id === p.id ? "selected" : ""}`}
                onClick={() => setSelected(p)}
              >
                <div className="history-item-text">{p.prompt_text.slice(0, 100)}</div>
                <div className="history-item-meta">
                  {p.model_name} &middot; {p.processing_time_ms}ms &middot;{" "}
                  {new Date(p.created_at).toLocaleString()}
                </div>
              </div>
            ))}

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  disabled={skip === 0}
                  onClick={() => setSkip(Math.max(0, skip - limit))}
                >
                  Previous
                </button>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  disabled={skip + limit >= total}
                  onClick={() => setSkip(skip + limit)}
                >
                  Next
                </button>
              </div>
            )}
          </div>

          {selected && (
            <div className="history-detail">
              <h3>Prompt</h3>
              <pre className="history-text">{selected.prompt_text}</pre>
              <h3>Response</h3>
              <pre className="history-text">{selected.response_text}</pre>
              <div className="history-detail-meta">
                <div>Model: {selected.model_name}</div>
                <div>Processing time: {selected.processing_time_ms}ms</div>
                <div>Created: {new Date(selected.created_at).toLocaleString()}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

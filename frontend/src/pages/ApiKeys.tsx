import { useEffect, useState } from "react";
import { get, post, del } from "../api/client";
import type { ApiKey, ApiKeyCreateResponse } from "../types";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [error, setError] = useState("");

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const data = await get<ApiKey[]>("/api-keys");
      setKeys(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!newName.trim()) {
      setError("Name is required");
      return;
    }
    try {
      const data = await post<ApiKeyCreateResponse>("/api-keys", {
        name: newName.trim(),
      });
      setCreatedKey(data.full_key);
      setNewName("");
      setShowCreate(false);
      fetchKeys();
    } catch (err: any) {
      setError(err.message || "Failed to create key");
    }
  };

  const handleRevoke = async (id: number) => {
    if (!confirm("Revoke this API key? This cannot be undone.")) return;
    try {
      await del(`/api-keys/${id}`);
      fetchKeys();
    } catch (err) {
      console.error(err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).catch(() => {});
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>API Keys</h2>
        <button
          className="btn btn-primary"
          onClick={() => {
            setShowCreate(true);
            setCreatedKey(null);
          }}
        >
          + Create Key
        </button>
      </div>

      {/* Created key notification */}
      {createdKey && (
        <div className="alert alert-success">
          <strong>Key created!</strong> Copy it now — you won't see it again.
          <div className="key-display">
            <code>{createdKey}</code>
            <button
              className="btn btn-sm btn-secondary"
              onClick={() => copyToClipboard(createdKey)}
            >
              Copy
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <form onSubmit={handleCreate} className="card create-form">
          <h3>New API Key</h3>
          <div className="form-group">
            <label>Key Name</label>
            <input
              type="text"
              placeholder="e.g., Production, CI/CD"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
          </div>
          {error && <p className="error-text">{error}</p>}
          <div className="form-actions">
            <button type="submit" className="btn btn-primary">
              Create
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p>Loading...</p>
      ) : keys.length === 0 ? (
        <div className="empty-state">
          <p>No API keys yet.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Key</th>
                <th>Status</th>
                <th>Last Used</th>
                <th>Created</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id}>
                  <td>{k.name}</td>
                  <td>
                    <code>{k.key_preview}...</code>
                  </td>
                  <td>
                    <span className={`badge ${k.is_active ? "badge-active" : "badge-inactive"}`}>
                      {k.is_active ? "Active" : "Revoked"}
                    </span>
                  </td>
                  <td>
                    {k.last_used_at
                      ? new Date(k.last_used_at).toLocaleString()
                      : "Never"}
                  </td>
                  <td>{new Date(k.created_at).toLocaleString()}</td>
                  <td>
                    {k.expires_at
                      ? new Date(k.expires_at).toLocaleString()
                      : "Never"}
                  </td>
                  <td>
                    {k.is_active && (
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleRevoke(k.id)}
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

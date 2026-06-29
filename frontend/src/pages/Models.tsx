import { useState, useEffect, type FormEvent } from "react";
import { listModels, pullModel, deleteModel } from "../api/models";
import type { ModelInfo } from "../types";

export default function Models() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pullName, setPullName] = useState("");
  const [pulling, setPulling] = useState(false);
  const [pullStatus, setPullStatus] = useState("");

  function fetchModels() {
    setLoading(true);
    setError("");
    listModels()
      .then((data) => setModels(data.models || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchModels();
  }, []);

  async function handlePull(e: FormEvent) {
    e.preventDefault();
    if (!pullName.trim()) return;
    setPulling(true);
    setPullStatus("");
    try {
      const result = await pullModel(pullName.trim());
      setPullStatus(result.status);
      setPullName("");
      fetchModels();
    } catch (err) {
      setPullStatus(`Error: ${err instanceof Error ? err.message : "Pull failed"}`);
    } finally {
      setPulling(false);
    }
  }

  async function handleDelete(name: string) {
    if (!confirm(`Delete model "${name}"?`)) return;
    try {
      await deleteModel(name);
      fetchModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  function formatBytes(bytes: number): string {
    const gb = bytes / 1_000_000_000;
    return `${gb.toFixed(2)} GB`;
  }

  return (
    <div className="models-page">
      <h2>Models</h2>

      <form onSubmit={handlePull} className="pull-form">
        <input
          type="text"
          value={pullName}
          onChange={(e) => setPullName(e.target.value)}
          placeholder="Pull a model (e.g. llama3, mistral)..."
          disabled={pulling}
        />
        <button type="submit" className="btn-primary" disabled={pulling || !pullName.trim()}>
          {pulling ? "Pulling..." : "Pull"}
        </button>
      </form>
      {pullStatus && <div className="alert alert-info">{pullStatus}</div>}

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p>Loading models...</p>
      ) : models.length === 0 ? (
        <p className="empty-state">
          No models available. Pull one using the form above.
        </p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Size</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.name}>
                <td>{m.name}</td>
                <td>{formatBytes(m.size)}</td>
                <td>
                  <button onClick={() => handleDelete(m.name)} className="btn-danger-sm">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

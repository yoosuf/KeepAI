import { useState, useEffect } from "react";
import { getAllPrompts } from "../api/admin";
import type { Prompt } from "../types";

export default function AdminPrompts() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getAllPrompts()
      .then(setPrompts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div className="admin-page">
      <h2>All Prompts</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>User ID</th>
            <th>Prompt</th>
            <th>Model</th>
            <th>Time</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {prompts.map((p) => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.user_id ?? "N/A"}</td>
              <td className="cell-preview">{p.prompt_text.slice(0, 80)}</td>
              <td>{p.model_name}</td>
              <td>{p.processing_time_ms}ms</td>
              <td>{new Date(p.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { useState, type FormEvent } from "react";
import { createPrompt, extractInvoice } from "../api/prompts";

type Tab = "prompt" | "invoice";

export default function Playground() {
  const [tab, setTab] = useState<Tab>("prompt");
  const [promptText, setPromptText] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState("0.7");
  const [modelName, setModelName] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setResponse("");
    setLoading(true);

    try {
      if (tab === "prompt") {
        const result = await createPrompt(promptText, {
          systemPrompt: systemPrompt || undefined,
          temperature: temperature ? parseFloat(temperature) : undefined,
        });
        setResponse(result.response_text || "(no response)");
      } else if (tab === "invoice") {
        const result = await extractInvoice(promptText, modelName || undefined);
        setResponse(JSON.stringify(result, null, 2));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="playground-page">
      <h2>API Playground</h2>

      <div className="tabs">
        <button
          className={`tab ${tab === "prompt" ? "active" : ""}`}
          onClick={() => setTab("prompt")}
        >
          Prompt
        </button>
        <button
          className={`tab ${tab === "invoice" ? "active" : ""}`}
          onClick={() => setTab("invoice")}
        >
          Invoice Extraction
        </button>
      </div>

      <form onSubmit={handleSubmit} className="playground-form">
        {tab === "prompt" && (
          <>
            <div className="form-group">
              <label htmlFor="prompt-text">Prompt</label>
              <textarea
                id="prompt-text"
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                rows={5}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="system-prompt">System Prompt (optional)</label>
              <textarea
                id="system-prompt"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={2}
              />
            </div>
            <div className="form-group-inline">
              <div className="form-group">
                <label htmlFor="temperature">Temperature</label>
                <input
                  id="temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                />
              </div>
            </div>
          </>
        )}

        {tab === "invoice" && (
          <>
            <div className="form-group">
              <label htmlFor="invoice-text">Invoice Text</label>
              <textarea
                id="invoice-text"
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                rows={5}
                required
                placeholder="Paste invoice text here..."
              />
            </div>
            <div className="form-group">
              <label htmlFor="invoice-model">Model (optional)</label>
              <input
                id="invoice-model"
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="llama3"
              />
            </div>
          </>
        )}

        <button type="submit" className="btn-primary" disabled={loading || !promptText.trim()}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {response && (
        <div className="playground-response">
          <h3>Response</h3>
          <pre>{response}</pre>
        </div>
      )}
    </div>
  );
}

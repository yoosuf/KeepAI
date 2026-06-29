import { useEffect, useState } from "react";
import { get, post, del, upload } from "../api/client";
import type { Document, SearchResult } from "../types";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"list" | "upload" | "search">("list");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const data = await get<Document[]>("/documents");
      setDocs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      await upload<Document>("/documents/upload", formData);
      setFile(null);
      setTab("list");
      fetchDocs();
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this document?")) return;
    try {
      await del(`/documents/${id}`);
      fetchDocs();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await get<SearchResult[]>(
        `/documents/search?q=${encodeURIComponent(searchQuery)}&top_k=10`
      );
      setSearchResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleQuery = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await post<{ response: string; results: SearchResult[] }>(
        "/documents/query",
        { query: searchQuery }
      );
      setSearchResults(data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const formatSize = (bytes: number | null): string => {
    if (!bytes) return "Unknown";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Documents</h2>
        <div className="tab-bar">
          <button
            className={`tab ${tab === "list" ? "active" : ""}`}
            onClick={() => setTab("list")}
          >
            All Documents
          </button>
          <button
            className={`tab ${tab === "upload" ? "active" : ""}`}
            onClick={() => setTab("upload")}
          >
            Upload
          </button>
          <button
            className={`tab ${tab === "search" ? "active" : ""}`}
            onClick={() => setTab("search")}
          >
            Search & Query
          </button>
        </div>
      </div>

      {tab === "upload" && (
        <form onSubmit={handleUpload} className="card upload-form">
          <h3>Upload Document</h3>
          <div className="form-group">
            <label>File (txt, pdf, docx, md)</label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              accept=".txt,.pdf,.docx,.md,.csv,.json"
            />
          </div>
          {error && <p className="error-text">{error}</p>}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={uploading || !file}
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>
      )}

      {tab === "search" && (
        <div className="card search-form">
          <h3>Search Documents</h3>
          <form onSubmit={handleSearch} className="search-row">
            <input
              type="text"
              placeholder="Search query..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={searching}>
              {searching ? "Searching..." : "Search"}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleQuery}
              disabled={searching}
            >
              Query LLM
            </button>
          </form>
          {searchResults.length > 0 && (
            <div className="search-results">
              <h4>Results</h4>
              {searchResults.map((r, i) => (
                <div key={i} className="search-result-item">
                  <div className="search-result-meta">
                    <strong>{r.filename}</strong> - Score: {r.score.toFixed(2)}
                  </div>
                  <p className="search-result-content">{r.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "list" && (
        <>
          {loading ? (
            <p>Loading...</p>
          ) : docs.length === 0 ? (
            <div className="empty-state">
              <p>No documents uploaded.</p>
              <button className="btn btn-primary" onClick={() => setTab("upload")}>
                Upload a document
              </button>
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map((d) => (
                    <tr key={d.id}>
                      <td>{d.filename}</td>
                      <td>{d.content_type || "Unknown"}</td>
                      <td>{formatSize(d.file_size)}</td>
                      <td>{new Date(d.created_at).toLocaleString()}</td>
                      <td>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(d.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { get } from "../api/client";
import type { UsageStats, UserUsageStats } from "../types";

export default function AnalyticsPage() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [userStats, setUserStats] = useState<UserUsageStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<"7d" | "30d" | "all">("7d");
  const [adminView, setAdminView] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const params = period === "all" ? "" : `?days=${period === "7d" ? 7 : 30}`;
      const data = await get<UsageStats>(`/analytics/stats${params}`);
      setStats(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserStats = async () => {
    try {
      const data = await get<UserUsageStats[]>("/analytics/admin/user-stats");
      setUserStats(data);
    } catch (err) {
      // May be 403 if not admin
    }
  };

  useEffect(() => {
    fetchStats();
  }, [period]);

  useEffect(() => {
    if (adminView) {
      fetchUserStats();
    }
  }, [adminView]);

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Usage Analytics</h2>
        <div className="tab-bar">
          <button
            className={`tab ${period === "7d" ? "active" : ""}`}
            onClick={() => setPeriod("7d")}
          >
            7 Days
          </button>
          <button
            className={`tab ${period === "30d" ? "active" : ""}`}
            onClick={() => setPeriod("30d")}
          >
            30 Days
          </button>
          <button
            className={`tab ${period === "all" ? "active" : ""}`}
            onClick={() => setPeriod("all")}
          >
            All Time
          </button>
          <button
            className={`tab ${adminView ? "active" : ""}`}
            onClick={() => setAdminView((v) => !v)}
          >
            Admin View
          </button>
        </div>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : !stats ? (
        <div className="empty-state">
          <p>No data yet. Start using the API to see analytics.</p>
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.total_requests}</div>
              <div className="stat-label">Total Requests</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.requests_today}</div>
              <div className="stat-label">Today</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {(stats.avg_processing_time_ms / 1000).toFixed(2)}s
              </div>
              <div className="stat-label">Avg Response Time</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {(stats.total_processing_time_ms / 1000).toFixed(1)}s
              </div>
              <div className="stat-label">Total Processing Time</div>
            </div>
          </div>

          {/* By model */}
          <div className="card">
            <h3>Requests by Model</h3>
            <div className="bar-chart">
              {Object.entries(stats.requests_by_model || {}).map(
                ([model, count]) => (
                  <div key={model} className="bar-row">
                    <span className="bar-label">{model}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${Math.min(
                            100,
                            (count / stats.total_requests) * 100
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="bar-value">{count}</span>
                  </div>
                )
              )}
            </div>
          </div>

          {/* By action */}
          <div className="card">
            <h3>Requests by Action</h3>
            <div className="bar-chart">
              {Object.entries(stats.requests_by_action || {}).map(
                ([action, count]) => (
                  <div key={action} className="bar-row">
                    <span className="bar-label">{action}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${Math.min(
                            100,
                            (count / stats.total_requests) * 100
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="bar-value">{count}</span>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Admin: per-user stats */}
          {adminView && (
            <div className="card">
              <h3>Per-User Usage</h3>
              {userStats.length === 0 ? (
                <p>No data or insufficient permissions.</p>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>User ID</th>
                        <th>Email</th>
                        <th>Requests</th>
                        <th>Total Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {userStats.map((u) => (
                        <tr key={u.user_id}>
                          <td>{u.user_id}</td>
                          <td>{u.email}</td>
                          <td>{u.total_requests}</td>
                          <td>{(u.total_processing_time_ms / 1000).toFixed(1)}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

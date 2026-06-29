import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-logo">KeepAI</h1>
          <span className="sidebar-subtitle">Local LLM Platform</span>
        </div>

        <div className="sidebar-nav">
          <span className="nav-section">Core</span>
          <NavLink to="/chat" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Chat
          </NavLink>
          <NavLink to="/conversations" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Conversations
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            History
          </NavLink>

          <span className="nav-section">Tools</span>
          <NavLink to="/models" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Models
          </NavLink>
          <NavLink to="/playground" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Playground
          </NavLink>
          <NavLink to="/documents" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Documents
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Analytics
          </NavLink>
          <NavLink to="/api-keys" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            API Keys
          </NavLink>

          <span className="nav-section">Admin</span>
          <NavLink to="/admin/users" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            Users
          </NavLink>
          <NavLink to="/admin/prompts" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
            All Prompts
          </NavLink>
        </div>

        <div className="sidebar-footer">
          <span className="user-email">{user?.email}</span>
          <button onClick={logout} className="btn-text">
            Log out
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

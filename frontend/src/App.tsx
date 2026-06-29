import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import History from "./pages/History";
import AdminUsers from "./pages/AdminUsers";
import AdminPrompts from "./pages/AdminPrompts";
import Models from "./pages/Models";
import Playground from "./pages/Playground";
import Conversations from "./pages/Conversations";
import ApiKeys from "./pages/ApiKeys";
import Documents from "./pages/Documents";
import Analytics from "./pages/Analytics";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/chat" element={<Chat />} />
              <Route path="/chat/:id" element={<Chat />} />
              <Route path="/history" element={<History />} />
              <Route path="/models" element={<Models />} />
              <Route path="/playground" element={<Playground />} />
              <Route path="/conversations" element={<Conversations />} />
              <Route path="/api-keys" element={<ApiKeys />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/admin/users" element={<AdminUsers />} />
              <Route path="/admin/prompts" element={<AdminPrompts />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";

import { AuthProvider, RequireAuth, useAuth } from "./auth/AuthContext";
import AnalysisPage from "./pages/Analysis";
import Chat from "./pages/Chat";
import History from "./pages/History";
import Login from "./pages/Login";
import Upload from "./pages/Upload";

function Shell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"}`;
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
          <Link to="/" className="font-semibold">
            <span className="text-sky-400">▍</span> AI Log Analyzer
          </Link>
          <nav className="flex gap-1">
            <NavLink to="/" end className={navClass}>
              Analyze
            </NavLink>
            <NavLink to="/history" className={navClass}>
              History
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm text-slate-400">
            <span>{user?.email}</span>
            <button onClick={logout} className="text-slate-500 hover:text-white">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <RequireAuth>
                <Shell>
                  <Routes>
                    <Route path="/" element={<Upload />} />
                    <Route path="/analyses/:id" element={<AnalysisPage />} />
                    <Route path="/logs/:logFileId/chat" element={<Chat />} />
                    <Route path="/history" element={<History />} />
                  </Routes>
                </Shell>
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

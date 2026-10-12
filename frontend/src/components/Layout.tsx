import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Users, Search, RefreshCw, LogOut, Database } from "lucide-react";
import { triggerRefresh, type IngestResponse } from "../api/client";
import { useAuth } from "../context/auth-context";
import { useState } from "react";

const NAV = [
  { to: "/", label: "Dashboard", icon: BarChart3 },
  { to: "/workers", label: "Workers", icon: Users },
  { to: "/query", label: "Skill Query", icon: Search },
  { to: "/sources", label: "Data Sources", icon: Database },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [refreshing, setRefreshing] = useState(false);
  const [msg, setMsg] = useState("");

  const handleRefresh = async () => {
    setRefreshing(true);
    setMsg("");
    try {
      const res: IngestResponse = await triggerRefresh();
      setMsg(res.message);
    } catch {
      setMsg("Refresh failed");
    } finally {
      setRefreshing(false);
      setTimeout(() => setMsg(""), 5000);
    }
  };

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-slate-900 text-white flex flex-col shrink-0">
        <div className="p-5 border-b border-slate-700">
          <h1 className="text-lg font-bold tracking-tight">CV Parser</h1>
          <p className="text-xs text-slate-400 mt-0.5">Skill Analysis Platform</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-slate-700 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-700 space-y-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh Data"}
          </button>
          {msg && <p className="text-xs text-slate-400 px-3">{msg}</p>}
        </div>
        {user && (
          <div className="p-3 border-t border-slate-700">
            <div className="flex items-center gap-3 px-2 mb-2">
              {user.picture ? (
                <img
                  src={user.picture}
                  alt=""
                  className="w-8 h-8 rounded-full shrink-0"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold shrink-0">
                  {user.name?.[0] ?? "?"}
                </div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user.name}
                </p>
                <p className="text-xs text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <LogOut size={16} />
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-[1400px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

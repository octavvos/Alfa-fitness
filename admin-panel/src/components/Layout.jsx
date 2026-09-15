import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/scanner", label: "Skanerlash" },
  { to: "/memberships", label: "Abonementlar" },
  { to: "/clients", label: "Mijozlar" },
  { to: "/plans", label: "Tariflar" },
  { to: "/visits", label: "Tashriflar" },
  { to: "/access-logs", label: "Kirish jurnali" },
];

const titles = {
  "/": "Dashboard",
  "/scanner": "Skanerlash",
  "/memberships": "Abonementlar",
  "/clients": "Mijozlar",
  "/plans": "Abonement turlari",
  "/visits": "Tashriflar",
  "/access-logs": "Kirish jurnali",
};

export default function Layout() {
  const { user, logout } = useAuth();
  const path = useLocation().pathname;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          Fitness<span>Klub</span>
        </div>
        <nav>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="who">{user?.username}</div>
          <button className="logout-btn" onClick={logout}>
            Chiqish
          </button>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <h1>{titles[path] ?? "Fitness klub"}</h1>
        </header>
        <div className="content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

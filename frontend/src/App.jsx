import { useState } from "react";
import "./App.css";

import Dashboard from "./pages/Dashboard";
import Models from "./pages/Models";
import Comparison2025 from "./pages/Comparison2025";
import About from "./pages/About";

export default function App() {
  const [page, setPage] = useState("dashboard");

  const MenuItem = ({ id, icon, text }) => (
    <div
      className={`sidebar-item ${page === id ? "active" : ""}`}
      onClick={() => setPage(id)}
    >
      <span>{icon}</span>
      <span>{text}</span>
    </div>
  );

  return (
    <div className="app-layout">

      <aside className="sidebar">

        <div className="logo">

          <h2>📈 FinSightAI</h2>

          <p>Financial Intelligence</p>

        </div>

        <MenuItem
          id="dashboard"
          icon="📊"
          text="Dashboard"
        />

        <MenuItem
          id="models"
          icon="🤖"
          text="AI Models"
        />

        <MenuItem
          id="comparison"
          icon="📈"
          text="Comparison"
        />

        <MenuItem
          id="about"
          icon="ℹ️"
          text="About"
        />

      </aside>

      <div className="main-content">

        {page === "dashboard" && <Dashboard />}

        {page === "models" && <Models />}

        {page === "comparison" && <Comparison2025 />}

        {page === "about" && <About />}

      </div>

    </div>
  );
}
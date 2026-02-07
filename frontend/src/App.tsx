import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Signals from "./pages/Signals";
import Options from "./pages/Options";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <nav className="nav">
        <span className="brand">PAT</span>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/analytics">Analytics</NavLink>
        <NavLink to="/signals">Signals</NavLink>
        <NavLink to="/options">Options</NavLink>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/options" element={<Options />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;

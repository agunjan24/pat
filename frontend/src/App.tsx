import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Signals from "./pages/Signals";
import Options from "./pages/Options";
import Import from "./pages/Import";
import Optimize from "./pages/Optimize";
import Alerts from "./pages/Alerts";
import PaperTrading from "./pages/PaperTrading";
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
        <NavLink to="/optimize">Optimize</NavLink>
        <NavLink to="/alerts">Alerts</NavLink>
        <NavLink to="/paper">Paper Trade</NavLink>
        <NavLink to="/import">Import</NavLink>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/options" element={<Options />} />
          <Route path="/optimize" element={<Optimize />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/paper" element={<PaperTrading />} />
          <Route path="/import" element={<Import />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;

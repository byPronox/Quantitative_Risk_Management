import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import AssetList from "./components/AssetList";
import CombinedAnalysisForm from "./components/CombinedAnalysisForm";
import NvdPage from "./pages/NvdPage";

const mockAssets = [
  { id: 1, name: "Web Server" },
  { id: 2, name: "Database Server" },
  { id: 3, name: "Domain Controller" }
];

export default function App() {
  return (
    <Router>
      <nav>
        <Link to="/">Dashboard</Link> | <Link to="/nvd">Vulnerabilidades NVD</Link>
      </nav>
      <Routes>
        <Route
          path="/"
          element={
            <Dashboard />
          }
        />
        <Route path="/nvd" element={<NvdPage />} />
      </Routes>
    </Router>
  );
}

function Dashboard() {
  const [assets] = React.useState(mockAssets);
  const [selectedId, setSelectedId] = React.useState(assets[0].id);
  const selectedAsset = assets.find(a => a.id === selectedId);

  return (
    <div className="dashboard">
      <AssetList assets={assets} selectedId={selectedId} onSelect={setSelectedId} />
      <main>
        <h1>Quantitative Risk Management Dashboard</h1>
        <CombinedAnalysisForm asset={selectedAsset} />
      </main>
    </div>
  );
}

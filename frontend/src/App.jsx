import React, { useState } from "react";
import AssetList from "./components/AssetList";
import CombinedAnalysisForm from "./components/CombinedAnalysisForm";

// Mock de activos, reemplaza por llamada a API si tienes backend
const mockAssets = [
  { id: 1, name: "Web Server" },
  { id: 2, name: "Database Server" },
  { id: 3, name: "Domain Controller" }
];

export default function App() {
  const [assets] = useState(mockAssets);
  const [selectedId, setSelectedId] = useState(assets[0].id);

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
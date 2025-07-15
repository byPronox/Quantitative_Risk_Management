import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import AssetList from "./components/AssetList";
import CombinedAnalysisForm from "./components/CombinedAnalysisForm";
import NvdPage from "./pages/NvdPage";
import ReportsPage from "./pages/ReportsPage";
import LoginPage from "./pages/LoginPage";

const mockAssets = [
  { id: 1, name: "Web Server" },
  { id: 2, name: "Database Server" },
  { id: 3, name: "Domain Controller" }
];

export default function App() {
  const [user, setUser] = React.useState(null);
  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }
  return (
    <Router>
      <nav className="bg-gray-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold">Risk Management System</h1>
              </div>
              <div className="ml-10 flex items-baseline space-x-4">
                <Link 
                  to="/" 
                  className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/nvd" 
                  className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  NVD Vulnerabilities
                </Link>
                <Link 
                  to="/reports" 
                  className="hover:bg-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Generate Reports
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <Routes>
        <Route
          path="/"
          element={<Dashboard />}
        />
        <Route path="/nvd" element={<NvdPage />} />
        <Route path="/reports" element={<ReportsPage />} />
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
        <h1>Quantitative Risk Management</h1>
        <CombinedAnalysisForm asset={selectedAsset} />
      </main>
    </div>
  );
}

import React from "react";
import { BrowserRouter as Router, Route, Routes, Link, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AssetList from "./components/AssetList";
import CombinedAnalysisForm from "./components/CombinedAnalysisForm";
import NvdPage from "./pages/NvdPage";
import ReportsPage from "./pages/ReportsPage";
import NmapPage from "./pages/NmapPage";
import Login from "./pages/Login";

const mockAssets = [
  { id: 1, name: "Servidor Web" },
  { id: 2, name: "Servidor de Base de Datos" },
  { id: 3, name: "Controlador de Dominio" }
];

function NavBar() {
  const { user, logout, isLoggedIn } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isLoggedIn) return null;

  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex-shrink-0 flex items-center gap-2">
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600">
                Sistema De Riesgos
              </h1>
            </div>
            <div className="hidden md:block">
              <div className="flex items-baseline space-x-2">
                <Link
                  to="/"
                  className="text-slate-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200"
                >
                  Predicción ML
                </Link>
                <Link
                  to="/nvd"
                  className="text-slate-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200"
                >
                  Vulnerabilidades NVD
                </Link>
                <Link
                  to="/reports"
                  className="text-slate-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200"
                >
                  Reportes
                </Link>
                <Link
                  to="/scan"
                  className="text-slate-600 hover:text-blue-600 hover:bg-blue-50 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200"
                >
                  Escaneo de Red
                </Link>
              </div>
            </div>
          </div>
          {/* User menu */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">
              👤 {user?.username || 'Usuario'}
            </span>
            <button
              onClick={handleLogout}
              className="text-slate-500 hover:text-red-600 hover:bg-red-50 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function AppRoutes() {
  return (
    <>
      <NavBar />
      <div className="min-h-[calc(100vh-4rem)] bg-slate-50/50">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/nvd"
            element={
              <ProtectedRoute>
                <NvdPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/scan"
            element={
              <ProtectedRoute>
                <NmapPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

function Dashboard() {
  const [assets] = React.useState(mockAssets);
  const [selectedId, setSelectedId] = React.useState(assets[0].id);
  const selectedAsset = assets.find(a => a.id === selectedId);

  return (
    <div className="flex flex-col md:flex-row min-h-[calc(100vh-4rem)]">
      <AssetList assets={assets} selectedId={selectedId} onSelect={setSelectedId} />
      <main className="flex-1 bg-slate-50/50">
        <CombinedAnalysisForm asset={selectedAsset} />
      </main>
    </div>
  );
}

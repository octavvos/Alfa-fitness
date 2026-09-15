import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ScannerPage from "./pages/ScannerPage";
import ClientsPage from "./pages/ClientsPage";
import PlansPage from "./pages/PlansPage";
import MembershipsPage from "./pages/MembershipsPage";
import VisitsPage from "./pages/VisitsPage";
import AccessLogsPage from "./pages/AccessLogsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/scanner" element={<ScannerPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/plans" element={<PlansPage />} />
            <Route path="/memberships" element={<MembershipsPage />} />
            <Route path="/visits" element={<VisitsPage />} />
            <Route path="/access-logs" element={<AccessLogsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

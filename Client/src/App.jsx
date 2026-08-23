import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import IncidentModal from './components/IncidentModal';
import Dashboard from './pages/Dashboard';
import RiskMapPage from './pages/RiskMapPage';
import Alerts from './pages/Alerts';
import Incidents from './pages/Incidents';
import EmergencyResponse from './pages/EmergencyResponse';
import SystemStatus from './pages/SystemStatus';
import Settings from './pages/Settings';

export default function App() {
  const [selectedState, setSelectedState] = useState('All NER States');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  // Bumped each time the modal opens so it remounts with fresh form state.
  const [reportKey, setReportKey] = useState(0);

  const openReport = () => {
    setReportKey((k) => k + 1);
    setReportOpen(true);
  };

  return (
    <BrowserRouter>
      <div className="app-shell">
        {/* Off-canvas scrim for mobile */}
        <div
          className={`scrim ${sidebarOpen ? 'show' : ''}`}
          onClick={() => setSidebarOpen(false)}
        />

        <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />

        <div className="main">
          <Header
            selectedState={selectedState}
            onSelectState={setSelectedState}
            onMenu={() => setSidebarOpen((v) => !v)}
            onReportIncident={openReport}
          />

          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/risk-map" element={<RiskMapPage />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/incidents" element={<Incidents onReportIncident={openReport} />} />
            <Route path="/emergency" element={<EmergencyResponse />} />
            <Route path="/system-status" element={<SystemStatus />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>

        <IncidentModal key={reportKey} open={reportOpen} onClose={() => setReportOpen(false)} />
      </div>
    </BrowserRouter>
  );
}

import { NavLink } from 'react-router-dom';
import Icon from './Icon';
import logo from '../assets/logo.png';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/risk-map', label: 'Risk Map', icon: 'map' },
  { to: '/alerts', label: 'Alerts', icon: 'alert', badge: '10' },
  { to: '/incidents', label: 'Incident Reports', icon: 'clipboard' },
  { to: '/emergency', label: 'Emergency Response', icon: 'shield' },
];

const FOOTER_ITEMS = [
  { to: '/system-status', label: 'System Status', icon: 'activity' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
];

export default function Sidebar({ open, onNavigate }) {
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand">
        <img src={logo} alt="TerraSense Logo" className="brand-logo" />
        <div className="brand-text">
          <span className="brand-name">TerraSense NER</span>
          <span className="brand-sub">Early Warning System</span>
        </div>
      </div>

      <nav className="nav">
        <span className="nav-section-label">Operations</span>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={onNavigate}
          >
            <Icon name={item.icon} size={18} className="nav-ico" />
            {item.label}
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </NavLink>
        ))}

        <span className="nav-section-label">System</span>
        {FOOTER_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={onNavigate}
          >
            <Icon name={item.icon} size={18} className="nav-ico" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sys-status">
          <span className="live-dot" />
          <div className="sys-status-text">
            <b>System Operational</b>
            <span>214 / 226 sensors online</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

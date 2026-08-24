import { useEffect, useRef, useState } from 'react';
import Icon from './Icon';
import { NER_STATES, NOTIFICATIONS, REGION_META } from '../data/mockData';

// Closes a dropdown when clicking outside its ref.
function useOutside(ref, onClose) {
  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose();
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [ref, onClose]);
}

export default function Header({ selectedState, onSelectState, onMenu, onReportIncident }) {
  const [stateOpen, setStateOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const stateRef = useRef(null);
  const notifRef = useRef(null);

  useOutside(stateRef, () => setStateOpen(false));
  useOutside(notifRef, () => setNotifOpen(false));

  const criticalCount = NOTIFICATIONS.filter((n) => n.band === 'CRITICAL').length;

  return (
    <header className="header">
      <button className="icon-btn menu-toggle" onClick={onMenu} aria-label="Toggle menu">
        <Icon name="layers" size={18} />
      </button>

      <div className="header-titles">
        <span className="header-title">TerraSense NER</span>
        <span className="header-subtitle">Landslide Early Warning &amp; Risk Monitoring</span>
      </div>

      <label className="searchbar" style={{ marginLeft: 8 }}>
        <Icon name="search" size={15} className="s-ico" />
        <input type="text" placeholder="Search districts, roads, incidents…" aria-label="Search" />
        <kbd>/</kbd>
      </label>

      <div className="header-right">
        {/* State / district selector */}
        <div className="state-select-wrap" ref={stateRef}>
          <button className="state-select" onClick={() => setStateOpen((v) => !v)}>
            <Icon name="location" size={15} className="sel-ico" />
            {selectedState}
            <Icon name="chevronDown" size={15} className="caret" />
          </button>
          {stateOpen && (
            <div className="dropdown fade-up">
              {NER_STATES.map((s) => (
                <button
                  key={s}
                  className={`dropdown-item ${s === selectedState ? 'selected' : ''}`}
                  onClick={() => {
                    onSelectState(s);
                    setStateOpen(false);
                  }}
                >
                  {s === selectedState && <Icon name="check" size={14} />}
                  <span style={{ marginLeft: s === selectedState ? 0 : 22 }}>{s}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="region-chip">
          <Icon name="globe" size={15} />
          <span className="muted">Region</span>
          <b>{REGION_META.name}</b>
        </div>

        <div className="updated-chip">
          <Icon name="refresh" size={14} />
          Updated {REGION_META.lastUpdated}
        </div>

        <button className="btn btn--danger btn--sm" onClick={onReportIncident}>
          <Icon name="plus" size={15} />
          Report Incident
        </button>

        {/* Notifications */}
        <div className="state-select-wrap" ref={notifRef}>
          <button className="icon-btn" onClick={() => setNotifOpen((v) => !v)} aria-label="Notifications">
            <Icon name="bell" size={18} />
            {criticalCount > 0 && <span className="badge-count">{NOTIFICATIONS.length}</span>}
          </button>
          {notifOpen && (
            <div className="dropdown right notif-panel fade-up">
              <div className="notif-head">
                Notifications
                <span className="eyebrow">{NOTIFICATIONS.length} new</span>
              </div>
              {NOTIFICATIONS.map((n) => (
                <div className="notif-item" key={n.id}>
                  <span
                    className="notif-bar"
                    style={{ background: n.band === 'CRITICAL' ? 'var(--risk-critical)' : 'var(--risk-high)' }}
                  />
                  <div>
                    <div className="n-title">{n.title}</div>
                    <div className="n-time">{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </header>
  );
}

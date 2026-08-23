import { useState } from 'react';
import { NER_STATES } from '../data/mockData';

const LANGUAGES = ['English', 'Assamese', 'Manipuri (Meitei)', 'Khasi', 'Mizo', 'Nagamese', 'Nepali', 'Bengali'];

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      style={{
        width: 42,
        height: 24,
        borderRadius: 999,
        border: '1px solid var(--color-line-strong)',
        background: checked ? 'var(--color-accent)' : 'var(--color-surface-2)',
        position: 'relative',
        transition: 'background 0.15s',
      }}
      aria-pressed={checked}
    >
      <span
        style={{
          position: 'absolute',
          top: 2,
          left: checked ? 20 : 2,
          width: 18,
          height: 18,
          borderRadius: '50%',
          background: '#fff',
          transition: 'left 0.15s',
        }}
      />
    </button>
  );
}

export default function Settings() {
  const [language, setLanguage] = useState('English');
  const [homeState, setHomeState] = useState('All NER States');
  const [prefs, setPrefs] = useState({ critical: true, sms: true, lowBandwidth: true, autoRefresh: true });

  const setPref = (k) => (v) => setPrefs((p) => ({ ...p, [k]: v }));

  const rows = [
    { key: 'critical', label: 'Critical alert push notifications', desc: 'Immediate push for CRITICAL risk zones' },
    { key: 'sms', label: 'SMS dispatch to field officers', desc: 'Send warnings over SMS for low-network areas' },
    { key: 'lowBandwidth', label: 'Low-bandwidth mode', desc: 'Reduce tile/data usage on weak connections' },
    { key: 'autoRefresh', label: 'Auto-refresh dashboard', desc: 'Refresh risk data every 2 minutes' },
  ];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Settings</h1>
          <p>Configure regional preferences, language and alert delivery for your operations centre.</p>
        </div>
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header">
            <div className="panel-title">Regional &amp; Language</div>
            <div className="panel-subtitle">Multilingual communication for NER communities</div>
          </div>
          <div className="panel-body">
            <div className="field">
              <label className="field-label">Default State / Region</label>
              <select className="select" value={homeState} onChange={(e) => setHomeState(e.target.value)}>
                {NER_STATES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="field-label">Alert Language</label>
              <select className="select" value={language} onChange={(e) => setLanguage(e.target.value)}>
                {LANGUAGES.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div className="panel-title">Notifications &amp; Delivery</div>
          </div>
          <div className="panel-body">
            {rows.map((r) => (
              <div className="status-feed" key={r.key} style={{ alignItems: 'center' }}>
                <div>
                  <div className="cell-strong" style={{ color: 'var(--color-ink)' }}>{r.label}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--color-ink-muted)' }}>{r.desc}</div>
                </div>
                <Toggle checked={prefs[r.key]} onChange={setPref(r.key)} />
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

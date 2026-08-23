// Shimmer skeleton primitives for loading states.

export function Skeleton({ width = '100%', height = 16, radius = 8, style }) {
  return (
    <span
      className="skeleton"
      style={{ display: 'block', width, height, borderRadius: radius, ...style }}
      aria-hidden="true"
    />
  );
}

// KPI card placeholder matching the real card's footprint.
export function KpiSkeleton() {
  return (
    <div className="risk-card" aria-hidden="true">
      <div className="risk-card-top">
        <Skeleton width={96} height={12} />
        <Skeleton width={38} height={38} radius={10} />
      </div>
      <Skeleton width={70} height={30} radius={6} style={{ marginTop: 4 }} />
      <div className="risk-card-foot">
        <Skeleton width={68} height={18} radius={999} />
        <Skeleton width={72} height={24} style={{ marginLeft: 'auto' }} />
      </div>
      <Skeleton width="60%" height={11} />
    </div>
  );
}

// Generic panel placeholder with a header + body block.
export function PanelSkeleton({ bodyHeight = 220 }) {
  return (
    <section className="panel" aria-busy="true" aria-live="polite">
      <div className="panel-header">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <Skeleton width={160} height={14} />
          <Skeleton width={240} height={11} />
        </div>
      </div>
      <div className="panel-body">
        <Skeleton width="100%" height={bodyHeight} radius={12} />
      </div>
    </section>
  );
}

export default function SettingsLoading() {
  return (
    <main className="page">
      <div className="page-header">
        <div className="skeleton-shimmer" style={{ width: 120, height: 36, borderRadius: 4 }} />
        <div className="skeleton-shimmer" style={{ width: 340, height: 16, borderRadius: 4 }} />
      </div>

      <section className="onboarding-form">
        <div className="skeleton-shimmer" style={{ width: 180, height: 20, borderRadius: 4, marginTop: 24 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton-shimmer" style={{ width: "100%", height: 40, borderRadius: 6 }} />
          ))}
        </div>

        <div className="skeleton-shimmer" style={{ width: 180, height: 20, borderRadius: 4, marginTop: 32 }} />
        <div className="skeleton-shimmer" style={{ width: "100%", height: 40, borderRadius: 6, marginTop: 12 }} />

        <div className="skeleton-shimmer" style={{ width: 120, height: 40, borderRadius: 6, marginTop: 32 }} />
      </section>
    </main>
  );
}

export default function DiscoverLoading() {
  return (
    <main className="page">
      <div className="page-header">
        <p className="eyebrow skeleton-shimmer" style={{ width: 60, height: 14 }} />
        <div className="skeleton-shimmer" style={{ width: 280, height: 36, borderRadius: 4 }} />
        <div className="skeleton-shimmer" style={{ width: 340, height: 16, borderRadius: 4 }} />
        <div className="skeleton-shimmer" style={{ width: 200, height: 14, borderRadius: 4, marginTop: 4 }} />
      </div>

      <section className="feed-toolbar">
        <div className="filter-pills">
          {Array.from({ length: 4 }).map((_, i) => (
            <span
              key={i}
              className="filter-pill skeleton-shimmer"
              style={{ width: 80 + i * 20, height: 30 }}
            />
          ))}
        </div>
      </section>

      <div className="discover-grid">
        {Array.from({ length: 6 }).map((_, i) => (
          <article key={i} className="discover-card skeleton-row" style={{ animationDelay: `${i * 40}ms` }}>
            <div className="skeleton-shimmer" style={{ width: "85%", height: 20, borderRadius: 4 }} />
            <div className="skeleton-shimmer" style={{ width: "60%", height: 14, borderRadius: 4, marginTop: 8 }} />
            <div className="skeleton-shimmer" style={{ width: "100%", height: 48, borderRadius: 4, marginTop: 10 }} />
            <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
              <span className="skeleton-shimmer" style={{ width: 48, height: 20, borderRadius: 4 }} />
              <span className="skeleton-shimmer" style={{ width: 48, height: 20, borderRadius: 4 }} />
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}

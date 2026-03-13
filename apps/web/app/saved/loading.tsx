export default function SavedLoading() {
  return (
    <main className="page">
      <div className="page-header">
        <p className="eyebrow skeleton-shimmer" style={{ width: 50, height: 14 }} />
        <div className="skeleton-shimmer" style={{ width: 220, height: 36, borderRadius: 4 }} />
        <div className="skeleton-shimmer" style={{ width: 300, height: 16, borderRadius: 4 }} />
      </div>

      <section className="feed-list">
        {Array.from({ length: 5 }).map((_, i) => (
          <article key={i} className="paper-row skeleton-row" style={{ animationDelay: `${i * 40}ms` }}>
            <div className="skeleton-shimmer" style={{ width: "85%", height: 22, borderRadius: 4 }} />
            <div className="skeleton-shimmer" style={{ width: "55%", height: 14, borderRadius: 4, marginTop: 8 }} />
            <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
              <span className="skeleton-shimmer" style={{ width: 60, height: 20, borderRadius: 4 }} />
              <span className="skeleton-shimmer" style={{ width: 60, height: 20, borderRadius: 4 }} />
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

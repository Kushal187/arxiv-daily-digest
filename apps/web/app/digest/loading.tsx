export default function DigestLoading() {
  return (
    <main className="page">
      <div className="page-header">
        <p className="eyebrow digest-skeleton-shimmer" style={{ width: 80, height: 14 }} />
        <div className="digest-skeleton-shimmer" style={{ width: 260, height: 36, borderRadius: 4 }} />
        <div className="digest-skeleton-shimmer" style={{ width: 180, height: 16, borderRadius: 4 }} />
      </div>

      <section className="feed-toolbar">
        <div className="filter-pills">
          {Array.from({ length: 4 }).map((_, i) => (
            <span
              key={i}
              className="filter-pill digest-skeleton-shimmer"
              style={{ width: 72 + i * 16, height: 30 }}
            />
          ))}
        </div>
      </section>

      <section className="feed-list">
        {Array.from({ length: 6 }).map((_, i) => (
          <article key={i} className="paper-row digest-skeleton-row">
            <div className="paper-row-header">
              <span className="digest-skeleton-shimmer" style={{ width: 100, height: 24, borderRadius: 999 }} />
            </div>
            <div className="digest-skeleton-shimmer" style={{ width: "90%", height: 22, borderRadius: 4 }} />
            <div className="digest-skeleton-shimmer" style={{ width: "60%", height: 14, borderRadius: 4, marginTop: 8 }} />
            <div className="digest-skeleton-shimmer" style={{ width: "100%", height: 38, borderRadius: 4, marginTop: 10 }} />
            <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
              <span className="digest-skeleton-shimmer" style={{ width: 48, height: 20, borderRadius: 4 }} />
              <span className="digest-skeleton-shimmer" style={{ width: 48, height: 20, borderRadius: 4 }} />
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

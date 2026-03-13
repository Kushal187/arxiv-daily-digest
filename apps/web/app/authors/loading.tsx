export default function AuthorsLoading() {
  return (
    <main className="page">
      <div className="page-header">
        <p className="eyebrow skeleton-shimmer" style={{ width: 60, height: 14 }} />
        <div className="skeleton-shimmer" style={{ width: 200, height: 36, borderRadius: 4 }} />
        <div className="skeleton-shimmer" style={{ width: 340, height: 16, borderRadius: 4 }} />
      </div>

      <section className="authors-page">
        <div className="authors-summary">
          <span className="skeleton-shimmer" style={{ width: 140, height: 14, borderRadius: 4 }} />
          <span className="skeleton-shimmer" style={{ width: 120, height: 14, borderRadius: 4 }} />
        </div>

        <div className="authors-grid">
          {Array.from({ length: 3 }).map((_, i) => (
            <section key={i} className="author-block skeleton-row" style={{ animationDelay: `${i * 40}ms` }}>
              <div className="author-block-header">
                <div className="skeleton-shimmer" style={{ width: 140, height: 22, borderRadius: 4 }} />
                <span className="skeleton-shimmer" style={{ width: 90, height: 14, borderRadius: 4 }} />
              </div>
              <ul className="author-paper-list">
                {Array.from({ length: 2 }).map((_, j) => (
                  <li key={j}>
                    <div className="skeleton-shimmer" style={{ width: "80%", height: 16, borderRadius: 4 }} />
                    <div className="skeleton-shimmer" style={{ width: "50%", height: 12, borderRadius: 4, marginTop: 4 }} />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </section>
    </main>
  );
}

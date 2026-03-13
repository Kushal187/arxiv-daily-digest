export default function PaperLoading() {
  return (
    <main className="page">
      <article className="paper-detail">
        <p className="eyebrow skeleton-shimmer" style={{ width: 50, height: 14 }} />
        <div className="skeleton-shimmer" style={{ width: "90%", height: 30, borderRadius: 4, marginTop: 8 }} />
        <div className="skeleton-shimmer" style={{ width: "70%", height: 14, borderRadius: 4, marginTop: 12 }} />

        <div className="skeleton-shimmer" style={{ width: "100%", height: 80, borderRadius: 6, marginTop: 20 }} />

        <div className="skeleton-shimmer" style={{ width: "100%", height: 60, borderRadius: 4, marginTop: 16 }} />

        <div style={{ display: "flex", gap: 6, marginTop: 16 }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <span key={i} className="skeleton-shimmer" style={{ width: 60, height: 22, borderRadius: 4 }} />
          ))}
        </div>

        <div className="skeleton-shimmer" style={{ width: 200, height: 14, borderRadius: 4, marginTop: 16 }} />

        <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
          <span className="skeleton-shimmer" style={{ width: 70, height: 32, borderRadius: 6 }} />
          <span className="skeleton-shimmer" style={{ width: 70, height: 32, borderRadius: 6 }} />
          <span className="skeleton-shimmer" style={{ width: 80, height: 32, borderRadius: 6 }} />
        </div>
      </article>
    </main>
  );
}

"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="page">
      <section className="page-header">
        <p className="eyebrow">error</p>
        <h1>Something went wrong</h1>
        <p className="page-description">Something went wrong loading this page.</p>
      </section>
      <section className="feed-list">
        <div className="empty-state">
          <button className="action-link prominent" onClick={reset} style={{ marginTop: 12 }}>
            Try again
          </button>
        </div>
      </section>
    </main>
  );
}

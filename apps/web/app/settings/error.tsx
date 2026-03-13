"use client";

export default function SettingsError({
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
        <p className="page-description">We could not load your settings.</p>
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

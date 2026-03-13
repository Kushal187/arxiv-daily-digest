"use client";

export default function RootError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <main className="page">
            <section className="page-header">
              <h1>Something went wrong</h1>
              <p className="page-description">A critical error occurred.</p>
            </section>
            <section className="feed-list">
              <div className="empty-state">
                <button className="action-link prominent" onClick={reset} style={{ marginTop: 12 }}>
                  Try again
                </button>
              </div>
            </section>
          </main>
        </div>
      </body>
    </html>
  );
}

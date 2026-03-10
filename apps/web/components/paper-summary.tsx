type Props = {
  summary: string | null;
  summarySource: "extractive" | "llm" | null;
};

export function PaperSummary({ summary, summarySource }: Props) {
  return (
    <div className="detail-section">
      <h2>Quick summary</h2>
      {summary ? <p>{summary}</p> : <p className="page-description">No summary is available yet for this paper.</p>}
      {summary ? (
        <p className="section-note">
          Source: {summarySource === "llm" ? "generated summary" : "extractive fallback"}
        </p>
      ) : null}
    </div>
  );
}

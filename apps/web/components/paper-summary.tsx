type Props = {
  summary: string | null;
  summarySource: "extractive" | "llm" | null;
};

export function PaperSummary({ summary, summarySource }: Props) {
  if (!summary) {
    return null;
  }

  return (
    <div className="paper-summary-block">
      <p className="paper-summary-label">
        {summarySource === "llm" ? "AI summary" : "Summary"}
      </p>
      <p className="paper-summary-text">{summary}</p>
    </div>
  );
}

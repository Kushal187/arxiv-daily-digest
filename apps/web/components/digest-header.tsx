import { formatCalendarDate } from "../lib/dates";

type Props = {
  requestedDate: string;
  resolvedDate: string;
  isFallback: boolean;
};

export function DigestHeader({ requestedDate, resolvedDate, isFallback }: Props) {
  return (
    <section className="page-header">
      <p className="eyebrow">daily digest</p>
      <h1>{formatCalendarDate(resolvedDate)}</h1>
      <p className="page-description">
        Ranked against selected topics, followed authors, category preferences, saved papers, and
        dismissals.
      </p>
      {isFallback ? (
        <p className="fallback-note">
          Showing the latest available digest from {formatCalendarDate(resolvedDate)} while{" "}
          {formatCalendarDate(requestedDate)} is still empty.
        </p>
      ) : null}
    </section>
  );
}

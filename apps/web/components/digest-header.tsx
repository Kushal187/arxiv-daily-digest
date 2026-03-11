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
      <h1>{formatCalendarDate(requestedDate)}</h1>
      <p className="page-description">
        Ranked against selected research areas, followed authors, category preferences, saved papers, and
        dismissals.
      </p>
      {isFallback ? (
        <p className="fallback-note">
          No digest is available for {formatCalendarDate(requestedDate)} yet; showing {formatCalendarDate(resolvedDate)}{" "}
          instead.
        </p>
      ) : null}
    </section>
  );
}

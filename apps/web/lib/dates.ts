export function formatCalendarDate(value: string, locale?: string): string {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, (month || 1) - 1, day || 1, 12));
  return new Intl.DateTimeFormat(locale, {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC"
  }).format(date);
}

export function formatTimestampDate(value: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

export function calendarDateString(value: Date, timeZone?: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone
  }).formatToParts(value);

  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;

  if (!year || !month || !day) {
    throw new Error("Could not format local calendar date.");
  }

  return `${year}-${month}-${day}`;
}

export function browserLocalDateString(value: Date = new Date()): string {
  return calendarDateString(value);
}

export function isCalendarDateString(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

export function utcCalendarDateString(value: Date = new Date()): string {
  return value.toISOString().slice(0, 10);
}

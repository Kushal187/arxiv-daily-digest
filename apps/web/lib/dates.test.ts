import { describe, expect, it } from "vitest";
import {
  browserLocalDateString,
  calendarDateString,
  formatCalendarDate,
  utcCalendarDateString,
  isCalendarDateString
} from "./dates";

describe("formatCalendarDate", () => {
  it("keeps calendar dates stable across time zones", () => {
    expect(formatCalendarDate("2026-03-10", "en-US")).toBe("March 10, 2026");
  });
});

describe("calendarDateString", () => {
  it("returns the local calendar day for a provided time zone", () => {
    expect(calendarDateString(new Date("2026-03-11T01:30:00Z"), "America/New_York")).toBe(
      "2026-03-10"
    );
  });

  it("uses the current environment time zone when no override is supplied", () => {
    expect(browserLocalDateString(new Date("2026-03-10T12:00:00Z"))).toBe("2026-03-10");
  });
});

describe("isCalendarDateString", () => {
  it("accepts plain YYYY-MM-DD strings", () => {
    expect(isCalendarDateString("2026-03-10")).toBe(true);
  });

  it("rejects non-calendar query values", () => {
    expect(isCalendarDateString("03/10/2026")).toBe(false);
  });
});

describe("utcCalendarDateString", () => {
  it("uses the server-side UTC calendar day", () => {
    expect(utcCalendarDateString(new Date("2026-03-10T23:59:59Z"))).toBe("2026-03-10");
  });
});

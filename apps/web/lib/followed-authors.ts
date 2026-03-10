export function normalizeFollowedAuthorDisplay(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

export function normalizeFollowedAuthorKey(value: string): string {
  return normalizeFollowedAuthorDisplay(value).toLowerCase();
}

export function dedupeFollowedAuthors(values: string[]): string[] {
  const authors = new Map<string, string>();

  for (const value of values) {
    const display = normalizeFollowedAuthorDisplay(value);
    const key = normalizeFollowedAuthorKey(display);

    if (!display || authors.has(key)) {
      continue;
    }

    authors.set(key, display);
  }

  return [...authors.values()];
}

type AuthorMatch = {
  followed: string;
  paperAuthor: string;
  score: number;
};

function normalizeAuthorName(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parts(name: string): string[] {
  return normalizeAuthorName(name).split(" ").filter(Boolean);
}

function levenshteinDistance(left: string, right: string): number {
  if (left === right) {
    return 0;
  }

  if (!left.length) {
    return right.length;
  }

  if (!right.length) {
    return left.length;
  }

  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);

  for (let row = 0; row < left.length; row += 1) {
    let diagonal = previous[0];
    previous[0] = row + 1;

    for (let column = 0; column < right.length; column += 1) {
      const nextDiagonal = previous[column + 1];
      const cost = left[row] === right[column] ? 0 : 1;
      previous[column + 1] = Math.min(
        previous[column + 1] + 1,
        previous[column] + 1,
        diagonal + cost
      );
      diagonal = nextDiagonal;
    }
  }

  return previous[right.length];
}

function scoreAuthorMatch(followed: string, paperAuthor: string): number {
  const followedNormalized = normalizeAuthorName(followed);
  const paperNormalized = normalizeAuthorName(paperAuthor);

  if (!followedNormalized || !paperNormalized) {
    return 0;
  }

  if (followedNormalized === paperNormalized) {
    return 1;
  }

  const followedParts = parts(followed);
  const paperParts = parts(paperAuthor);
  if (followedParts.length < 2 || paperParts.length < 2) {
    return 0;
  }

  const followedFirst = followedParts[0] ?? "";
  const paperFirst = paperParts[0] ?? "";
  const followedLast = followedParts.at(-1) ?? "";
  const paperLast = paperParts.at(-1) ?? "";
  if (!followedLast || !paperLast || !followedFirst || !paperFirst) {
    return 0;
  }

  if (followedLast === paperLast) {
    if (followedFirst === paperFirst) {
      return 0.92;
    }

    if (
      Math.min(followedFirst.length, paperFirst.length) >= 3 &&
      (followedFirst.startsWith(paperFirst) || paperFirst.startsWith(followedFirst))
    ) {
      return 0.88;
    }

    if (
      Math.min(followedFirst.length, paperFirst.length) >= 4 &&
      levenshteinDistance(followedFirst, paperFirst) === 1
    ) {
      return 0.84;
    }
  }

  if (
    followedFirst === paperFirst &&
    followedLast.length >= 5 &&
    paperLast.length >= 5 &&
    levenshteinDistance(followedLast, paperLast) === 1
  ) {
    return 0.8;
  }

  return 0;
}

export function matchFollowedAuthors(
  followedAuthors: string[],
  paperAuthors: string[]
): AuthorMatch[] {
  const matches: AuthorMatch[] = [];

  for (const followed of followedAuthors) {
    let bestMatch: AuthorMatch | null = null;

    for (const paperAuthor of paperAuthors) {
      const score = scoreAuthorMatch(followed, paperAuthor);
      if (!bestMatch || score > bestMatch.score) {
        bestMatch = { followed, paperAuthor, score };
      }
    }

    if (bestMatch && bestMatch.score >= 0.8) {
      matches.push(bestMatch);
    }
  }

  return matches.sort((left, right) => right.score - left.score);
}

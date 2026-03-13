import { auth } from "./lib/auth";
import { NextResponse } from "next/server";

const PROTECTED_PREFIXES = [
  "/digest",
  "/discover",
  "/saved",
  "/authors",
  "/settings",
  "/papers",
  "/onboarding",
];

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));

  if (isProtected && !req.auth?.user) {
    return NextResponse.redirect(new URL("/", req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};

import Link from "next/link";
import type { Session } from "next-auth";
import { SignInButton } from "./sign-in-button";
import { SignOutButton } from "./sign-out-button";

export function Nav({ session }: { session: Session | null }) {
  return (
    <header className="site-header">
      <div className="site-branding">
        <Link className="brand" href={session ? "/digest" : "/"}>
          arXiv Daily Digest
        </Link>
        <p className="site-tagline">ranked daily arxiv for ml researchers</p>
      </div>
      <nav className="nav-links">
        {session ? (
          <>
            <Link href="/digest">Digest</Link>
            <Link href="/authors">Authors</Link>
            <Link href="/saved">Saved</Link>
            <Link href="/settings">Settings</Link>
            <SignOutButton />
          </>
        ) : (
          <SignInButton className="nav-signin" />
        )}
      </nav>
    </header>
  );
}

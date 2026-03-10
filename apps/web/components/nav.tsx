import Link from "next/link";
import type { Session } from "next-auth";

export function Nav({ session }: { session: Session | null }) {
  return (
    <header className="site-header">
      <div>
        <Link className="brand" href={session ? "/digest" : "/"}>
          arXiv Daily Digest
        </Link>
        <p className="subtle">Daily research discovery for ML researchers.</p>
      </div>
      <nav className="nav-links">
        {session ? (
          <>
            <Link href="/digest">Digest</Link>
            <Link href="/saved">Saved</Link>
            <Link href="/settings">Settings</Link>
            <a href="/api/auth/signout">Sign out</a>
          </>
        ) : (
          <a href="/api/auth/signin">Sign in with Google</a>
        )}
      </nav>
    </header>
  );
}

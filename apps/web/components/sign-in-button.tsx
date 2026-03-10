import { signIn } from "../lib/auth";

export function SignInButton({ className }: { className?: string }) {
  return (
    <form
      className="sign-in-form"
      action={async () => {
        "use server";
        await signIn("google");
      }}
    >
      <button type="submit" className={className}>
        Sign in with Google
      </button>
    </form>
  );
}

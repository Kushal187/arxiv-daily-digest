"use client";

import { useRef, useState } from "react";

async function doSignOut() {
  const csrfRes = await fetch("/api/auth/csrf");
  const { csrfToken } = await csrfRes.json();

  await fetch("/api/auth/signout", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ csrfToken }),
  });

  window.location.href = "/";
}

export function SignOutButton() {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  function handleOpen() {
    setOpen(true);
    setTimeout(() => dialogRef.current?.showModal(), 0);
  }

  function handleClose() {
    dialogRef.current?.close();
    setOpen(false);
  }

  return (
    <>
      <button type="button" className="nav-link-button" onClick={handleOpen}>
        Sign out
      </button>
      {open && (
        <dialog ref={dialogRef} className="signout-dialog" onClose={handleClose}>
          <div className="signout-dialog-inner">
            <p className="signout-dialog-title">Sign out?</p>
            <p className="signout-dialog-text">
              You&apos;ll need to sign in again to see your personalized digest.
            </p>
            <div className="signout-dialog-actions">
              <button type="button" className="cta-secondary" onClick={handleClose}>
                Cancel
              </button>
              <button type="button" className="cta-danger" onClick={doSignOut}>
                Sign out
              </button>
            </div>
          </div>
        </dialog>
      )}
    </>
  );
}

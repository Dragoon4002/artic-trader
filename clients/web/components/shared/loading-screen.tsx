"use client";

import { useEffect, useState } from "react";

export function LoadingScreen() {
  const [visible, setVisible] = useState(true);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const finish = () => {
      setFading(true);
      window.setTimeout(() => setVisible(false), 400);
    };
    if (document.readyState === "complete") {
      finish();
      return;
    }
    window.addEventListener("load", finish);
    return () => window.removeEventListener("load", finish);
  }, []);

  if (!visible) return null;

  return (
    <div
      aria-hidden
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--color-surface, #0A0A0F)",
        opacity: fading ? 0 : 1,
        transition: "opacity 400ms ease",
        pointerEvents: fading ? "none" : "auto",
      }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/FoxRunning-bgRemoved.gif"
        alt="Loading"
        style={{ width: 160, height: "auto" }}
      />
    </div>
  );
}

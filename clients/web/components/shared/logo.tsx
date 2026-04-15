import Image from "next/image";
import Link from "next/link";

export function Logo({ size = "default" }: { size?: "default" | "small" }) {
  const imgSize = size === "small" ? 24 : 32;
  return (
    <Link href="/" className="flex items-center gap-2.5 text-white font-semibold tracking-tight">
      <Image
        src="/artic-logo.png"
        alt="Artic"
        width={imgSize}
        height={imgSize}
        className="rounded-lg"
      />
      <span className={size === "small" ? "text-sm text-white/60" : "text-lg"}>
        Artic
      </span>
    </Link>
  );
}

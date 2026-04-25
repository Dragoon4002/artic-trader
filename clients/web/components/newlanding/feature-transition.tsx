import Image from "next/image";

export function FeatureTransition() {
  return (
    <div className="relative w-full overflow-hidden">
      {/* Top fade into surface */}
      <div className="pointer-events-none absolute top-0 left-0 right-0 h-32 z-10 bg-gradient-to-b from-surface via-surface/80 to-transparent" />

      {/* Bottom fade into surface */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-48 z-10 bg-gradient-to-t from-surface via-surface/90 to-transparent" />

      {/* Side fades */}
      <div className="pointer-events-none absolute inset-y-0 left-0 w-32 z-10 bg-gradient-to-r from-surface to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-32 z-10 bg-gradient-to-l from-surface to-transparent" />

      <div className="relative h-[420px] md:h-[560px] w-full">
        <Image
          src="/assets/feature%20lake.png"
          alt=""
          fill
          priority={false}
          className="object-cover object-center opacity-70"
        />
      </div>
    </div>
  );
}

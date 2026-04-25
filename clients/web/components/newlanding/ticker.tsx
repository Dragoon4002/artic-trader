const items = [
  { name: "Initia", type: "L1 chain" },
  { name: "MiniEVM", type: "appchain" },
  { name: "Morph", type: "VM runtime" },
  { name: "Pyth", type: "price feeds" },
  { name: "Claude", type: "LLM" },
  { name: "GPT-4o", type: "LLM" },
  { name: "DeepSeek", type: "LLM" },
  { name: "Gemini", type: "LLM" },
  { name: "TwelveData", type: "candles" },
  { name: "CoinMarketCap", type: "data" },
  { name: "PostgreSQL", type: "storage" },
  { name: "Docker", type: "containers" },
  { name: "Initia MiniEVM", type: "on-chain audit" },
  { name: "WebSocket", type: "streaming" },
];

export function Ticker() {
  const doubled = [...items, ...items];
  return (
    <div className="overflow-hidden py-8 border-y border-white/6 bg-foreground">
      <div className="flex gap-15 items-center animate-ticker w-max">
        {doubled.map((item, i) => (
          <span
            key={i}
            className="text-[13px] text-popover/50 whitespace-nowrap font-medium"
          >
            <strong className="text-background">{item.name}</strong> {item.type}
          </span>
        ))}
      </div>
    </div>
  );
}

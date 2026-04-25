import { Navbar } from "@/components/newlanding/navbar";
import { Footer } from "@/components/landing/footer";
import Link from "next/link";
import { ArrowLeft, Clock, Calendar } from "lucide-react";

function Tag({ children }: { children: string }) {
  return (
    <span className="text-[10px] uppercase tracking-wider font-semibold text-orange-text bg-orange/15 px-2.5 py-1 rounded-full">
      {children}
    </span>
  );
}

function H2({ children }: { children: string }) {
  return (
    <h2 className="text-2xl md:text-3xl font-bold text-white mt-16 mb-4">
      {children}
    </h2>
  );
}

function H3({ children }: { children: string }) {
  return (
    <h3 className="text-lg md:text-xl font-semibold text-white mt-10 mb-3">
      {children}
    </h3>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[15px] text-white/60 leading-[1.8] mb-4">{children}</p>
  );
}

function Highlight({ children }: { children: string }) {
  return <span className="text-orange-text font-medium">{children}</span>;
}

function StrategyCard({
  name,
  signal,
  description,
}: {
  name: string;
  signal: string;
  description: string;
}) {
  return (
    <div className="p-4 rounded-xl border border-white/8 bg-white/3 mb-3">
      <div className="flex items-start justify-between gap-3 mb-2">
        <p className="text-sm font-semibold text-white">{name}</p>
        <code className="text-[11px] text-teal-light bg-teal/15 px-2 py-0.5 rounded-md font-mono whitespace-nowrap shrink-0">
          {signal}
        </code>
      </div>
      <p className="text-[13px] text-white/45 leading-relaxed">
        {description}
      </p>
    </div>
  );
}

function ComparisonTable() {
  const rows = [
    {
      category: "Momentum",
      marketFit: "Strong trends",
      risk: "Medium-High",
      latency: "Low",
      color: "text-orange-text",
    },
    {
      category: "Mean Reversion",
      marketFit: "Range-bound",
      risk: "Medium",
      latency: "Low",
      color: "text-teal-light",
    },
    {
      category: "Volatility",
      marketFit: "Breakouts & squeezes",
      risk: "High",
      latency: "Medium",
      color: "text-red-light",
    },
    {
      category: "Volume / Order Flow",
      marketFit: "Intraday, liquid markets",
      risk: "Low-Medium",
      latency: "Low",
      color: "text-blue-light",
    },
    {
      category: "Statistical",
      marketFit: "All regimes",
      risk: "Low",
      latency: "Medium-High",
      color: "text-orange-light",
    },
  ];

  return (
    <div className="overflow-x-auto my-8 rounded-xl border border-white/8">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/8 bg-white/3">
            <th className="text-left text-xs text-white/50 font-semibold px-4 py-3 uppercase tracking-wider">
              Category
            </th>
            <th className="text-left text-xs text-white/50 font-semibold px-4 py-3 uppercase tracking-wider">
              Best Market Fit
            </th>
            <th className="text-left text-xs text-white/50 font-semibold px-4 py-3 uppercase tracking-wider">
              Risk
            </th>
            <th className="text-left text-xs text-white/50 font-semibold px-4 py-3 uppercase tracking-wider">
              Signal Latency
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.category}
              className="border-b border-white/5 last:border-0"
            >
              <td className={`px-4 py-3 font-medium ${row.color}`}>
                {row.category}
              </td>
              <td className="px-4 py-3 text-white/50">{row.marketFit}</td>
              <td className="px-4 py-3 text-white/50">{row.risk}</td>
              <td className="px-4 py-3 text-white/50">{row.latency}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-6 p-5 rounded-xl border border-orange/30 bg-orange/10">
      <p className="text-sm text-orange-text leading-relaxed">{children}</p>
    </div>
  );
}

export default function StrategyComparisonPost() {
  return (
    <>
      <Navbar />
      <article className="flex-1 px-6 pt-32 pb-20 max-w-3xl mx-auto">
        {/* Back link */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mb-10"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          All posts
        </Link>

        {/* Header */}
        <div className="flex flex-wrap gap-2 mb-5">
          <Tag>Strategies</Tag>
          <Tag>Research</Tag>
          <Tag>Quant</Tag>
        </div>

        <h1 className="text-[clamp(28px,5vw,44px)] font-bold tracking-tight text-white leading-[1.15] mb-5">
          A Comparative Study of Quantitative Trading Strategies
        </h1>

        <div className="flex items-center gap-4 text-xs text-white/30 mb-12">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            April 15, 2026
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            12 min read
          </span>
        </div>

        <div className="h-px bg-white/8 mb-12" />

        {/* Content */}
        <P>
          Artic ships with over 30 quantitative strategies spanning five
          families. Rather than picking one, an LLM evaluates market conditions
          and selects the optimal strategy — or blends several — in real time.
          This post breaks down each family, explains the core signal logic, and
          compares their strengths so you can understand what is happening under
          the hood.
        </P>

        <P>
          Every strategy in Artic returns a normalised{" "}
          <Highlight>signal</Highlight> between −1 (strongly bearish) and +1
          (strongly bullish), along with a detail string for diagnostics. The LLM
          reads these signals, cross-references volatility and regime data, and
          decides position sizing and direction.
        </P>

        <ComparisonTable />

        {/* --- MOMENTUM --- */}
        <H2>1. Momentum Strategies</H2>

        <P>
          Momentum strategies bet that assets moving strongly in one direction
          will continue. They are the bread and butter of trend-following systems
          and work best in directional markets with clear price trends.
        </P>

        <StrategyCard
          name="Simple Momentum"
          signal="% return over N bars"
          description="The simplest signal: compute percentage return over a lookback window. Positive return → bullish, negative → bearish. Fast to compute, but prone to whipsaws in choppy markets."
        />
        <StrategyCard
          name="Dual Momentum"
          signal="short-term vs long-term divergence"
          description="Compares short-term momentum against long-term momentum. When both agree, the signal is strong. When they diverge, it can detect regime shifts early — at the cost of occasional false starts."
        />
        <StrategyCard
          name="Breakout"
          signal="N-period high/low break"
          description="Fires a full ±1.0 signal when price breaks the highest high or lowest low over N periods. Binary and decisive — ideal for catching strong moves, but generates false signals in sideways markets."
        />
        <StrategyCard
          name="Donchian Channel"
          signal="normalised position in channel"
          description="Maps price position within the Donchian Channel (highest high to lowest low). Near the top → bullish, near bottom → bearish. Smoother than raw breakout, good for position sizing."
        />
        <StrategyCard
          name="MA Crossover"
          signal="(fast SMA − slow SMA) / slow"
          description="Classic moving average crossover. Signal magnitude scales with the gap between fast and slow SMA, giving proportional conviction rather than binary entries."
        />
        <StrategyCard
          name="EMA Crossover"
          signal="exponential MA cross"
          description="Same logic as MA Crossover but uses exponential averages. Reacts faster to recent price changes, which helps in volatile crypto markets but increases whipsaw risk."
        />
        <StrategyCard
          name="MACD Signal"
          signal="MACD line vs signal line"
          description="Measures the divergence between the MACD line and its signal line. Combines trend detection with momentum strength — widely used across traditional and crypto markets alike."
        />
        <StrategyCard
          name="Ichimoku"
          signal="Tenkan/Kijun cross + cloud position"
          description="Multi-timeframe system: Tenkan-sen / Kijun-sen crossover layered with price position relative to the Kumo cloud. Rich signal but requires more data for warm-up."
        />

        <Callout>
          Momentum strategies dominate in trending markets. In Artic, the LLM
          up-weights them when ADX (trend strength) is high and volatility is
          expanding.
        </Callout>

        {/* --- MEAN REVERSION --- */}
        <H2>2. Mean Reversion Strategies</H2>

        <P>
          Mean reversion strategies assume that prices oscillate around a fair
          value and will revert after extreme moves. They work best in
          range-bound, liquid markets and tend to underperform during strong
          trends.
        </P>

        <StrategyCard
          name="Z-Score"
          signal="inverted deviation from rolling mean"
          description="Computes how many standard deviations price sits from its rolling mean, then inverts it. A z-score of +2 generates a bearish signal (expecting reversion down). Simple, robust, and parameters-light."
        />
        <StrategyCard
          name="Bollinger Reversion"
          signal="fade Bollinger Band extremes"
          description="When price touches or exceeds the upper Bollinger Band, go short; when it hits the lower band, go long. Signal intensity scales with how far price has penetrated the band."
        />
        <StrategyCard
          name="RSI Signal"
          signal="oversold (<30) / overbought (>70)"
          description="The classic Relative Strength Index. Below 30 → long, above 70 → short. Signal is proportional to the distance from the 50 midline. Works well with confirmation from other signals."
        />
        <StrategyCard
          name="Stochastic Signal"
          signal="%K/%D extremes"
          description="Similar logic to RSI but uses the Stochastic Oscillator (%K and %D lines). More sensitive to short-term moves, making it useful for intraday entries."
        />
        <StrategyCard
          name="Range Support/Resistance"
          signal="fade recent highs/lows"
          description="Identifies recent local highs and lows as support/resistance levels, then fades moves into those zones. Simple but effective in markets that respect range boundaries."
        />
        <StrategyCard
          name="Linear Regression Channel"
          signal="deviation from trend line"
          description="Fits a linear regression to price, then measures deviation from the trend line. Combines mean reversion with trend awareness — revert to the trend, not just the mean."
        />

        <Callout>
          Mean reversion strategies are the counterbalance to momentum. The LLM
          switches to them when ADX is low and Bollinger Bandwidth is
          contracting, indicating a range-bound regime.
        </Callout>

        {/* --- VOLATILITY --- */}
        <H2>3. Volatility Strategies</H2>

        <P>
          Volatility strategies don&apos;t bet on direction per se — they bet on
          the expansion or contraction of price movement. They are especially
          valuable around events, news releases, and regime transitions.
        </P>

        <StrategyCard
          name="ATR Breakout"
          signal="candle range > ATR × multiplier"
          description="Fires when a single candle's range exceeds a multiple of the Average True Range. Catches explosive moves early but needs tight risk management as the trade is already extended."
        />
        <StrategyCard
          name="Bollinger Squeeze"
          signal="low-vol consolidation → breakout"
          description="Detects when Bollinger Bands narrow (squeeze), indicating compressed volatility, then signals the direction of the breakout. High win rate on the initial expansion but requires patience during the squeeze phase."
        />
        <StrategyCard
          name="Keltner-Bollinger"
          signal="Keltner bands vs Bollinger bands"
          description="Compares ATR-based Keltner Channels against standard-deviation-based Bollinger Bands. When Bollinger fits inside Keltner, a squeeze is on. Breakout direction determines signal. More nuanced than Bollinger Squeeze alone."
        />

        <Callout>
          Volatility strategies act as regime detectors. Artic&apos;s LLM uses
          them as confirming filters — if volatility is compressing, it reduces
          position size across all strategies until a breakout confirms
          direction.
        </Callout>

        {/* --- VOLUME / ORDER FLOW --- */}
        <H2>4. Volume & Order Flow Strategies</H2>

        <P>
          Price tells you what happened; volume tells you how much conviction was
          behind it. These strategies incorporate trade volume and derivatives
          data to gauge the quality of moves.
        </P>

        <StrategyCard
          name="VWAP Deviation"
          signal="distance from volume-weighted avg price"
          description="VWAP is the benchmark for institutional execution. When price deviates significantly above VWAP, short-term traders tend to sell; below, they buy. Artic uses this as an intraday anchor."
        />
        <StrategyCard
          name="OBV Trend"
          signal="On-Balance Volume slope"
          description="Cumulates volume on up-days and subtracts volume on down-days. Rising OBV confirms bullish moves; divergence between OBV and price is a powerful early warning for reversals."
        />
        <StrategyCard
          name="Funding Bias"
          signal="fade extreme funding rates"
          description="Specific to perpetual futures. When funding rate is extremely positive (longs paying shorts), the market is over-leveraged long — and vice versa. Fading extremes captures reversion in derivatives markets."
        />

        <Callout>
          Volume strategies add a conviction layer. The LLM uses OBV divergence
          to validate or override momentum signals — a rising price with falling
          OBV triggers caution.
        </Callout>

        {/* --- STATISTICAL / ADVANCED --- */}
        <H2>5. Statistical & Advanced Strategies</H2>

        <P>
          These strategies use more sophisticated mathematical models. They
          tend to be more robust to noise but require longer warm-up periods and
          more data to produce stable signals.
        </P>

        <StrategyCard
          name="Kalman Fair Value"
          signal="1D Kalman filter price estimate"
          description="Uses a Kalman filter to estimate the 'true' price, filtering out noise. Trades deviations from this fair value estimate. Adapts its smoothing dynamically based on recent forecast accuracy."
        />
        <StrategyCard
          name="ADX Filter"
          signal="+DI / −DI with trend strength"
          description="The Average Directional Index measures trend strength, not direction. Artic uses it as a meta-signal: high ADX → enable momentum strategies; low ADX → switch to mean reversion."
        />
        <StrategyCard
          name="Supertrend"
          signal="ATR-based dynamic support/resistance"
          description="Plots dynamic stop levels above and below price using ATR. When price crosses above the stop, it flips bullish (and vice versa). Clean binary signals with built-in risk levels."
        />

        <Callout>
          Statistical strategies serve as the backbone of Artic&apos;s
          meta-layer. ADX and Kalman outputs directly influence how the LLM
          weights every other strategy category.
        </Callout>

        {/* --- HOW THE LLM SELECTS --- */}
        <H2>How the LLM Selects Strategies</H2>

        <P>
          The core innovation in Artic is not any individual strategy — it is the
          dynamic selection layer. Here is how it works:
        </P>

        <div className="my-6 space-y-3">
          {[
            {
              step: "01",
              title: "Regime Detection",
              desc: "ADX, Bollinger Bandwidth, and volatility metrics classify the current market as trending, ranging, or transitioning.",
            },
            {
              step: "02",
              title: "Signal Collection",
              desc: "All 30+ strategies compute their signals independently. Each returns a normalised value and diagnostic detail.",
            },
            {
              step: "03",
              title: "LLM Evaluation",
              desc: "The language model receives signal values, regime classification, recent performance data, and risk constraints. It reasons about which strategy family fits the current conditions.",
            },
            {
              step: "04",
              title: "Position Sizing",
              desc: "Based on conviction level and volatility, the LLM sets position size. High-confidence regime matches get larger allocations; ambiguous conditions get scaled down.",
            },
            {
              step: "05",
              title: "Continuous Adaptation",
              desc: "Every tick cycle, the LLM re-evaluates. If the regime shifts mid-trade, it can reduce exposure or rotate to a different strategy — no manual intervention needed.",
            },
          ].map((item) => (
            <div
              key={item.step}
              className="flex gap-4 p-4 rounded-xl border border-white/8 bg-white/3"
            >
              <span className="text-xl font-bold text-orange/50 font-mono shrink-0">
                {item.step}
              </span>
              <div>
                <p className="text-sm font-semibold text-white mb-1">
                  {item.title}
                </p>
                <p className="text-[13px] text-white/45 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* --- CONCLUSION --- */}
        <H2>Conclusion</H2>

        <P>
          No single strategy wins in all market conditions. Momentum thrives in
          trends but bleeds in ranges. Mean reversion captures bounces but gets
          steamrolled by breakouts. Volatility strategies detect regime shifts
          but need patience.
        </P>

        <P>
          The insight behind Artic is that the selection problem — which strategy
          to use right now — is itself a reasoning problem. Language models
          excel at synthesising disparate signals, weighing trade-offs, and
          making contextual decisions. By pairing 30+ deterministic quant
          strategies with an LLM orchestrator, Artic gets the best of both
          worlds: rigorous, tested signal generation and flexible, adaptive
          strategy selection.
        </P>

        <div className="h-px bg-white/8 mt-16 mb-8" />

        {/* Back to blog */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          All posts
        </Link>
      </article>
      <Footer />
    </>
  );
}

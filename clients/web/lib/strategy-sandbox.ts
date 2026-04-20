/**
 * Mirror of the alpha RestrictedPython sandbox policy (docs/alpha/security-model.md).
 * Server-side is the source of truth — this is a client-side lint so authors get
 * instant feedback before hitting Save.
 */

export const ALLOWED_IMPORTS = ["math", "statistics", "numpy", "talib"] as const

export const ALLOWED_BUILTINS = [
  "abs", "min", "max", "sum", "len", "range", "enumerate", "zip", "map",
  "filter", "sorted", "round", "list", "tuple", "dict", "set", "bool", "int",
  "float", "str",
] as const

export const FORBIDDEN_NAMES = [
  "open", "__import__", "eval", "exec", "compile", "getattr", "setattr",
  "globals", "locals", "vars", "object", "type",
] as const

export const FORBIDDEN_MODULES = [
  "os", "sys", "subprocess", "socket", "urllib", "requests", "httpx", "pathlib",
  "shutil", "threading", "asyncio", "multiprocessing",
] as const

export const CPU_BUDGET_MS = 500
export const MEMORY_BUDGET_MB = 64

export const REQUIRED_FN = "strategy"
export const SIGNATURE = "(plan, price_history, candles) -> (signal: float, detail: str)"

export const STARTER_CODE = `# RestrictedPython sandboxed — see lint panel for allowed symbols.
# Signature: strategy(plan, price_history, candles) -> (signal: float, detail: str)
# signal is a float in [-1, 1]; + = bullish, - = bearish, 0 = flat.

def strategy(plan, price_history, candles):
    # example: short-term momentum with a 20-candle lookback
    if len(candles) < 20:
        return 0.0, "warming up"

    window = candles[-20:]
    avg_close = sum(c["close"] for c in window) / 20
    price = price_history[-1]

    threshold = plan.get("threshold", 0.002)
    diff = (price - avg_close) / avg_close

    if diff > threshold:
        return 1.0, f"above 20-avg by {diff * 100:.2f}%"
    if diff < -threshold:
        return -1.0, f"below 20-avg by {diff * 100:.2f}%"
    return 0.0, "in band"
`

export interface LintIssue {
  severity: "error" | "warn" | "info"
  line: number
  message: string
  token?: string
}

/** Simple substring/regex lint. Not a real parser — server-side is authoritative. */
export function lintStrategy(code: string): LintIssue[] {
  const issues: LintIssue[] = []
  const lines = code.split("\n")

  // Must define strategy()
  const hasFn = /^\s*def\s+strategy\s*\(/m.test(code)
  if (!hasFn) {
    issues.push({
      severity: "error",
      line: 1,
      message: `Missing required \`def ${REQUIRED_FN}(plan, price_history, candles):\`.`,
    })
  }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i]
    // Skip comments + strings (naïve — ignores multi-line strings)
    const line = raw.replace(/#.*$/, "")

    // Forbidden names used as function calls or bare references
    for (const name of FORBIDDEN_NAMES) {
      const re = new RegExp(`(?<![\\w.])${escape(name)}\\s*\\(`)
      if (re.test(line)) {
        issues.push({
          severity: "error",
          line: i + 1,
          token: name,
          message: `\`${name}(\` is blocked by the sandbox — runtime raises ImportError/NameError.`,
        })
      }
    }

    // Dunder attribute access: .__foo__
    const dunder = line.match(/\.__[A-Za-z_][A-Za-z0-9_]*__/)
    if (dunder) {
      issues.push({
        severity: "error",
        line: i + 1,
        token: dunder[0],
        message: `Dunder attribute access (\`${dunder[0]}\`) is blocked.`,
      })
    }

    // import X / from X import ...
    const imp = line.match(/^\s*(?:from\s+([\w.]+)\s+import\s+|import\s+([\w.]+))/)
    if (imp) {
      const mod = (imp[1] || imp[2] || "").split(".")[0]
      if (!mod) continue
      if (FORBIDDEN_MODULES.includes(mod as (typeof FORBIDDEN_MODULES)[number])) {
        issues.push({
          severity: "error",
          line: i + 1,
          token: mod,
          message: `\`${mod}\` is not importable in the sandbox (no network / filesystem / subprocess).`,
        })
      } else if (
        !ALLOWED_IMPORTS.includes(mod as (typeof ALLOWED_IMPORTS)[number])
      ) {
        issues.push({
          severity: "warn",
          line: i + 1,
          token: mod,
          message: `\`${mod}\` isn't on the allow-list. Allowed: ${ALLOWED_IMPORTS.join(", ")}.`,
        })
      }
    }
  }

  // Size + tick cadence info
  const bytes = new Blob([code]).size
  if (bytes > 16_384) {
    issues.push({
      severity: "warn",
      line: 1,
      message: `Code is ${(bytes / 1024).toFixed(1)} KB — strategies over ~16 KB tend to hit the ${CPU_BUDGET_MS}ms tick budget.`,
    })
  }
  return issues
}

function escape(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

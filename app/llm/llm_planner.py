"""
LLM-based strategy planner — multi-model: OpenAI (GPT), Anthropic (Claude), DeepSeek.
Called once at session start for strategy planning; supervisor checks on cycle.
Uses MarketRegimeSummary for compact, feature-rich market analysis.
"""
import os
import json
from pathlib import Path
from typing import Optional, Tuple, Literal, List
from datetime import datetime
from ..schemas import StrategyPlan, MarketRegimeSummary, SupervisorResponse
from ..market.market import MarketData
from ..market.market_analysis import MarketAnalyzer

Provider = Literal["openai", "anthropic", "deepseek", "gemini"]


def _extract_json(text: str) -> str:
    """Extract JSON object from LLM response, handling markdown fences and extra text."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # Find first { and matching }
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return text


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_env_file(key: str) -> Optional[str]:
    for _root in (_project_root(), Path.cwd(), _project_root().parent):
        _env = _root / ".env"
        if not _env.is_file():
            continue
        try:
            with open(_env, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        val = v.strip().strip('"').strip("'").strip()
                        return val if val else None
        except Exception:
            continue
    return None


def _load_project_env() -> None:
    try:
        from dotenv import load_dotenv
        for _root in (_project_root(), Path.cwd()):
            _env = _root / ".env"
            if _env.is_file():
                load_dotenv(_env, override=True)
                break
    except Exception:
        pass
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY"):
        if not (os.getenv(key) or "").strip():
            val = _read_env_file(key)
            if val:
                os.environ[key] = val


class LLMPlanner:
    """
    Multi-model LLM planner: OpenAI (GPT), Anthropic (Claude), or DeepSeek.
    Uses MarketRegimeSummary for strategy planning and supervisor checks.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        cmc_api_key: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ):
        _load_project_env()
        _openai = (openai_api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        _anthropic = (anthropic_api_key or os.getenv("ANTHROPIC_API_KEY") or "").strip()
        _deepseek = (deepseek_api_key or os.getenv("DEEPSEEK_API_KEY") or "").strip()
        _gemini = (gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.openai_api_key = _openai if _openai else None
        self.anthropic_api_key = _anthropic if _anthropic else None
        self.deepseek_api_key = _deepseek if _deepseek else None
        self.gemini_api_key = _gemini if _gemini else None
        self.llm_model_override = (os.getenv("LLM_MODEL") or "").strip() or None
        _provider = (llm_provider or os.getenv("LLM_PROVIDER") or "").strip().lower()
        if _provider in ("openai", "anthropic", "deepseek", "gemini"):
            self._llm_provider: Optional[Provider] = _provider
        else:
            self._llm_provider = (
                "openai" if self.openai_api_key
                else ("anthropic" if self.anthropic_api_key
                      else ("deepseek" if self.deepseek_api_key
                            else ("gemini" if self.gemini_api_key else None)))
            )
        self._openai_client = None
        self._anthropic_client = None
        self._deepseek_client = None
        self._gemini_client = None
        self.market_data = None
        self.analyzer = MarketAnalyzer()
        twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY")
        if twelve_data_api_key:
            try:
                self.market_data = MarketData(twelve_data_api_key=twelve_data_api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize MarketData: {e}")

    def _get_provider(self, override: Optional[str] = None) -> Optional[Provider]:
        override = (override or "").strip().lower() or None
        if override == "openai" and self.openai_api_key:
            return "openai"
        if override == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        if override == "deepseek" and self.deepseek_api_key:
            return "deepseek"
        if override == "gemini" and self.gemini_api_key:
            return "gemini"
        if override == "anthropic":
            print("[LLM] Requested Claude but ANTHROPIC_API_KEY not set; falling back.")
        if override == "deepseek":
            print("[LLM] Requested DeepSeek but DEEPSEEK_API_KEY not set; falling back.")
        if override == "gemini":
            print("[LLM] Requested Gemini but GEMINI_API_KEY not set; falling back.")
        if self._llm_provider == "openai" and self.openai_api_key:
            return "openai"
        if self._llm_provider == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        if self._llm_provider == "deepseek" and self.deepseek_api_key:
            return "deepseek"
        if self._llm_provider == "gemini" and self.gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        if self.anthropic_api_key:
            return "anthropic"
        if self.deepseek_api_key:
            return "deepseek"
        if self.gemini_api_key:
            return "gemini"
        return None

    def _has_llm(self) -> bool:
        return self._get_provider() is not None

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._openai_client = OpenAI(api_key=self.openai_api_key)
        return self._openai_client

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            from anthropic import Anthropic
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self._anthropic_client = Anthropic(api_key=self.anthropic_api_key)
        return self._anthropic_client

    def _get_deepseek_client(self):
        if self._deepseek_client is None:
            from openai import OpenAI
            if not self.deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY not set")
            self._deepseek_client = OpenAI(
                api_key=self.deepseek_api_key,
                base_url="https://api.deepseek.com",
            )
        return self._deepseek_client

    def _get_gemini_client(self):
        if self._gemini_client is None:
            from openai import OpenAI
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not set")
            self._gemini_client = OpenAI(
                api_key=self.gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
        return self._gemini_client

    def _chat(
        self,
        system_content: str,
        user_content: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        provider_override: Optional[str] = None,
    ) -> str:
        provider = self._get_provider(override=provider_override)
        if not provider:
            raise ValueError("No LLM provider. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, or GEMINI_API_KEY.")
        model_defaults = {
            "openai": "gpt-4o-mini",
            "deepseek": "deepseek-chat",
            "gemini": "gemini-2.0-flash",
            "anthropic": "claude-sonnet-4-5",
        }
        model = self.llm_model_override or model_defaults[provider]
        if provider in ("openai", "deepseek", "gemini"):
            client = {"openai": self._get_openai_client, "deepseek": self._get_deepseek_client, "gemini": self._get_gemini_client}[provider]()
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
            )
            # Gemini thinking models (2.5-*) need max_completion_tokens, not max_tokens
            if provider == "gemini" and "2.5" in model:
                kwargs["max_completion_tokens"] = max_tokens * 8
            else:
                kwargs["max_tokens"] = max_tokens
            response = client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip()
        # anthropic
        client = self._get_anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_content,
            messages=[{"role": "user", "content": user_content}],
            temperature=temperature,
        )
        content = ""
        if response.content and len(response.content) > 0:
            content = (response.content[0].text or "").strip()
        return content

    def plan_strategy(
        self,
        symbol: str,
        amount_usdt: float,
        leverage: int,
        risk_profile: str = "moderate",
        primary_timeframe: str = "15m",
        market_context: Optional[dict] = None,
        llm_provider: Optional[str] = None,
        indicators: Optional[List[str]] = None,
    ) -> StrategyPlan:
        if not self._has_llm():
            return self._get_default_strategy(risk_profile)
        try:
            bar_count, min_bars = self.analyzer.choose_timeframe_and_lookback(
                primary_timeframe=primary_timeframe,
                risk_profile=risk_profile
            )
            candles = None
            if self.market_data:
                candles = self.market_data.get_ohlcv_candles(
                    symbol=symbol,
                    timeframe=primary_timeframe,
                    bar_count=bar_count
                )
            if not candles or len(candles) < min_bars:
                return self._get_default_strategy(risk_profile)
            funding_data = self.market_data.get_funding_data(symbol, days=30) if self.market_data else None
            oi_data = self.market_data.get_open_interest_data(symbol, days=30) if self.market_data else None
            features = self.analyzer.compute_features(candles=candles, funding_data=funding_data, oi_data=oi_data)
            last_50_candles = candles[-50:] if len(candles) >= 50 else candles
            summary = self.analyzer.build_summary(
                symbol=symbol,
                primary_timeframe=primary_timeframe,
                bar_count=len(candles),
                features=features,
                last_50_candles=last_50_candles
            )
            strategy_shortlist = self.analyzer.suggest_strategy_shortlist(summary)
            return self._call_llm_with_summary(
                symbol=symbol,
                amount_usdt=amount_usdt,
                leverage=leverage,
                risk_profile=risk_profile,
                summary=summary,
                strategy_shortlist=strategy_shortlist,
                market_context=market_context,
                llm_provider=llm_provider,
                indicators=indicators,
            )
        except Exception as e:
            print(f"[WARN] LLM planning failed: {e}")
            return self._get_default_strategy(risk_profile)

    def _call_llm_with_summary(
        self,
        symbol: str,
        amount_usdt: float,
        leverage: int,
        risk_profile: str,
        summary: MarketRegimeSummary,
        strategy_shortlist: list,
        market_context: Optional[dict],
        llm_provider: Optional[str] = None,
        indicators: Optional[List[str]] = None,
    ) -> StrategyPlan:
        summary_dict = summary.model_dump(exclude_none=True)
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            elif isinstance(d, datetime):
                return d.isoformat()
            return d
        summary_dict = sanitize_dict(summary_dict)
        indicators_line = ""
        if indicators and len(indicators) > 0:
            indicators_line = f"\nUser-selected indicators to prioritize in analysis: {', '.join(indicators)}\n"
        prompt = f"""You are a quantitative trading strategist. Analyze the market regime and generate a trading strategy.

Symbol: {symbol}, Size: {amount_usdt} USDT, Leverage: {leverage}x, Risk: {risk_profile}
Timeframe: {summary.chosen_primary_timeframe}, Bars: {summary.bar_count_used}
{indicators_line}
Market Regime Summary:
{json.dumps(summary_dict, indent=2)}

Suggested strategies: {', '.join(strategy_shortlist)}

Return ONLY valid JSON:
{{"strategy": "<name>", "lookback": <5-50>, "threshold": <0.0002-0.003>, "max_loss_pct": <0.01-0.05>}}
For aggressive risk use lower threshold (0.0002-0.0005). Choose from: {', '.join(strategy_shortlist)}"""
        system = "Return valid JSON only. No other text."
        content = self._chat(system_content=system, user_content=prompt, temperature=0.3, max_tokens=1024, provider_override=llm_provider)
        content = _extract_json(content)
        return StrategyPlan(**json.loads(content))

    def _get_default_strategy(self, risk_profile: str) -> StrategyPlan:
        defaults = {
            "conservative": StrategyPlan(strategy="momentum", lookback=15, threshold=0.001, max_loss_pct=0.015),
            "moderate": StrategyPlan(strategy="momentum", lookback=10, threshold=0.0015, max_loss_pct=0.02),
            "aggressive": StrategyPlan(strategy="momentum", lookback=6, threshold=0.0003, max_loss_pct=0.035),
        }
        return defaults.get(risk_profile.lower(), defaults["moderate"])

    def supervisor_check(
        self,
        symbol: str,
        current_price: float,
        entry_price: float,
        side: str,
        unrealized_pnl_usdt: float,
        unrealized_pnl_pct: float,
        strategy_name: str,
        tp_sl_mode: str = "fixed",
        market_summary: Optional[dict] = None,
        llm_provider: Optional[str] = None,
    ) -> SupervisorResponse:
        if not self._has_llm():
            return SupervisorResponse(action="KEEP", reasoning="No LLM key.")
        try:
            prompt = f"""Trading supervisor. Position: {symbol} {side} @ ${entry_price:,.2f}, current ${current_price:,.2f}, PnL ${unrealized_pnl_usdt:,.2f} ({unrealized_pnl_pct*100:.2f}%). Strategy: {strategy_name}, TP/SL: {tp_sl_mode}.
Return JSON only: {{"action": "KEEP"|"CLOSE"|"ADJUST_TP_SL", "reasoning": "..."}}
KEEP=position fine. CLOSE=close now. ADJUST_TP_SL only if dynamic mode."""
            content = self._chat(system_content="Return valid JSON only.", user_content=prompt, temperature=0.2, max_tokens=200, provider_override=llm_provider)
            for marker in ["```json", "```"]:
                if marker in content:
                    parts = content.split(marker, 1)
                    if len(parts) > 1:
                        content = parts[1].split("```")[0].strip()
                    break
            start = content.find("{")
            if start >= 0:
                depth = 0
                for i in range(start, len(content)):
                    if content[i] == "{":
                        depth += 1
                    elif content[i] == "}":
                        depth -= 1
                        if depth == 0:
                            content = content[start : i + 1]
                            break
            data = json.loads(content)
            action = data.get("action", "KEEP").upper()
            if action not in ("KEEP", "CLOSE", "ADJUST_TP_SL"):
                action = "KEEP"
            if tp_sl_mode != "dynamic" and action == "ADJUST_TP_SL":
                action = "KEEP"
            return SupervisorResponse(action=action, reasoning=data.get("reasoning", ""))
        except Exception as e:
            return SupervisorResponse(action="KEEP", reasoning=f"Supervisor error: {e}")

    def get_full_analysis(
        self,
        symbol: str,
        amount_usdt: float,
        leverage: int,
        risk_profile: str = "moderate",
        primary_timeframe: str = "15m",
        market_context: Optional[dict] = None,
        llm_provider: Optional[str] = None,
        indicators: Optional[List[str]] = None,
    ) -> Tuple[MarketRegimeSummary, StrategyPlan, list, str, str]:
        bar_count, min_bars = self.analyzer.choose_timeframe_and_lookback(
            primary_timeframe=primary_timeframe,
            risk_profile=risk_profile
        )
        candles = None
        if self.market_data:
            candles = self.market_data.get_ohlcv_candles(symbol=symbol, timeframe=primary_timeframe, bar_count=bar_count)
        if not candles or len(candles) < min_bars:
            summary = MarketRegimeSummary(symbol=symbol, exchange="coinmarketcap", timestamp=datetime.now(), chosen_primary_timeframe=primary_timeframe, bar_count_used=0)
            strategy_plan = self._get_default_strategy(risk_profile)
            return summary, strategy_plan, ["momentum"], "Insufficient data. Using default momentum.", f"Default momentum: lookback {strategy_plan.lookback}, threshold {strategy_plan.threshold}"
        funding_data = self.market_data.get_funding_data(symbol, days=30) if self.market_data else None
        oi_data = self.market_data.get_open_interest_data(symbol, days=30) if self.market_data else None
        features = self.analyzer.compute_features(candles=candles, funding_data=funding_data, oi_data=oi_data)
        last_50_candles = candles[-50:] if len(candles) >= 50 else candles
        summary = self.analyzer.build_summary(symbol=symbol, primary_timeframe=primary_timeframe, bar_count=len(candles), features=features, last_50_candles=last_50_candles)
        strategy_shortlist = self.analyzer.suggest_strategy_shortlist(summary)
        try:
            strategy_plan = self._call_llm_with_summary(symbol=symbol, amount_usdt=amount_usdt, leverage=leverage, risk_profile=risk_profile, summary=summary, strategy_shortlist=strategy_shortlist, market_context=market_context, llm_provider=llm_provider, indicators=indicators)
        except Exception as e:
            print(f"[WARN] LLM strategy planning failed in full analysis: {e}")
            strategy_plan = self._get_default_strategy(risk_profile)
        analysis_paragraph, quant_algo_description = self._get_analysis_explanation(symbol=symbol, summary=summary, strategy_plan=strategy_plan, strategy_shortlist=strategy_shortlist, risk_profile=risk_profile, leverage=leverage, llm_provider=llm_provider, indicators=indicators)
        return summary, strategy_plan, strategy_shortlist, analysis_paragraph, quant_algo_description

    def _get_analysis_explanation(
        self,
        symbol: str,
        summary: MarketRegimeSummary,
        strategy_plan: StrategyPlan,
        strategy_shortlist: list,
        risk_profile: str,
        leverage: int,
        llm_provider: Optional[str] = None,
        indicators: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        if not self._has_llm():
            return (
                f"Based on market analysis, {strategy_plan.strategy} recommended for {symbol} ({risk_profile}).",
                f"Quant executes {strategy_plan.strategy}: lookback {strategy_plan.lookback}, threshold {strategy_plan.threshold}, max loss {strategy_plan.max_loss_pct*100:.2f}%.",
            )
        summary_dict = summary.model_dump(exclude_none=True)
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            elif isinstance(d, datetime):
                return d.isoformat()
            return d
        summary_dict = sanitize_dict(summary_dict)
        indicators_line = ""
        if indicators and len(indicators) > 0:
            indicators_line = f"\nPrioritize these indicators in analysis: {', '.join(indicators)}\n"
        prompt = f"""Quant analyst. Symbol: {symbol}, Risk: {risk_profile}, Leverage: {leverage}x.
{indicators_line}
Summary: {json.dumps(summary_dict, indent=2)}
Strategy: {strategy_plan.strategy}, lookback {strategy_plan.lookback}, threshold {strategy_plan.threshold}, max loss {strategy_plan.max_loss_pct*100:.2f}%.
Shortlist: {', '.join(strategy_shortlist)}
Return JSON: {{"analysis_paragraph": "5-8 sentence market analysis and justification (incorporate selected indicators)", "quant_algo_description": "4-6 sentence algorithm execution description"}}"""
        try:
            content = self._chat(system_content="Return valid JSON only.", user_content=prompt, temperature=0.4, max_tokens=1200, provider_override=llm_provider)
            content = _extract_json(content)
            result = json.loads(content)
            return result.get("analysis_paragraph", ""), result.get("quant_algo_description", "")
        except Exception as e:
            print(f"[WARN] Analysis explanation failed: {e}")
            return (
                f"Market analysis suggests {strategy_plan.strategy} for {symbol}.",
                f"Algorithm: {strategy_plan.strategy} with lookback {strategy_plan.lookback}, threshold {strategy_plan.threshold}.",
            )

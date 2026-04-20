"""
Agent manager — launches/stops multiple trading engine subprocesses.
Each agent runs uvicorn on its own port.
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

CONFIG_DIR = Path.home() / ".arcgenesis"
AGENTS_FILE = CONFIG_DIR / "agents.json"
BASE_PORT = 8010
STARTUP_TIMEOUT = 15  # seconds to wait for health check

EXCLUDE_FROM_SAVE = {"exchange_api_key", "exchange_secret", "llm_api_key"}


@dataclass
class AgentInfo:
    agent_id: str
    symbol: str
    amount_usdt: float
    leverage: int
    risk_profile: str
    port: int
    pid: Optional[int] = None
    created_at: str = ""
    alive: bool = False
    # extended fields
    name: str = ""
    timeframe: str = "15m"
    poll_seconds: float = 1.0
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
    tp_sl_mode: str = "fixed"
    live_mode: bool = False
    supervisor_interval: float = 60.0
    llm_provider: Optional[str] = None
    # per-agent API keys (memory only, not persisted)
    exchange_api_key: str = ""
    exchange_secret: str = ""
    llm_api_key: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        if not self.agent_id:
            self.agent_id = f"{self.symbol.lower()}-{self.port}"
        if not self.name:
            self.name = f"{self.symbol} Agent"

    @staticmethod
    def _llm_env_key(provider: Optional[str]) -> str:
        mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }
        return mapping.get(provider or "", "OPENAI_API_KEY")


class AgentManager:
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        self._engine_dir = Path(__file__).resolve().parent
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if AGENTS_FILE.exists():
            try:
                data = json.loads(AGENTS_FILE.read_text())
                for item in data:
                    info = AgentInfo(**item)
                    info.alive = False
                    self.agents[info.agent_id] = info
            except Exception:
                pass

    def _save(self):
        data = [
            {k: v for k, v in asdict(a).items() if k not in EXCLUDE_FROM_SAVE}
            for a in self.agents.values()
        ]
        AGENTS_FILE.write_text(json.dumps(data, indent=2))

    def _next_port(self) -> int:
        used = {a.port for a in self.agents.values() if a.alive}
        port = BASE_PORT
        while port in used:
            port += 1
        return port

    def _build_env(self, info: AgentInfo) -> dict:
        env = os.environ.copy()
        if info.exchange_api_key:
            env["EXCHANGE_API_KEY"] = info.exchange_api_key
        if info.exchange_secret:
            env["EXCHANGE_SECRET"] = info.exchange_secret
        if info.llm_api_key:
            env[AgentInfo._llm_env_key(info.llm_provider)] = info.llm_api_key
        return env

    def _start_request_body(self, info: AgentInfo) -> dict:
        body = {
            "symbol": info.symbol,
            "amount_usdt": info.amount_usdt,
            "leverage": info.leverage,
            "risk_profile": info.risk_profile,
            "primary_timeframe": info.timeframe,
            "poll_seconds": info.poll_seconds,
            "tp_sl_mode": info.tp_sl_mode,
            "live_mode": info.live_mode,
            "supervisor_interval_seconds": info.supervisor_interval,
        }
        if info.tp_pct is not None:
            body["tp_pct"] = info.tp_pct
        if info.sl_pct is not None:
            body["sl_pct"] = info.sl_pct
        if info.llm_provider:
            body["llm_provider"] = info.llm_provider
        return body

    async def _spawn_and_wait(self, info: AgentInfo) -> subprocess.Popen:
        env = self._build_env(info)
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(info.port)],
            cwd=str(self._engine_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        async with httpx.AsyncClient() as client:
            healthy = False
            for _ in range(STARTUP_TIMEOUT * 5):
                try:
                    r = await client.get(f"http://127.0.0.1:{info.port}/health", timeout=1)
                    if r.status_code == 200:
                        healthy = True
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.2)
            if not healthy:
                proc.kill()
                raise RuntimeError(f"Agent {info.agent_id} failed to start on port {info.port}")
            await client.post(
                f"http://127.0.0.1:{info.port}/start",
                json=self._start_request_body(info),
                timeout=30,
            )
        return proc

    async def launch(
        self,
        symbol: str,
        amount_usdt: float = 1000,
        leverage: int = 5,
        risk_profile: str = "moderate",
        name: str = "",
        timeframe: str = "15m",
        poll_seconds: float = 1.0,
        tp_pct: Optional[float] = None,
        sl_pct: Optional[float] = None,
        tp_sl_mode: str = "fixed",
        live_mode: bool = False,
        supervisor_interval: float = 60.0,
        llm_provider: Optional[str] = None,
        exchange_api_key: str = "",
        exchange_secret: str = "",
        llm_api_key: str = "",
    ) -> AgentInfo:
        port = self._next_port()
        agent_id = f"{symbol.lower()}-{port}"

        info = AgentInfo(
            agent_id=agent_id,
            symbol=symbol,
            amount_usdt=amount_usdt,
            leverage=leverage,
            risk_profile=risk_profile,
            port=port,
            name=name or f"{symbol} Agent",
            timeframe=timeframe,
            poll_seconds=poll_seconds,
            tp_pct=tp_pct,
            sl_pct=sl_pct,
            tp_sl_mode=tp_sl_mode,
            live_mode=live_mode,
            supervisor_interval=supervisor_interval,
            llm_provider=llm_provider,
            exchange_api_key=exchange_api_key,
            exchange_secret=exchange_secret,
            llm_api_key=llm_api_key,
        )

        proc = await self._spawn_and_wait(info)
        info.pid = proc.pid
        info.alive = True

        self.agents[agent_id] = info
        self._processes[agent_id] = proc
        self._save()
        return info

    async def start_agent(self, agent_id: str) -> AgentInfo:
        info = self.agents.get(agent_id)
        if not info:
            raise ValueError(f"Unknown agent: {agent_id}")
        if info.alive:
            return info

        info.port = self._next_port()
        proc = await self._spawn_and_wait(info)
        info.pid = proc.pid
        info.alive = True
        self._processes[agent_id] = proc
        self._save()
        return info

    async def stop(self, agent_id: str):
        info = self.agents.get(agent_id)
        if not info:
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"http://127.0.0.1:{info.port}/stop", timeout=5)
        except Exception:
            pass
        proc = self._processes.pop(agent_id, None)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        elif info.pid:
            try:
                os.kill(info.pid, signal.SIGTERM)
            except OSError:
                pass
        info.alive = False
        info.pid = None
        self._save()

    async def delete(self, agent_id: str):
        info = self.agents.get(agent_id)
        if not info:
            return
        if info.alive:
            await self.stop(agent_id)
        del self.agents[agent_id]
        self._processes.pop(agent_id, None)
        self._save()

    async def status(self, agent_id: str) -> Optional[dict]:
        info = self.agents.get(agent_id)
        if not info:
            return None
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"http://127.0.0.1:{info.port}/status", timeout=2)
                if r.status_code == 200:
                    info.alive = True
                    return r.json()
        except Exception:
            info.alive = False
        return None

    async def status_all(self) -> Dict[str, Optional[dict]]:
        results = {}
        tasks = {aid: self.status(aid) for aid in list(self.agents.keys())}
        for aid, coro in tasks.items():
            results[aid] = await coro
        return results

    async def logs(self, agent_id: str) -> Optional[dict]:
        info = self.agents.get(agent_id)
        if not info or not info.alive:
            return None
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"http://127.0.0.1:{info.port}/logs", timeout=3)
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass
        return None

    async def check_alive(self):
        for agent_id, info in list(self.agents.items()):
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"http://127.0.0.1:{info.port}/health", timeout=1)
                    info.alive = r.status_code == 200
            except Exception:
                info.alive = False

    async def stop_all(self):
        for agent_id in list(self.agents.keys()):
            if self.agents[agent_id].alive:
                await self.stop(agent_id)

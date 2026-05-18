"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as api from "@/lib/api"
import type { CreateAgentRequest, IndexerFilter, MarketplaceSort } from "@/lib/schemas"

// Conservative defaults — data is read-only fixture-backed today, so long
// stale times are fine. When real fetches land, per-hook overrides go here.
const LONG = 30_000
const SHORT = 5_000

export const qk = {
  agents: () => ["agents"] as const,
  agent: (id: string) => ["agents", id] as const,
  trades: (agentId?: string) => ["trades", agentId ?? "all"] as const,
  decisions: (agentId: string) => ["decisions", agentId] as const,
  chainWallet: () => ["chain-wallet"] as const,
  logs: (agentId: string) => ["logs", agentId] as const,
  strategies: () => ["strategies"] as const,
  strategy: (id: string) => ["strategies", id] as const,
  strategyStats: (hash: string) => ["strategies", "stats", hash] as const,
  marketplace: (sort: MarketplaceSort, limit: number, offset: number) =>
    ["marketplace", sort, limit, offset] as const,
  marketplaceItem: (id: string) => ["marketplace", "item", id] as const,
  credits: () => ["credits"] as const,
  ledger: () => ["ledger"] as const,
  indexer: (f: IndexerFilter) => ["indexer", f] as const,
  sessions: () => ["sessions"] as const,
  apiKeyHint: () => ["api-key-hint"] as const,
}

export const useAgents = () =>
  useQuery({
    queryKey: qk.agents(),
    queryFn: api.listAgents,
    staleTime: SHORT,
  })

export const useAgent = (id: string) =>
  useQuery({
    queryKey: qk.agent(id),
    queryFn: () => api.getAgent(id),
    staleTime: SHORT,
    enabled: !!id,
  })

export const useTrades = (agentId?: string) =>
  useQuery({
    queryKey: qk.trades(agentId),
    queryFn: () => api.listTrades(agentId),
    staleTime: SHORT,
  })

export const useDecisions = (agentId?: string) =>
  useQuery({
    queryKey: qk.decisions(agentId ?? ""),
    queryFn: () => api.listDecisions(agentId ?? ""),
    staleTime: SHORT,
    enabled: !!agentId,
  })

export const useChainWallet = () =>
  useQuery({
    queryKey: qk.chainWallet(),
    queryFn: api.getWallet,
    staleTime: SHORT,
    refetchInterval: 15_000,
  })

export const useWithdrawChainWallet = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ to, amount }: { to: string; amount: string }) =>
      api.withdrawWallet(to, amount),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.chainWallet() }),
  })
}

export const useLogs = (agentId: string) =>
  useQuery({
    queryKey: qk.logs(agentId),
    queryFn: () => api.listLogs(agentId),
    staleTime: SHORT,
    enabled: !!agentId,
  })

export const useStrategies = () =>
  useQuery({
    queryKey: qk.strategies(),
    queryFn: api.listStrategies,
    staleTime: LONG,
  })

export const useMarketplace = (
  sort: MarketplaceSort,
  limit = 50,
  offset = 0,
) =>
  useQuery({
    queryKey: qk.marketplace(sort, limit, offset),
    queryFn: () => api.listMarketplace(sort, limit, offset),
    staleTime: LONG,
  })

export const useMarketplaceItem = (id: string) =>
  useQuery({
    queryKey: qk.marketplaceItem(id),
    queryFn: () => api.getMarketplaceItem(id),
    staleTime: LONG,
    enabled: !!id,
  })

export const useStrategy = (id: string) =>
  useQuery({
    queryKey: qk.strategy(id),
    queryFn: () => api.getStrategy(id),
    staleTime: LONG,
    enabled: !!id,
  })

export const useStrategyStats = (hash: string | null | undefined) =>
  useQuery({
    queryKey: qk.strategyStats(hash ?? ""),
    queryFn: () => api.getStrategyStats(hash as string),
    staleTime: SHORT,
    enabled: !!hash,
  })

export const useCredits = () =>
  useQuery({
    queryKey: qk.credits(),
    queryFn: api.getCredits,
    staleTime: SHORT,
  })

export const useLedger = () =>
  useQuery({
    queryKey: qk.ledger(),
    queryFn: api.listLedger,
    staleTime: SHORT,
  })

export const useIndexer = (filter: IndexerFilter) =>
  useQuery({
    queryKey: qk.indexer(filter),
    queryFn: () => api.listIndexer(filter),
    staleTime: SHORT,
  })

export const useSessions = () =>
  useQuery({
    queryKey: qk.sessions(),
    queryFn: api.listSessions,
    staleTime: LONG,
  })

export const useApiKeyHint = () =>
  useQuery({
    queryKey: qk.apiKeyHint(),
    queryFn: api.getApiKeyHint,
    staleTime: LONG,
  })

// ── Mutations ──────────────────────────────────────────────────────────────

export const useCreateAgent = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateAgentRequest) => api.createAgent(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.agents() }),
  })
}

export const useStartAgent = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.startAgent(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: qk.agents() })
      qc.invalidateQueries({ queryKey: qk.agent(id) })
    },
  })
}

export const useStopAgent = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.stopAgent(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: qk.agents() })
      qc.invalidateQueries({ queryKey: qk.agent(id) })
    },
  })
}

export const useDeleteAgent = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteAgent(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.agents() }),
  })
}

export const useStartAllAgents = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.startAllAgents(),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.agents() }),
  })
}

export const useStopAllAgents = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.stopAllAgents(),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.agents() }),
  })
}

export const useSetSecret = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ keyName, value }: { keyName: string; value: string }) =>
      api.setSecret(keyName, value),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["secret-keys"] }),
  })
}

export const useSecretKeys = () =>
  useQuery({
    queryKey: ["secret-keys"],
    queryFn: api.listSecretKeys,
    staleTime: LONG,
  })

// ── Strategies + marketplace mutations ─────────────────────────────────────

export const useCreateStrategy = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: {
      name: string
      code: string
      params_schema?: Record<string, unknown>
    }) => api.createStrategy(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.strategies() }),
  })
}

export const usePatchStrategy = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string
      body: { name?: string; code?: string; params_schema?: Record<string, unknown> }
    }) => api.patchStrategy(id, body),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: qk.strategies() })
      qc.invalidateQueries({ queryKey: qk.strategy(vars.id) })
    },
  })
}

export const useDeleteStrategy = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteStrategy(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.strategies() }),
  })
}

export const useInstallStrategy = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (marketplaceId: string) => api.installStrategy(marketplaceId),
    onSuccess: (_, marketplaceId) => {
      qc.invalidateQueries({ queryKey: qk.strategies() })
      // Optimistic install count bump.
      qc.invalidateQueries({ queryKey: ["marketplace"] })
      qc.invalidateQueries({ queryKey: qk.marketplaceItem(marketplaceId) })
    },
  })
}

export const usePublishStrategy = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.publishStrategy(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["marketplace"] })
      qc.invalidateQueries({ queryKey: qk.strategies() })
    },
  })
}

export const useReportStrategy = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.reportMarketplaceItem(id, reason),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["marketplace"] })
      qc.invalidateQueries({ queryKey: qk.marketplaceItem(vars.id) })
    },
  })
}

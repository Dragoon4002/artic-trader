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
  logs: (agentId: string) => ["logs", agentId] as const,
  strategies: () => ["strategies"] as const,
  marketplace: (sort: MarketplaceSort) => ["marketplace", sort] as const,
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

export const useMarketplace = (sort: MarketplaceSort) =>
  useQuery({
    queryKey: qk.marketplace(sort),
    queryFn: () => api.listMarketplace(sort),
    staleTime: LONG,
  })

export const useMarketplaceItem = (id: string) =>
  useQuery({
    queryKey: qk.marketplaceItem(id),
    queryFn: () => api.getMarketplaceItem(id),
    staleTime: LONG,
    enabled: !!id,
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

"use client"

import { useEffect, useState, useCallback } from "react"

export type OnboardingStep = "llm_key" | "strategy" | "first_agent"

const STORAGE_KEY = "artic:onboarding:v1"
const ALL: OnboardingStep[] = ["llm_key", "strategy", "first_agent"]

interface State {
  completed: Record<OnboardingStep, boolean>
}

const empty: State = {
  completed: { llm_key: false, strategy: false, first_agent: false },
}

function read(): State {
  if (typeof window === "undefined") return empty
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return empty
    const parsed = JSON.parse(raw) as State
    // Shape-guard against older/broken saves.
    if (!parsed?.completed) return empty
    return {
      completed: {
        llm_key: !!parsed.completed.llm_key,
        strategy: !!parsed.completed.strategy,
        first_agent: !!parsed.completed.first_agent,
      },
    }
  } catch {
    return empty
  }
}

function write(state: State) {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Quota / disabled storage — onboarding state isn't critical.
  }
}

/**
 * localStorage-backed completion tracker for the 3-step onboarding flow.
 * Auth-aware completion (e.g. "user has a stored LLM key") can replace this
 * later by reading from the hub; the shape stays the same.
 */
export function useOnboarding() {
  const [state, setState] = useState<State>(empty)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setState(read())
    setHydrated(true)
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setState(read())
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  const setCompleted = useCallback(
    (step: OnboardingStep, done: boolean) => {
      setState((s) => {
        const next: State = {
          completed: { ...s.completed, [step]: done },
        }
        write(next)
        return next
      })
    },
    []
  )

  const reset = useCallback(() => {
    write(empty)
    setState(empty)
  }, [])

  const completedCount = ALL.filter((s) => state.completed[s]).length
  const allDone = completedCount === ALL.length

  return {
    hydrated,
    completed: state.completed,
    completedCount,
    totalSteps: ALL.length,
    allDone,
    setCompleted,
    reset,
  }
}

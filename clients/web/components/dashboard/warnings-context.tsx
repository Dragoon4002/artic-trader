"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react"

/**
 * Global toggle for non-critical UI warnings (PendingHub banners, etc).
 * Default is OFF — demos stay uncluttered. Choice persists to localStorage
 * and syncs across tabs via the `storage` event.
 */

const STORAGE_KEY = "artic:warnings-visible:v1"

interface Ctx {
  visible: boolean
  toggle: () => void
  set: (v: boolean) => void
}

const WarningsContext = createContext<Ctx | null>(null)

function read(): boolean {
  if (typeof window === "undefined") return false
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "1"
  } catch {
    return false
  }
}

function write(v: boolean) {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(STORAGE_KEY, v ? "1" : "0")
  } catch {
    /* ignored */
  }
}

export function WarningsProvider({ children }: PropsWithChildren) {
  // Hydrate from storage after mount to avoid SSR/CSR mismatch.
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    setVisible(read())
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setVisible(read())
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  const set = useCallback((v: boolean) => {
    setVisible(v)
    write(v)
  }, [])

  const toggle = useCallback(() => {
    setVisible((prev) => {
      write(!prev)
      return !prev
    })
  }, [])

  const value = useMemo<Ctx>(() => ({ visible, toggle, set }), [visible, toggle, set])
  return <WarningsContext.Provider value={value}>{children}</WarningsContext.Provider>
}

export function useWarningsVisible(): boolean {
  // Returns false (default-off) when no provider is mounted so PendingHub
  // stays hidden even if accidentally rendered outside the dashboard shell.
  return useContext(WarningsContext)?.visible ?? false
}

export function useWarnings(): Ctx {
  const ctx = useContext(WarningsContext)
  if (!ctx) {
    // Non-null API for the toggle button — it lives inside the provider.
    return { visible: false, toggle: () => {}, set: () => {} }
  }
  return ctx
}

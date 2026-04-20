export function shortenAddr(addr: string | null | undefined): string {
  if (!addr) return ""
  if (addr.length <= 16) return addr
  return `${addr.slice(0, 8)}…${addr.slice(-6)}`
}

export function displayName(address: string | null | undefined, username: string | null | undefined): string {
  if (!username) return shortenAddr(address)
  return username.endsWith(".init") ? username : `${username}.init`
}

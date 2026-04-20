import { PropsWithChildren } from "react"
import { AuthGuard } from "@/components/dashboard/auth-guard"
import { DashboardHeader } from "@/components/dashboard/header"

export default function DashboardLayout({ children }: PropsWithChildren) {
  return (
    <AuthGuard>
      <DashboardHeader />
      <main className="mx-auto w-full max-w-7xl px-6 py-10">{children}</main>
    </AuthGuard>
  )
}

import { PropsWithChildren } from "react"
import { AuthGuard } from "@/components/dashboard/auth-guard"
import { DashboardHeader } from "@/components/dashboard/header"
import { WarningsProvider } from "@/components/dashboard/warnings-context"

export default function DashboardLayout({ children }: PropsWithChildren) {
  return (
    <AuthGuard>
      <WarningsProvider>
        <DashboardHeader />
        <main className="mx-auto w-full max-w-[88rem] px-5 py-8 md:px-8 md:py-10">
          {children}
        </main>
      </WarningsProvider>
    </AuthGuard>
  )
}

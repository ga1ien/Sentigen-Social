"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { Bell, Settings, LogOut, User, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { useUser } from "@/contexts/user-context"
import { env } from "@/lib/env"

export function DashboardNav() {
	const { theme, setTheme } = useTheme()
	const router = useRouter()
	const { toast } = useToast()
	const { user, loading, signOut } = useUser()

	const handleSignOut = async () => {
		try {
			await signOut()
			router.push('/auth/login')
		} catch (error) {
			toast({
				title: "Error",
				description: "Failed to sign out. Please try again.",
				variant: "destructive",
			})
		}
	}

	return (
		<header className="border-b bg-background/70 backdrop-blur supports-[backdrop-filter]:bg-background/40">
			<div className="container mx-auto px-4 py-3 flex items-center justify-between">
				<div className="flex items-center gap-3">
					<h1 className="text-lg font-semibold tracking-wide lowercase">{env.NEXT_PUBLIC_APP_NAME}</h1>
					<Badge variant="secondary">Dashboard</Badge>
				</div>

				<div className="flex items-center gap-2">
					<Button variant="ghost" size="icon">
						<Bell className="h-4 w-4" />
					</Button>
					<Button
						variant="ghost"
						size="icon"
						onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
					>
						<Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
						<Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
						<span className="sr-only">Toggle theme</span>
					</Button>

					<DropdownMenu>
						<DropdownMenuTrigger asChild>
							<Button variant="ghost" className="h-8 px-3 rounded-full">
								<span className="text-sm">{loading ? '...' : (user?.email?.split('@')[0] || 'user')}</span>
							</Button>
						</DropdownMenuTrigger>
						<DropdownMenuContent className="w-56" align="end" forceMount>
							<DropdownMenuLabel className="font-normal">
								<div className="flex flex-col space-y-1">
									<p className="text-sm font-medium leading-none">
										{loading ? "Loading..." : (user?.user_metadata?.full_name || user?.email?.split('@')[0] || "User")}
									</p>
									<p className="text-xs leading-none text-muted-foreground">
										{loading ? "..." : (user?.email || "No email")}
									</p>
								</div>
							</DropdownMenuLabel>
							<DropdownMenuSeparator />
							<DropdownMenuItem>
								<User className="mr-2 h-4 w-4" />
								<span>Profile</span>
							</DropdownMenuItem>
							<DropdownMenuItem>
								<Settings className="mr-2 h-4 w-4" />
								<span>Settings</span>
							</DropdownMenuItem>
							<DropdownMenuSeparator />
							<DropdownMenuItem onClick={handleSignOut}>
								<LogOut className="mr-2 h-4 w-4" />
								<span>Log out</span>
							</DropdownMenuItem>
						</DropdownMenuContent>
					</DropdownMenu>
				</div>
			</div>
		</header>
	)
}

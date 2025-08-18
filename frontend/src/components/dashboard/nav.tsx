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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Settings, LogOut, User } from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "@/lib/toast-filter"
import { useUser } from "@/contexts/user-context"
import { env } from "@/lib/env"

export function DashboardNav() {
	const router = useRouter()
	// Using filtered toast that only shows warnings/errors
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
		<header className="pointer-events-none">
			<div className="container mx-auto px-4 py-3 flex items-center justify-end">
				<div className="flex items-center gap-2 pointer-events-auto">
					<DropdownMenu>
						<DropdownMenuTrigger asChild>
							<Button variant="ghost" className="relative h-10 w-10 rounded-full p-0">
								<Avatar className="h-9 w-9">
									<AvatarImage
										src={user?.user_metadata?.avatar_url || user?.user_metadata?.picture || ''}
										alt={user?.user_metadata?.full_name || user?.email || 'User avatar'}
									/>
									<AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-500 text-white">
										{loading ? '...' : (user?.user_metadata?.full_name || user?.email || 'U')?.charAt(0).toUpperCase()}
									</AvatarFallback>
								</Avatar>
							</Button>
						</DropdownMenuTrigger>
						<DropdownMenuContent className="w-56" align="end" forceMount>
							<DropdownMenuLabel className="font-normal">
								<div className="flex flex-col space-y-1">
									<p className="text-sm font-medium leading-none">
										{loading ? 'Loading...' : (user?.user_metadata?.full_name || user?.email || 'User')}
									</p>
									<p className="text-xs leading-none text-muted-foreground">
										{loading ? '...' : (user?.email || '')}
									</p>
								</div>
							</DropdownMenuLabel>
							<DropdownMenuSeparator />
							<DropdownMenuItem onClick={() => router.push('/dashboard/settings')}>
								<User className="mr-2 h-4 w-4" />
								<span>Account</span>
							</DropdownMenuItem>
							<DropdownMenuItem onClick={() => router.push('/dashboard/settings')}>
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

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Users,
  UserPlus,
  Mail,
  MoreVertical,
  Shield,
  Edit,
  Trash2,
  Crown,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface TeamMember {
  id: string
  name: string
  email: string
  avatar?: string
  role: 'owner' | 'admin' | 'editor' | 'member'
  status: 'active' | 'pending' | 'inactive'
  joinedAt: string
  lastActive: string
  permissions: string[]
}

interface Invitation {
  id: string
  email: string
  role: 'admin' | 'editor' | 'member'
  invitedBy: string
  invitedAt: string
  status: 'pending' | 'accepted' | 'expired'
}

// Real data will be loaded from workspace members
// For now, showing empty state until workspace integration is complete

export default function TeamPage() {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'admin' | 'editor' | 'member'>('member')
  const { toast } = useToast()

  const filteredMembers = teamMembers.filter(member => {
    const matchesSearch = member.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         member.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = roleFilter === 'all' || member.role === roleFilter
    return matchesSearch && matchesRole
  })

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner': return <Crown className="h-4 w-4 text-yellow-500" />
      case 'admin': return <Shield className="h-4 w-4 text-blue-500" />
      default: return null
    }
  }

  const getRoleBadge = (role: string) => {
    const colors = {
      owner: 'bg-yellow-500',
      admin: 'bg-blue-500',
      editor: 'bg-green-500',
      member: 'bg-gray-500'
    }
    return (
      <Badge className={`${colors[role as keyof typeof colors]} text-white`}>
        {role.charAt(0).toUpperCase() + role.slice(1)}
      </Badge>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />
      case 'inactive': return <XCircle className="h-4 w-4 text-red-500" />
      default: return null
    }
  }

  const handleInviteMember = async () => {
    if (!inviteEmail.trim()) {
      toast({
        title: "Email required",
        description: "Please enter an email address.",
        variant: "destructive",
      })
      return
    }

    // Check if already a member or invited
    const existingMember = teamMembers.find(m => m.email === inviteEmail)
    const existingInvite = invitations.find(i => i.email === inviteEmail)

    if (existingMember) {
      toast({
        title: "Already a member",
        description: "This person is already a team member.",
        variant: "destructive",
      })
      return
    }

    if (existingInvite) {
      toast({
        title: "Already invited",
        description: "An invitation has already been sent to this email.",
        variant: "destructive",
      })
      return
    }

    const newInvitation: Invitation = {
      id: Date.now().toString(),
      email: inviteEmail,
      role: inviteRole,
      invitedBy: 'John Doe', // Current user
      invitedAt: new Date().toISOString(),
      status: 'pending'
    }

    setInvitations(prev => [newInvitation, ...prev])
    setInviteEmail('')
    setInviteRole('member')
    setIsInviteDialogOpen(false)

    toast({
      title: "Invitation sent",
      description: `Invitation sent to ${inviteEmail}`,
    })
  }

  const handleRemoveMember = (memberId: string) => {
    setTeamMembers(prev => prev.filter(m => m.id !== memberId))
    toast({
      title: "Member removed",
      description: "Team member has been removed.",
    })
  }

  const handleCancelInvitation = (invitationId: string) => {
    setInvitations(prev => prev.filter(i => i.id !== invitationId))
    toast({
      title: "Invitation cancelled",
      description: "The invitation has been cancelled.",
    })
  }

  const handleResendInvitation = (invitationId: string) => {
    toast({
      title: "Invitation resent",
      description: "The invitation has been resent.",
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Team Management</h1>
          <p className="text-muted-foreground">
            Manage your team members and their permissions
          </p>
        </div>
        <Dialog open={isInviteDialogOpen} onOpenChange={setIsInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <UserPlus className="mr-2 h-4 w-4" />
              Invite Member
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite Team Member</DialogTitle>
              <DialogDescription>
                Send an invitation to join your workspace
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="role">Role</Label>
                <Select value={inviteRole} onValueChange={(value) => setInviteRole(value as 'admin' | 'editor' | 'member')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Admin - Full access except billing</SelectItem>
                    <SelectItem value="editor">Editor - Can create and edit content</SelectItem>
                    <SelectItem value="member">Member - Can view and comment</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsInviteDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleInviteMember}>
                Send Invitation
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="members" className="space-y-6">
        <TabsList>
          <TabsTrigger value="members">Team Members</TabsTrigger>
          <TabsTrigger value="invitations">
            Pending Invitations
            {invitations.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {invitations.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="members" className="space-y-6">
          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search team members..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="owner">Owner</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="editor">Editor</SelectItem>
                <SelectItem value="member">Member</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Team Members List */}
          <div className="grid gap-4">
            {filteredMembers.map((member) => (
              <Card key={member.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <Avatar className="h-12 w-12">
                        <AvatarImage src={member.avatar} alt={member.name} />
                        <AvatarFallback>
                          {member.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-semibold">{member.name}</h3>
                          {getRoleIcon(member.role)}
                          {getStatusIcon(member.status)}
                        </div>
                        <p className="text-sm text-muted-foreground">{member.email}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          {getRoleBadge(member.role)}
                          <span className="text-xs text-muted-foreground">
                            Joined {new Date(member.joinedAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="text-right text-sm text-muted-foreground">
                        <p>Last active</p>
                        <p>{new Date(member.lastActive).toLocaleDateString()}</p>
                      </div>
                      {member.role !== 'owner' && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit Role
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Mail className="mr-2 h-4 w-4" />
                              Send Message
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleRemoveMember(member.id)}
                              className="text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Remove Member
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredMembers.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center">
                <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No team members found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || roleFilter !== 'all'
                    ? 'Try adjusting your search or filters'
                    : 'Invite your first team member to get started'
                  }
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="invitations" className="space-y-6">
          {invitations.length > 0 ? (
            <div className="grid gap-4">
              {invitations.map((invitation) => (
                <Card key={invitation.id}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                          <Mail className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{invitation.email}</h3>
                          <p className="text-sm text-muted-foreground">
                            Invited by {invitation.invitedBy}
                          </p>
                          <div className="flex items-center space-x-2 mt-1">
                            {getRoleBadge(invitation.role)}
                            <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                              <Clock className="w-3 h-3 mr-1" />
                              Pending
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="text-right text-sm text-muted-foreground">
                          <p>Invited</p>
                          <p>{new Date(invitation.invitedAt).toLocaleDateString()}</p>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleResendInvitation(invitation.id)}>
                              <Mail className="mr-2 h-4 w-4" />
                              Resend Invitation
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleCancelInvitation(invitation.id)}
                              className="text-destructive"
                            >
                              <XCircle className="mr-2 h-4 w-4" />
                              Cancel Invitation
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Mail className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No pending invitations</h3>
                <p className="text-muted-foreground mb-4">
                  All team invitations have been accepted or there are no pending invitations.
                </p>
                <Button onClick={() => setIsInviteDialogOpen(true)}>
                  <UserPlus className="mr-2 h-4 w-4" />
                  Invite Team Member
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

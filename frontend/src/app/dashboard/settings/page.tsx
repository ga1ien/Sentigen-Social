'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  CreditCard,
  Key,
  Upload,
  Save,
  Trash2,
  Eye,
  EyeOff,
  Twitter,
  Linkedin,
  Facebook,
  Instagram,
  Link as LinkIcon,
  Unlink,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { toast } from '@/lib/toast-filter'
import { createClient } from '@/lib/supabase/client'

interface SocialAccount {
  platform: 'twitter' | 'linkedin' | 'facebook' | 'instagram'
  username: string
  connected: boolean
  lastSync: string
}

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  // Using filtered toast that only shows warnings/errors
  const supabase = createClient()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Real user data from Supabase
  const [userProfile, setUserProfile] = useState({
    name: '',
    email: '',
    avatar: '/avatars/01.png',
    bio: '',
    timezone: 'America/New_York',
    language: 'en'
  })

  useEffect(() => {
    const getUser = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser()
        if (user) {
          setUser(user)
          setUserProfile({
            name: user.user_metadata?.full_name || user.email?.split('@')[0] || '',
            email: user.email || '',
            avatar: user.user_metadata?.avatar_url || '/avatars/01.png',
            bio: user.user_metadata?.bio || '',
            timezone: user.user_metadata?.timezone || 'America/New_York',
            language: user.user_metadata?.language || 'en'
          })
        }
      } catch (error) {
        console.error('Error fetching user:', error)
      } finally {
        setLoading(false)
      }
    }

    getUser()
  }, [supabase.auth])

  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    pushNotifications: true,
    weeklyReports: true,
    postReminders: true,
    teamUpdates: false,
    marketingEmails: false
  })

  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([])
  const [loadingSocial, setLoadingSocial] = useState(true)

  // Load social accounts
  useEffect(() => {
    if (user && !loading) {
      loadSocialAccounts()
    }
  }, [user, loading])

  const loadSocialAccounts = async () => {
    try {
      setLoadingSocial(true)
      const response = await fetch('/api/social-accounts/connected', {
        headers: {
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        const accounts = Object.entries(data.accounts).map(([platform, info]: [string, any]) => ({
          platform: platform as 'twitter' | 'linkedin' | 'facebook' | 'instagram',
          username: info.username || '',
          connected: info.connected || false,
          lastSync: info.last_sync || ''
        }))
        setSocialAccounts(accounts)
      }
    } catch (error) {
      console.error('Error loading social accounts:', error)
      // Fallback to empty accounts
      setSocialAccounts([
        { platform: 'twitter', username: '', connected: false, lastSync: '' },
        { platform: 'linkedin', username: '', connected: false, lastSync: '' },
        { platform: 'facebook', username: '', connected: false, lastSync: '' },
        { platform: 'instagram', username: '', connected: false, lastSync: '' }
      ])
    } finally {
      setLoadingSocial(false)
    }
  }

  const [workspaceSettings, setWorkspaceSettings] = useState({
    workspaceName: 'My Workspace',
    defaultTimezone: 'America/New_York',
    brandColor: '#3b82f6',
    autoScheduling: true,
    contentApproval: false,
    aiSuggestions: true
  })

  const handleSaveProfile = async () => {
    setIsLoading(true)
    try {
      if (!user) {
        throw new Error('No user found')
      }

      // Update user metadata in Supabase
      const { error } = await supabase.auth.updateUser({
        data: {
          full_name: userProfile.name,
          bio: userProfile.bio,
          timezone: userProfile.timezone,
          language: userProfile.language,
          avatar_url: userProfile.avatar
        }
      })

      if (error) {
        throw error
      }

      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully.",
      })
    } catch (error) {
      console.error('Error updating profile:', error)
      toast({
        title: "Update failed",
        description: "There was an error updating your profile.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleConnectSocial = async (platform: string) => {
    try {
      const account = socialAccounts.find(acc => acc.platform === platform)
      const isCurrentlyConnected = account?.connected || false

      if (isCurrentlyConnected) {
        // Disconnect
        const response = await fetch(`/api/social-accounts/disconnect/${platform}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
          }
        })

        if (response.ok) {
          setSocialAccounts(prev =>
            prev.map(acc =>
              acc.platform === platform
                ? { ...acc, connected: false, lastSync: '' }
                : acc
            )
          )
          toast({
            title: "Account disconnected",
            description: `${platform} has been disconnected.`,
          })
        } else {
          throw new Error('Failed to disconnect account')
        }
      } else {
        // Connect
        const response = await fetch(`/api/social-accounts/connect/${platform}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          toast({
            title: "Connection initiated",
            description: data.instructions || `Please complete the ${platform} authorization process.`,
          })

          // Open connection URL if provided
          if (data.connection_url) {
            window.open(data.connection_url, '_blank')
          }

          // Refresh accounts after a short delay
          setTimeout(() => {
            loadSocialAccounts()
          }, 2000)
        } else {
          throw new Error('Failed to initiate connection')
        }
      }
    } catch (error) {
      console.error('Error managing social account:', error)
      toast({
        title: "Error",
        description: "Failed to update social account. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleDisconnectSocial = (platform: string) => {
    setSocialAccounts(prev =>
      prev.map(account =>
        account.platform === platform
          ? { ...account, connected: false, lastSync: '' }
          : account
      )
    )
    toast({
      title: "Account disconnected",
      description: `${platform.charAt(0).toUpperCase() + platform.slice(1)} account disconnected.`,
    })
  }

  const getSocialIcon = (platform: string) => {
    switch (platform) {
      case 'twitter': return <Twitter className="h-5 w-5" />
      case 'linkedin': return <Linkedin className="h-5 w-5" />
      case 'facebook': return <Facebook className="h-5 w-5" />
      case 'instagram': return <Instagram className="h-5 w-5" />
      default: return <Globe className="h-5 w-5" />
    }
  }

  const getSocialColor = (platform: string) => {
    switch (platform) {
      case 'twitter': return 'text-blue-500'
      case 'linkedin': return 'text-blue-700'
      case 'facebook': return 'text-blue-600'
      case 'instagram': return 'text-pink-500'
      default: return 'text-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">
            Manage your account and workspace preferences
          </p>
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="social">Social Accounts</TabsTrigger>
          <TabsTrigger value="workspace">Workspace</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center space-x-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={userProfile.avatar} alt={userProfile.name} />
                  <AvatarFallback>
                    {userProfile.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm">
                    <Upload className="mr-2 h-4 w-4" />
                    Change Avatar
                  </Button>
                  <p className="text-sm text-muted-foreground mt-1">
                    JPG, PNG or GIF. Max size 2MB.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={userProfile.name}
                    onChange={(e) => setUserProfile(prev => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={userProfile.email}
                    onChange={(e) => setUserProfile(prev => ({ ...prev, email: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  placeholder="Tell us about yourself..."
                  value={userProfile.bio}
                  onChange={(e) => setUserProfile(prev => ({ ...prev, bio: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={userProfile.timezone} onValueChange={(value) => setUserProfile(prev => ({ ...prev, timezone: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                      <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                      <SelectItem value="Europe/London">London (GMT)</SelectItem>
                      <SelectItem value="Europe/Paris">Paris (CET)</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="language">Language</Label>
                  <Select value={userProfile.language} onValueChange={(value) => setUserProfile(prev => ({ ...prev, language: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="it">Italian</SelectItem>
                      <SelectItem value="pt">Portuguese</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSaveProfile} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Choose how you want to be notified about updates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="email-notifications">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                  </div>
                  <Switch
                    id="email-notifications"
                    checked={notifications.emailNotifications}
                    onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, emailNotifications: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="push-notifications">Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive push notifications in your browser</p>
                  </div>
                  <Switch
                    id="push-notifications"
                    checked={notifications.pushNotifications}
                    onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, pushNotifications: checked }))}
                  />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="weekly-reports">Weekly Reports</Label>
                    <p className="text-sm text-muted-foreground">Get weekly analytics summaries</p>
                  </div>
                  <Switch
                    id="weekly-reports"
                    checked={notifications.weeklyReports}
                    onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, weeklyReports: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="post-reminders">Post Reminders</Label>
                    <p className="text-sm text-muted-foreground">Reminders for scheduled posts</p>
                  </div>
                  <Switch
                    id="post-reminders"
                    checked={notifications.postReminders}
                    onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, postReminders: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="team-updates">Team Updates</Label>
                    <p className="text-sm text-muted-foreground">Updates from team members</p>
                  </div>
                  <Switch
                    id="team-updates"
                    checked={notifications.teamUpdates}
                    onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, teamUpdates: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="marketing-emails">Marketing Emails</Label>
                    <p className="text-sm text-muted-foreground">Product updates and tips</p>
                  </div>
                  <Switch
                    id="marketing-emails"
                    checked={notifications.marketingEmails}
                    onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, marketingEmails: checked }))}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button>
                  <Save className="mr-2 h-4 w-4" />
                  Save Preferences
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="social" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Social Media Accounts</CardTitle>
              <CardDescription>
                Connect your social media accounts to publish content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {socialAccounts.map((account) => (
                <div key={account.platform} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className={`${getSocialColor(account.platform)}`}>
                      {getSocialIcon(account.platform)}
                    </div>
                    <div>
                      <h3 className="font-medium capitalize">{account.platform}</h3>
                      {account.connected ? (
                        <div className="flex items-center space-x-2">
                          <p className="text-sm text-muted-foreground">{account.username}</p>
                          <Badge variant="outline" className="text-green-600 border-green-600">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Connected
                          </Badge>
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">Not connected</p>
                      )}
                      {account.connected && account.lastSync && (
                        <p className="text-xs text-muted-foreground">
                          Last sync: {new Date(account.lastSync).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <div>
                    {account.connected ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDisconnectSocial(account.platform)}
                      >
                        <Unlink className="mr-2 h-4 w-4" />
                        Disconnect
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleConnectSocial(account.platform)}
                      >
                        <LinkIcon className="mr-2 h-4 w-4" />
                        Connect
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workspace" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Workspace Settings</CardTitle>
              <CardDescription>
                Configure your workspace preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="workspace-name">Workspace Name</Label>
                <Input
                  id="workspace-name"
                  value={workspaceSettings.workspaceName}
                  onChange={(e) => setWorkspaceSettings(prev => ({ ...prev, workspaceName: e.target.value }))}
                />
              </div>

              <div>
                <Label htmlFor="default-timezone">Default Timezone</Label>
                <Select
                  value={workspaceSettings.defaultTimezone}
                  onValueChange={(value) => setWorkspaceSettings(prev => ({ ...prev, defaultTimezone: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                    <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                    <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                    <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="brand-color">Brand Color</Label>
                <div className="flex items-center space-x-2">
                  <Input
                    id="brand-color"
                    type="color"
                    value={workspaceSettings.brandColor}
                    onChange={(e) => setWorkspaceSettings(prev => ({ ...prev, brandColor: e.target.value }))}
                    className="w-16 h-10"
                  />
                  <Input
                    value={workspaceSettings.brandColor}
                    onChange={(e) => setWorkspaceSettings(prev => ({ ...prev, brandColor: e.target.value }))}
                    placeholder="#3b82f6"
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="auto-scheduling">Auto Scheduling</Label>
                    <p className="text-sm text-muted-foreground">Automatically schedule posts at optimal times</p>
                  </div>
                  <Switch
                    id="auto-scheduling"
                    checked={workspaceSettings.autoScheduling}
                    onCheckedChange={(checked) => setWorkspaceSettings(prev => ({ ...prev, autoScheduling: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="content-approval">Content Approval</Label>
                    <p className="text-sm text-muted-foreground">Require approval before publishing</p>
                  </div>
                  <Switch
                    id="content-approval"
                    checked={workspaceSettings.contentApproval}
                    onCheckedChange={(checked) => setWorkspaceSettings(prev => ({ ...prev, contentApproval: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="ai-suggestions">AI Suggestions</Label>
                    <p className="text-sm text-muted-foreground">Enable AI-powered content suggestions</p>
                  </div>
                  <Switch
                    id="ai-suggestions"
                    checked={workspaceSettings.aiSuggestions}
                    onCheckedChange={(checked) => setWorkspaceSettings(prev => ({ ...prev, aiSuggestions: checked }))}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button>
                  <Save className="mr-2 h-4 w-4" />
                  Save Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>
                Manage your account security and privacy
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="current-password">Current Password</Label>
                <div className="relative">
                  <Input
                    id="current-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter current password"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              <div>
                <Label htmlFor="new-password">New Password</Label>
                <Input
                  id="new-password"
                  type="password"
                  placeholder="Enter new password"
                />
              </div>

              <div>
                <Label htmlFor="confirm-password">Confirm New Password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="Confirm new password"
                />
              </div>

              <div className="flex justify-end">
                <Button>
                  <Key className="mr-2 h-4 w-4" />
                  Update Password
                </Button>
              </div>

              <Separator />

              <div>
                <h3 className="text-lg font-medium mb-4">Two-Factor Authentication</h3>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Authenticator App</p>
                    <p className="text-sm text-muted-foreground">
                      Use an authenticator app to generate verification codes
                    </p>
                  </div>
                  <Button variant="outline">
                    Enable 2FA
                  </Button>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="text-lg font-medium mb-4 text-destructive">Danger Zone</h3>
                <div className="border border-destructive rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Delete Account</p>
                      <p className="text-sm text-muted-foreground">
                        Permanently delete your account and all data
                      </p>
                    </div>
                    <Button variant="destructive">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete Account
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="billing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Billing & Subscription</CardTitle>
              <CardDescription>
                Manage your subscription and billing information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium">Current Plan</h3>
                  <p className="text-sm text-muted-foreground">Professional Plan</p>
                  <Badge className="mt-1">Active</Badge>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">$29/month</p>
                  <p className="text-sm text-muted-foreground">Billed monthly</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-4">Payment Method</h3>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CreditCard className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <p className="font-medium">•••• •••• •••• 4242</p>
                      <p className="text-sm text-muted-foreground">Expires 12/25</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    Update
                  </Button>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-4">Billing History</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">January 2024</p>
                      <p className="text-sm text-muted-foreground">Professional Plan</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">$29.00</p>
                      <Button variant="ghost" size="sm">
                        Download
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">December 2023</p>
                      <p className="text-sm text-muted-foreground">Professional Plan</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">$29.00</p>
                      <Button variant="ghost" size="sm">
                        Download
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="outline">
                  Cancel Subscription
                </Button>
                <Button>
                  Upgrade Plan
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

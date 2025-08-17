"use client"

import { useState, useRef, useEffect } from 'react'
import { useUser } from '@/contexts/user-context'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import {
  Plus,
  Calendar as CalendarIcon,
  Clock,
  Edit,
  Trash2,
  Twitter,
  Linkedin,
  Facebook,
  Instagram,
  Youtube,
  Eye,
  Send
} from 'lucide-react'

interface CalendarEvent {
  id: string
  title: string
  start: string
  end?: string
  content: string
  platforms: string[]
  status: 'draft' | 'scheduled' | 'published' | 'failed'
  backgroundColor?: string
  borderColor?: string
}

const platformIcons = {
  twitter: Twitter,
  linkedin: Linkedin,
  facebook: Facebook,
  instagram: Instagram,
  youtube: Youtube,
}

const platformColors = {
  twitter: '#1DA1F2',
  linkedin: '#0077B5',
  facebook: '#1877F2',
  instagram: '#E4405F',
  youtube: '#FF0000',
}

const statusColors = {
  draft: '#6B7280',
  scheduled: '#3B82F6',
  published: '#10B981',
  failed: '#EF4444',
}

export default function CalendarPage() {
  const { user, loading } = useUser()
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loadingEvents, setLoadingEvents] = useState(true)

  useEffect(() => {
    if (user && !loading) {
      loadScheduledPosts()
    }
  }, [user, loading])

  const loadScheduledPosts = async () => {
    try {
      setLoadingEvents(true)
      // TODO: Load real scheduled posts from database
      // For now, show empty state
      setEvents([])
    } catch (error) {
      console.error('Error loading scheduled posts:', error)
    } finally {
      setLoadingEvents(false)
    }
  }

  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [isEventDialogOpen, setIsEventDialogOpen] = useState(false)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [newEvent, setNewEvent] = useState({
    title: '',
    content: '',
    platforms: [] as string[],
    date: '',
    time: '',
  })

  const calendarRef = useRef<FullCalendar>(null)
  const { toast } = useToast()

  const handleDateClick = (arg: { dateStr: string }) => {
    setSelectedDate(arg.dateStr)
    setNewEvent({
      ...newEvent,
      date: arg.dateStr,
      time: '09:00',
    })
    setIsCreateDialogOpen(true)
  }

  const handleEventClick = (arg: { event: { id: string } }) => {
    const event = events.find(e => e.id === arg.event.id)
    if (event) {
      setSelectedEvent(event)
      setIsEventDialogOpen(true)
    }
  }

  const handleEventDrop = (arg: { event: { id: string; start: Date | null } }) => {
    const eventId = arg.event.id
    const newStart = arg.event.start?.toISOString()

    if (newStart) {
      setEvents(prev => prev.map(event =>
        event.id === eventId
          ? { ...event, start: newStart }
          : event
      ))

      toast({
        title: "Event Moved",
        description: "Post has been rescheduled successfully.",
      })
    }
  }

  const handleCreateEvent = async () => {
    if (!newEvent.title || !newEvent.content || newEvent.platforms.length === 0) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive"
      })
      return
    }

    try {
      const eventDateTime = `${newEvent.date}T${newEvent.time}:00`
      const backgroundColor = newEvent.platforms.length === 1
        ? platformColors[newEvent.platforms[0] as keyof typeof platformColors]
        : '#8B5CF6'

      // TODO: Save to database via API
      const event: CalendarEvent = {
        id: Date.now().toString(),
        title: newEvent.title,
        start: eventDateTime,
        content: newEvent.content,
        platforms: newEvent.platforms,
        status: 'scheduled',
        backgroundColor,
        borderColor: backgroundColor,
      }

      setEvents(prev => [...prev, event])
      setIsCreateDialogOpen(false)
      setNewEvent({
        title: '',
        content: '',
        platforms: [],
        date: '',
        time: '',
      })

      toast({
        title: "Post Scheduled",
        description: "Your post has been added to the calendar.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to schedule post. Please try again.",
        variant: "destructive"
      })
    }
  }

  const handleDeleteEvent = (eventId: string) => {
    setEvents(prev => prev.filter(event => event.id !== eventId))
    setIsEventDialogOpen(false)
    setSelectedEvent(null)

    toast({
      title: "Post Deleted",
      description: "The scheduled post has been removed.",
    })
  }

  const handlePublishNow = (eventId: string) => {
    setEvents(prev => prev.map(event =>
      event.id === eventId
        ? {
            ...event,
            status: 'published',
            backgroundColor: statusColors.published,
            borderColor: statusColors.published,
          }
        : event
    ))
    setIsEventDialogOpen(false)

    toast({
      title: "Post Published",
      description: "Your post has been published immediately.",
    })
  }

  const handlePlatformToggle = (platform: string) => {
    setNewEvent(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }))
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'published': return 'default'
      case 'scheduled': return 'secondary'
      case 'draft': return 'outline'
      case 'failed': return 'destructive'
      default: return 'outline'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Content Calendar</h1>
          <p className="text-muted-foreground">
            Schedule and manage your social media posts across all platforms
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Schedule Post
        </Button>
      </div>

      {/* Calendar Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {events.filter(e => e.status === 'scheduled').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Published</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {events.filter(e => e.status === 'published').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Drafts</CardTitle>
            <Edit className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {events.filter(e => e.status === 'draft').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Week</CardTitle>
            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {events.filter(e => {
                const eventDate = new Date(e.start)
                const now = new Date()
                const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
                return eventDate >= now && eventDate <= weekFromNow
              }).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar */}
      <Card>
        <CardHeader>
          <CardTitle>Schedule Overview</CardTitle>
          <CardDescription>
            Click on a date to schedule a new post, or drag events to reschedule
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="calendar-container">
            <FullCalendar
              ref={calendarRef}
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
              }}
              events={events}
              dateClick={handleDateClick}
              eventClick={handleEventClick}
              eventDrop={handleEventDrop}
              editable={true}
              droppable={true}
              height="auto"
              eventDisplay="block"
              dayMaxEvents={3}
              moreLinkClick="popover"
            />
          </div>
        </CardContent>
      </Card>

      {/* Event Details Dialog */}
      <Dialog open={isEventDialogOpen} onOpenChange={setIsEventDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Post Details</DialogTitle>
            <DialogDescription>
              View and manage your scheduled post
            </DialogDescription>
          </DialogHeader>

          {selectedEvent && (
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-lg">{selectedEvent.title}</h3>
                <p className="text-sm text-muted-foreground">
                  Scheduled for {new Date(selectedEvent.start).toLocaleString()}
                </p>
              </div>

              <div className="space-y-2">
                <Label>Status</Label>
                <Badge variant={getStatusBadgeVariant(selectedEvent.status)}>
                  {selectedEvent.status.charAt(0).toUpperCase() + selectedEvent.status.slice(1)}
                </Badge>
              </div>

              <div className="space-y-2">
                <Label>Platforms</Label>
                <div className="flex flex-wrap gap-2">
                  {selectedEvent.platforms.map((platform) => {
                    const Icon = platformIcons[platform as keyof typeof platformIcons]
                    return (
                      <div key={platform} className="flex items-center space-x-2 bg-muted px-3 py-1 rounded-full">
                        <Icon className="h-4 w-4" />
                        <span className="text-sm capitalize">{platform}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Content</Label>
                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm whitespace-pre-wrap">{selectedEvent.content}</p>
                </div>
              </div>

              <div className="flex justify-between">
                <Button
                  variant="destructive"
                  onClick={() => handleDeleteEvent(selectedEvent.id)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>

                <div className="space-x-2">
                  <Button variant="outline">
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Button>
                  {selectedEvent.status === 'scheduled' && (
                    <Button onClick={() => handlePublishNow(selectedEvent.id)}>
                      <Send className="mr-2 h-4 w-4" />
                      Publish Now
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Event Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Schedule New Post</DialogTitle>
            <DialogDescription>
              Create and schedule a new social media post
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="event-date">Date</Label>
                <Input
                  id="event-date"
                  type="date"
                  value={newEvent.date}
                  onChange={(e) => setNewEvent(prev => ({ ...prev, date: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="event-time">Time</Label>
                <Input
                  id="event-time"
                  type="time"
                  value={newEvent.time}
                  onChange={(e) => setNewEvent(prev => ({ ...prev, time: e.target.value }))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="event-title">Title</Label>
              <Input
                id="event-title"
                placeholder="Enter post title..."
                value={newEvent.title}
                onChange={(e) => setNewEvent(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="event-content">Content</Label>
              <Textarea
                id="event-content"
                placeholder="Enter post content..."
                rows={4}
                value={newEvent.content}
                onChange={(e) => setNewEvent(prev => ({ ...prev, content: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label>Platforms</Label>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(platformIcons).map(([platform, Icon]) => (
                  <div
                    key={platform}
                    className={`flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                      newEvent.platforms.includes(platform)
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-muted/50'
                    }`}
                    onClick={() => handlePlatformToggle(platform)}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="text-sm capitalize">{platform}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateEvent}>
                Schedule Post
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <style jsx global>{`
        .fc-event {
          border-radius: 4px;
          border: none !important;
          padding: 2px 4px;
          font-size: 12px;
          cursor: pointer;
        }
        .fc-event:hover {
          opacity: 0.8;
        }
        .fc-daygrid-event {
          margin: 1px 0;
        }
        .fc-event-title {
          font-weight: 500;
        }
        .calendar-container .fc {
          font-family: inherit;
        }
        .fc-button {
          background-color: hsl(var(--primary)) !important;
          border-color: hsl(var(--primary)) !important;
          color: hsl(var(--primary-foreground)) !important;
        }
        .fc-button:hover {
          background-color: hsl(var(--primary)) !important;
          border-color: hsl(var(--primary)) !important;
          opacity: 0.9;
        }
        .fc-button:disabled {
          opacity: 0.5;
        }
        .fc-today-button {
          background-color: hsl(var(--secondary)) !important;
          border-color: hsl(var(--secondary)) !important;
          color: hsl(var(--secondary-foreground)) !important;
        }
      `}</style>
    </div>
  )
}

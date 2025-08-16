"use client"

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import Mention from '@tiptap/extension-mention'
import Color from '@tiptap/extension-color'
import { TextStyle } from '@tiptap/extension-text-style'
import Underline from '@tiptap/extension-underline'
import Strike from '@tiptap/extension-strike'
import CodeBlock from '@tiptap/extension-code-block'
import Blockquote from '@tiptap/extension-blockquote'
import BulletList from '@tiptap/extension-bullet-list'
import OrderedList from '@tiptap/extension-ordered-list'
import ListItem from '@tiptap/extension-list-item'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { 
  Bold, 
  Italic, 
  Underline as UnderlineIcon, 
  Strikethrough, 
  Code, 
  Quote, 
  List, 
  ListOrdered, 
  Link as LinkIcon, 
  Image as ImageIcon,
  Palette,
  Type,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Undo,
  Redo,
  Hash,
  AtSign
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState, useCallback } from 'react'

interface RichTextEditorProps {
  content?: string
  onChange?: (content: string) => void
  placeholder?: string
  maxLength?: number
  platforms?: string[]
  className?: string
  editable?: boolean
}

export function RichTextEditor({
  content = '',
  onChange,
  placeholder = 'Start writing your post...',
  maxLength = 2000,
  platforms = [],
  className,
  editable = true
}: RichTextEditorProps) {
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false)

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        bulletList: false,
        orderedList: false,
        listItem: false,
        blockquote: false,
        codeBlock: false,
        strike: false,
      }),
      Placeholder.configure({
        placeholder,
      }),
      CharacterCount.configure({
        limit: maxLength,
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-primary underline cursor-pointer',
        },
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'max-w-full h-auto rounded-lg',
        },
      }),
      Mention.configure({
        HTMLAttributes: {
          class: 'text-primary font-medium',
        },
        suggestion: {
          items: ({ query }) => {
            // Mock mention suggestions - in real app, this would fetch from API
            const suggestions = [
              'john_doe', 'jane_smith', 'company_account', 'team_lead'
            ]
            return suggestions
              .filter(item => item.toLowerCase().startsWith(query.toLowerCase()))
              .slice(0, 5)
          },
        },
      }),
      Color,
      TextStyle,
      Underline,
      Strike,
      CodeBlock.configure({
        HTMLAttributes: {
          class: 'bg-muted p-4 rounded-lg font-mono text-sm',
        },
      }),
      Blockquote.configure({
        HTMLAttributes: {
          class: 'border-l-4 border-primary pl-4 italic',
        },
      }),
      BulletList.configure({
        HTMLAttributes: {
          class: 'list-disc list-inside',
        },
      }),
      OrderedList.configure({
        HTMLAttributes: {
          class: 'list-decimal list-inside',
        },
      }),
      ListItem,
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: cn(
          'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none',
          'min-h-[200px] p-4'
        ),
      },
    },
  })

  const addImage = useCallback(() => {
    const url = window.prompt('Enter image URL:')
    if (url && editor) {
      editor.chain().focus().setImage({ src: url }).run()
    }
  }, [editor])

  const setLink = useCallback(() => {
    const previousUrl = editor?.getAttributes('link').href
    const url = window.prompt('Enter URL:', previousUrl)

    if (url === null) {
      return
    }

    if (url === '') {
      editor?.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }

    editor?.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }, [editor])

  const addHashtag = useCallback(() => {
    const hashtag = window.prompt('Enter hashtag (without #):')
    if (hashtag && editor) {
      editor.chain().focus().insertContent(`#${hashtag} `).run()
    }
  }, [editor])

  if (!editor) {
    return null
  }

  const characterCount = editor.storage.characterCount.characters()
  const wordCount = editor.storage.characterCount.words()

  // Platform-specific character limits
  const platformLimits = {
    twitter: 280,
    linkedin: 3000,
    facebook: 63206,
    instagram: 2200,
  }

  return (
    <div className={cn('border rounded-lg', className)}>
      {/* Toolbar */}
      <div className="border-b p-2 flex flex-wrap items-center gap-1">
        {/* Text Formatting */}
        <div className="flex items-center gap-1">
          <Button
            variant={editor.isActive('bold') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleBold().run()}
            disabled={!editor.can().chain().focus().toggleBold().run()}
          >
            <Bold className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('italic') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            disabled={!editor.can().chain().focus().toggleItalic().run()}
          >
            <Italic className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('underline') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            disabled={!editor.can().chain().focus().toggleUnderline().run()}
          >
            <UnderlineIcon className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('strike') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleStrike().run()}
            disabled={!editor.can().chain().focus().toggleStrike().run()}
          >
            <Strikethrough className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('code') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleCode().run()}
            disabled={!editor.can().chain().focus().toggleCode().run()}
          >
            <Code className="h-4 w-4" />
          </Button>
        </div>

        <Separator orientation="vertical" className="h-6" />

        {/* Lists and Quotes */}
        <div className="flex items-center gap-1">
          <Button
            variant={editor.isActive('bulletList') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('orderedList') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
          >
            <ListOrdered className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('blockquote') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
          >
            <Quote className="h-4 w-4" />
          </Button>
          <Button
            variant={editor.isActive('codeBlock') ? 'default' : 'ghost'}
            size="sm"
            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          >
            <Code className="h-4 w-4" />
          </Button>
        </div>

        <Separator orientation="vertical" className="h-6" />

        {/* Media and Links */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={setLink}
          >
            <LinkIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={addImage}
          >
            <ImageIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={addHashtag}
          >
            <Hash className="h-4 w-4" />
          </Button>
        </div>

        <Separator orientation="vertical" className="h-6" />

        {/* Undo/Redo */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().chain().focus().undo().run()}
          >
            <Undo className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().chain().focus().redo().run()}
          >
            <Redo className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Editor Content */}
      <EditorContent editor={editor} className="min-h-[200px]" />

      {/* Footer with stats and platform limits */}
      <div className="border-t p-2 flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>{wordCount} words</span>
          <span className={cn(
            characterCount > maxLength ? 'text-destructive' : '',
            characterCount > maxLength * 0.9 ? 'text-orange-500' : ''
          )}>
            {characterCount}/{maxLength} characters
          </span>
        </div>

        {/* Platform character limits */}
        {platforms.length > 0 && (
          <div className="flex items-center gap-2">
            {platforms.map((platform) => {
              const limit = platformLimits[platform as keyof typeof platformLimits]
              if (!limit) return null
              
              const isOverLimit = characterCount > limit
              const isNearLimit = characterCount > limit * 0.9
              
              return (
                <Badge
                  key={platform}
                  variant={isOverLimit ? 'destructive' : isNearLimit ? 'secondary' : 'outline'}
                  className="text-xs"
                >
                  {platform}: {characterCount}/{limit}
                </Badge>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

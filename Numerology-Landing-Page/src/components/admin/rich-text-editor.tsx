/**
 * TipTap rich-text editor wrapper for admin content editing.
 * Extensions: StarterKit, Image, Link, Table suite.
 * Custom image upload via /admin/upload endpoint.
 */
import * as React from 'react'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Table from '@tiptap/extension-table'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import TableRow from '@tiptap/extension-table-row'
import { EditorContent, useEditor, type Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import {
  Bold,
  Code,
  Image as ImageIcon,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Redo,
  Table as TableIcon,
  Undo,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { uploadFile } from '@/lib/admin-api'

interface RichTextEditorProps {
  value: string
  onChange: (html: string) => void
  placeholder?: string
}

export default function RichTextEditor({ value, onChange, placeholder }: RichTextEditorProps) {
  const [sourceView, setSourceView] = React.useState(false)
  const [sourceHtml, setSourceHtml] = React.useState(value)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({ allowBase64: false }),
      Link.configure({ openOnClick: false }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    content: value,
    onUpdate: ({ editor: ed }: { editor: Editor }) => {
      onChange(ed.getHTML())
    },
  })

  const handleImageUpload = React.useCallback(
    async (file: File) => {
      if (!editor) return
      try {
        const { url } = await uploadFile(file)
        editor.chain().focus().setImage({ src: url }).run()
      } catch (err) {
        alert(`Upload ảnh thất bại: ${(err as Error).message}`)
      }
    },
    [editor]
  )

  const onFileChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) handleImageUpload(file)
      e.target.value = ''
    },
    [handleImageUpload]
  )

  const toggleSource = React.useCallback(() => {
    if (!editor) return
    if (!sourceView) {
      setSourceHtml(editor.getHTML())
      setSourceView(true)
    } else {
      editor.commands.setContent(sourceHtml)
      onChange(sourceHtml)
      setSourceView(false)
    }
  }, [editor, sourceView, sourceHtml, onChange])

  const addTable = React.useCallback(() => {
    editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  }, [editor])

  if (!editor) {
    return (
      <div className="rounded-md border border-input bg-background px-3 py-2 text-sm text-muted-foreground">
        Đang tải trình soạn thảo...
      </div>
    )
  }

  return (
    <div className="rounded-md border border-input bg-background overflow-hidden">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-0.5 p-1.5 border-b border-border bg-muted/40">
        <Btn active={editor.isActive('bold')} onClick={() => editor.chain().focus().toggleBold().run()} title="Bold">
          <Bold className="w-3.5 h-3.5" />
        </Btn>
        <Btn
          active={editor.isActive('italic')}
          onClick={() => editor.chain().focus().toggleItalic().run()}
          title="Italic"
        >
          <Italic className="w-3.5 h-3.5" />
        </Btn>
        <Btn
          active={editor.isActive('bulletList')}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          title="Danh sách"
        >
          <List className="w-3.5 h-3.5" />
        </Btn>
        <Btn
          active={editor.isActive('orderedList')}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          title="Danh sách số"
        >
          <ListOrdered className="w-3.5 h-3.5" />
        </Btn>
        <Btn
          active={editor.isActive('link')}
          onClick={() => {
            const url = window.prompt('URL:')
            if (url) editor.chain().focus().setLink({ href: url }).run()
            else editor.chain().focus().unsetLink().run()
          }}
          title="Link"
        >
          <LinkIcon className="w-3.5 h-3.5" />
        </Btn>
        <Btn active={false} onClick={() => fileInputRef.current?.click()} title="Ảnh">
          <ImageIcon className="w-3.5 h-3.5" />
        </Btn>
        <Btn active={false} onClick={addTable} title="Bảng">
          <TableIcon className="w-3.5 h-3.5" />
        </Btn>
        <span className="mx-1 h-5 w-px bg-border" />
        <Btn active={false} onClick={() => editor.chain().focus().undo().run()} title="Undo">
          <Undo className="w-3.5 h-3.5" />
        </Btn>
        <Btn active={false} onClick={() => editor.chain().focus().redo().run()} title="Redo">
          <Redo className="w-3.5 h-3.5" />
        </Btn>
        <span className="mx-1 h-5 w-px bg-border" />
        <Btn active={sourceView} onClick={toggleSource} title="Mã nguồn HTML">
          <Code className="w-3.5 h-3.5" />
        </Btn>
      </div>

      <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />

      {sourceView ? (
        <textarea
          className="w-full min-h-[220px] p-3 font-mono text-xs bg-background text-foreground border-0 resize-y focus:outline-none focus:ring-0"
          value={sourceHtml}
          placeholder={placeholder}
          onChange={(e) => setSourceHtml(e.target.value)}
        />
      ) : (
        <div className="prose prose-sm max-w-none">
          <EditorContent
            editor={editor}
            className="min-h-[220px] p-3 [&_.ProseMirror]:outline-none [&_.ProseMirror]:min-h-[200px] [&_.ProseMirror_p]:my-2 [&_.ProseMirror_h1]:text-xl [&_.ProseMirror_h2]:text-lg [&_.ProseMirror_h3]:text-base [&_.ProseMirror_h1]:font-bold [&_.ProseMirror_h2]:font-bold [&_.ProseMirror_h3]:font-semibold [&_.ProseMirror_ul]:list-disc [&_.ProseMirror_ol]:list-decimal [&_.ProseMirror_ul]:pl-6 [&_.ProseMirror_ol]:pl-6 [&_.ProseMirror_a]:text-primary [&_.ProseMirror_a]:underline [&_.ProseMirror_table]:border-collapse [&_.ProseMirror_table]:my-2 [&_.ProseMirror_td]:border [&_.ProseMirror_td]:border-border [&_.ProseMirror_td]:p-1.5 [&_.ProseMirror_th]:border [&_.ProseMirror_th]:border-border [&_.ProseMirror_th]:bg-muted [&_.ProseMirror_th]:p-1.5 [&_.ProseMirror_th]:font-semibold [&_.ProseMirror_img]:rounded-md [&_.ProseMirror_img]:my-2"
          />
        </div>
      )}
    </div>
  )
}

interface BtnProps {
  active: boolean
  onClick: () => void
  title?: string
  children: React.ReactNode
}

function Btn({ active, onClick, title, children }: BtnProps) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={cn(
        'inline-flex items-center justify-center w-7 h-7 rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground',
        active && 'bg-primary/10 text-primary'
      )}
    >
      {children}
    </button>
  )
}

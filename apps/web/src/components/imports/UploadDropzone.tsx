"use client"

import { useRef, useState, useCallback } from "react"
import { Upload, X, File } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const ACCEPTED = [".pdf", ".csv"]
const MAX_BYTES = 20 * 1024 * 1024 // 20 MB

interface Props {
  file: File | null
  onChange: (file: File | null) => void
  disabled?: boolean
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function UploadDropzone({ file, onChange, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validate = useCallback((f: File): string | null => {
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."))
    if (!ACCEPTED.includes(ext)) return `File type not supported. Use ${ACCEPTED.join(" or ")}.`
    if (f.size > MAX_BYTES) return `File exceeds 20 MB limit.`
    return null
  }, [])

  const accept = useCallback(
    (f: File) => {
      const err = validate(f)
      if (err) { setError(err); return }
      setError(null)
      onChange(f)
    },
    [validate, onChange],
  )

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) setDragging(true)
  }
  const onDragLeave = () => setDragging(false)
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (disabled) return
    const f = e.dataTransfer.files[0]
    if (f) accept(f)
  }
  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) accept(f)
    e.target.value = ""
  }

  if (file) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 px-4 py-3">
        <File className="h-5 w-5 text-muted-foreground shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{file.name}</p>
          <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={() => onChange(null)}
          disabled={disabled}
          aria-label="Remove file"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          "w-full rounded-lg border-2 border-dashed border-border px-6 py-10 text-center transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          dragging && "border-primary bg-primary/5",
          disabled ? "opacity-50 cursor-not-allowed" : "hover:border-primary/60 hover:bg-accent/20 cursor-pointer",
        )}
        aria-label="Upload area. Click or drag a PDF or CSV file here."
      >
        <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
        <p className="text-sm font-medium">
          {dragging ? "Drop file here" : "Click or drag file here"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">PDF or CSV · max 20 MB</p>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        className="sr-only"
        onChange={onInputChange}
        disabled={disabled}
        aria-hidden="true"
      />
      {error && <p className="text-xs text-destructive mt-1.5">{error}</p>}
    </div>
  )
}

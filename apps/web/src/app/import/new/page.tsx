"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageHeader } from "@/components/shared/PageHeader"
import { InstrumentPicker } from "@/components/instruments/InstrumentPicker"
import { UploadDropzone } from "@/components/imports/UploadDropzone"
import { ImportBatchCard } from "@/components/imports/ImportBatchCard"
import { useUploadFile } from "@/hooks/useImports"
import { useInstruments } from "@/hooks/useInstruments"
import type { ImportBatchOut } from "@/lib/api"

export default function ImportNewPage() {
  const router = useRouter()
  const [instrumentId, setInstrumentId] = useState<string | undefined>()
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<ImportBatchOut | null>(null)

  const { data: instruments = [] } = useInstruments()
  const upload = useUploadFile()

  const canSubmit = !!instrumentId && !!file && !upload.isPending

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!instrumentId || !file) return
    try {
      const batch = await upload.mutateAsync({ instrumentId, file })
      setResult(batch)
      setFile(null)
      toast.success("File imported successfully")
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Import failed")
    }
  }

  const resultInstrument = instruments.find((i) => i.id === result?.instrument_id)

  return (
    <>
      <PageHeader title="Import Statement" />

      <div className="max-w-lg space-y-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Upload File</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Instrument picker */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Instrument *</label>
                <InstrumentPicker
                  value={instrumentId}
                  onChange={setInstrumentId}
                  placeholder="Select an instrument"
                />
              </div>

              {/* Dropzone */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">File *</label>
                <UploadDropzone
                  file={file}
                  onChange={setFile}
                  disabled={upload.isPending}
                />
              </div>

              <div className="flex gap-3 pt-1">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push("/imports")}
                  disabled={upload.isPending}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={!canSubmit}>
                  {upload.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Importing…
                    </>
                  ) : (
                    "Import File"
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Result card */}
        {result && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Import result</p>
            <ImportBatchCard batch={result} instrument={resultInstrument} />
            <Button
              variant="link"
              className="px-0 h-auto text-sm"
              onClick={() => router.push("/imports")}
            >
              View all imports →
            </Button>
          </div>
        )}
      </div>
    </>
  )
}

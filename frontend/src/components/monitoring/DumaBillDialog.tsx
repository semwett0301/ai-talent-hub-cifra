import { useState } from "react"

import { isDumaBillUrl } from "@/api/npa"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { LoaderCircle, Scale } from "lucide-react"

interface DumaBillDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  submitLabel: string
  savingLabel: string
  steps?: string[]
  onSubmit: (url: string) => Promise<void>
}

/** A bill-URL form shared by every flow that registers a законопроект with npa_service —
 * adding it to the tracked registry (`NpaPage`) or attaching one to a news alert
 * (`NewsPage`). Validation and the submit lifecycle live here; callers only supply copy
 * and what a confirmed url should do. */
export function DumaBillDialog({
  open,
  onOpenChange,
  title,
  description,
  submitLabel,
  savingLabel,
  steps,
  onSubmit,
}: DumaBillDialogProps) {
  const [url, setUrl] = useState("")
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  function changeOpen(nextOpen: boolean) {
    if (!nextOpen && saving) return
    if (!nextOpen) {
      setUrl("")
      setError("")
    }
    onOpenChange(nextOpen)
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!isDumaBillUrl(url)) {
      setError("Нужна ссылка вида https://sozd.duma.gov.ru/bill/123-8")
      return
    }
    setSaving(true)
    setError("")
    try {
      await onSubmit(url.trim())
      setUrl("")
      changeOpen(false)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={changeOpen}>
      <DialogContent>
        <form className="npa-add-form" onSubmit={handleSubmit}>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
          {steps && (
            <div className="npa-add-steps" aria-label="Что произойдёт после добавления">
              {steps.map((step, index) => (
                <span key={step}><strong>{index + 1}</strong>{step}</span>
              ))}
            </div>
          )}
          <label className="form-field">
            Ссылка на законопроект
            <Input
              autoFocus
              aria-label="Ссылка на законопроект"
              aria-invalid={Boolean(error)}
              value={url}
              onChange={(event) => { setUrl(event.target.value); setError("") }}
              placeholder="https://sozd.duma.gov.ru/bill/1286425-8"
            />
          </label>
          {error && <p role="alert" className="form-error">{error}</p>}
          {saving && <p className="small muted npa-saving-note" aria-live="polite">
            <LoaderCircle className="spin" /> {savingLabel}
          </p>}
          <DialogFooter>
            <Button type="button" variant="outline" disabled={saving} onClick={() => changeOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={!url.trim() || saving}>
              {saving ? <LoaderCircle className="spin" /> : <Scale />}
              {saving ? "Сохраняем…" : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

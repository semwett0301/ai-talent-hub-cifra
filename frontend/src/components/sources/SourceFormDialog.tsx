import { useState } from "react"
import { Globe } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { Choice } from "@/components/monitoring/Shared"
import { errorDetail } from "@/api/client"
import { useCreateSource, useUpdateSource } from "@/api/sourceMutations"
import {
  DEFAULT_RELIABILITY,
  RELIABILITY_LABELS,
  isReliability,
  type Source,
  type SourceReliability,
} from "@/api/sources"

const URL_ERROR = "Укажите полный адрес сайта, RSS или канала: https://…"
const SAVE_ERROR = "Не удалось сохранить источник."

const reliabilityOptions = Object.entries(RELIABILITY_LABELS).map(([value, label]) => ({
  value,
  label,
}))

function isWellFormed(url: string): boolean {
  try {
    const parsed = new URL(url.trim())

    return (
      ["http:", "https:"].includes(parsed.protocol) &&
      parsed.hostname.includes(".") &&
      !parsed.username &&
      !parsed.password
    )
  } catch {
    return false
  }
}

function SourceForm({ source, onDone }: { source: Source | null; onDone: () => void }) {
  const [name, setName] = useState(source?.name ?? "")
  const [link, setLink] = useState(source?.link ?? "")
  const [reliability, setReliability] = useState<SourceReliability>(
    source?.reliability ?? DEFAULT_RELIABILITY
  )
  const [error, setError] = useState("")

  const create = useCreateSource()
  const update = useUpdateSource()
  const isSaving = create.isPending || update.isPending

  // The server detects the type, so a Telegram-specific check is no longer possible here.
  function submit() {
    if (!isWellFormed(link)) {
      setError(URL_ERROR)
      return
    }

    const body = {
      name: name.trim(),
      link: link.trim(),
      reliability,
    }
    const handlers = {
      onError: (failure: unknown) => setError(errorDetail(failure, SAVE_ERROR)),
      onSuccess: onDone,
    }

    if (source) {
      update.mutate({ params: { path: { source_id: source.id } }, body }, handlers)
      return
    }

    create.mutate({ body }, handlers)
  }

  return (
    <form
      className="source-form"
      onSubmit={(event) => {
        event.preventDefault()
        submit()
      }}
    >
      <label className="form-field">
        Название
        <Input
          required
          maxLength={80}
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Например, отраслевое издание"
        />
      </label>
      <label className="form-field">
        Адрес
        <Input
          required
          value={link}
          onChange={(event) => setLink(event.target.value)}
          placeholder="https://example.com/rss"
        />
      </label>
      <div className="form-field">
        <span>Надёжность источника</span>
        <Choice
          label="Надёжность источника"
          value={reliability}
          onChange={(value) => isReliability(value) && setReliability(value)}
          options={reliabilityOptions}
        />
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <DialogFooter>
        <Button variant="outline" type="button" onClick={onDone}>
          Отмена
        </Button>
        <Button type="submit" disabled={isSaving || !name.trim() || !link.trim()}>
          <Globe />
          {isSaving ? "Сохраняем…" : source ? "Сохранить" : "Добавить"}
        </Button>
      </DialogFooter>
    </form>
  )
}

export function SourceFormDialog({
  source,
  open,
  onOpenChange,
}: {
  source: Source | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>{source ? "Изменить источник" : "Добавить источник"}</DialogTitle>
        <DialogDescription>
          {source
            ? "Тип определяется автоматически по адресу и обновится, если адрес изменить."
            : "Тип источника определит сервер — это может занять несколько секунд."}
        </DialogDescription>
        {/* Remounts per source, so the fields start from that row's values without an effect. */}
        <SourceForm
          key={source?.id ?? "new"}
          source={source}
          onDone={() => onOpenChange(false)}
        />
      </DialogContent>
    </Dialog>
  )
}

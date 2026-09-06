import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog"
import { useDeleteSource, useUpdateSource } from "@/api/sourceMutations"
import type { Source } from "@/api/sources"

export function DeleteSourceDialog({
  source,
  onClose,
}: {
  source: Source | null
  onClose: () => void
}) {
  const remove = useDeleteSource()
  const update = useUpdateSource()

  if (!source) return null

  const byId = { params: { path: { source_id: source.id } } }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogTitle>Удалить «{source.name}»?</DialogTitle>
        <DialogDescription>
          Источник исчезнет из списка навсегда. Уже собранные новости останутся. Если нужно
          только остановить сбор — отключите отслеживание, источник сохранится.
        </DialogDescription>
        <DialogFooter>
          <Button variant="outline" type="button" onClick={onClose}>
            Отмена
          </Button>
          {source.is_enabled && (
            <Button
              variant="outline"
              type="button"
              disabled={update.isPending}
              onClick={() =>
                update.mutate({ ...byId, body: { is_enabled: false } }, { onSuccess: onClose })
              }
            >
              Отключить
            </Button>
          )}
          <Button
            type="button"
            disabled={remove.isPending}
            onClick={() => remove.mutate(byId, { onSuccess: onClose })}
          >
            {remove.isPending ? "Удаляем…" : "Удалить"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

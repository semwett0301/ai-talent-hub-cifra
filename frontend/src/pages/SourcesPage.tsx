import { useState } from "react"
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DeleteSourceDialog } from "@/components/sources/DeleteSourceDialog"
import { SourceFormDialog } from "@/components/sources/SourceFormDialog"
import { SourceRow } from "@/components/sources/SourceRow"
import { errorDetail } from "@/api/client"
import { useSources } from "@/api/sourceMutations"
import type { Source } from "@/api/sources"

const LOAD_ERROR = "Не удалось загрузить источники."
const SKELETON_ROWS = [0, 1, 2]

function SourcesTable({
  sources,
  onEdit,
  onDelete,
}: {
  sources: Source[]
  onEdit: (source: Source) => void
  onDelete: (source: Source) => void
}) {
  return (
    <Table className="source-table">
      <TableHeader>
        <TableRow>
          <TableHead>Источник</TableHead>
          <TableHead>Тип</TableHead>
          <TableHead>Частота</TableHead>
          <TableHead>Отслеживание</TableHead>
          <TableHead>Действия</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sources.map((source) => (
          <SourceRow key={source.id} source={source} onEdit={onEdit} onDelete={onDelete} />
        ))}
      </TableBody>
    </Table>
  )
}

export function SourcesPage() {
  const { data: sources, isPending, error } = useSources()

  const [editing, setEditing] = useState<Source | null>(null)
  const [isFormOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState<Source | null>(null)

  function openForm(source: Source | null) {
    setEditing(source)
    setFormOpen(true)
  }

  const tracked = sources?.filter((source) => source.is_enabled).length ?? 0

  return (
    <section className="panel sources-panel sources-only">
      <div className="section-heading">
        <h2>Активные источники</h2>
        <span className="small muted">
          {sources ? `${tracked} из ${sources.length} отслеживаются` : "загрузка…"}
        </span>
      </div>
      <p className="small muted">
        Включайте отслеживание и настраивайте частоту проверки для каждого источника.
      </p>

      {isPending &&
        SKELETON_ROWS.map((row) => <Skeleton key={row} className="source-skeleton" />)}

      {error && (
        <p role="alert" className="form-error">
          {errorDetail(error, LOAD_ERROR)}
        </p>
      )}

      {sources && sources.length === 0 && (
        <p className="small muted">Источников пока нет — добавьте первый.</p>
      )}

      {sources && sources.length > 0 && (
        <SourcesTable sources={sources} onEdit={openForm} onDelete={setDeleting} />
      )}

      <Button variant="outline" className="add-source" onClick={() => openForm(null)}>
        <Plus />
        Добавить RSS, сайт или Telegram-канал
      </Button>

      <SourceFormDialog source={editing} open={isFormOpen} onOpenChange={setFormOpen} />
      <DeleteSourceDialog source={deleting} onClose={() => setDeleting(null)} />
    </section>
  )
}

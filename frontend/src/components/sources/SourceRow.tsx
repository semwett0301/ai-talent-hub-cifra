import { Landmark, Pencil, Rss, Send, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { TableCell, TableRow } from "@/components/ui/table"
import { useUpdateSource } from "@/api/sourceMutations"
import { TYPE_LABELS, frequencyLabel, type Source, type SourceType } from "@/api/sources"

const NOT_A_NEWS_RESOURCE = "Не новостной ресурс"

const ICONS = { telegram: Send, rss: Rss, web: Landmark } as const

function rowClassName(source: Source): string {
  if (!source.is_relevant) return "source-irrelevant"

  return source.is_enabled ? "" : "source-disabled"
}

export function SourceRow({
  source,
  onEdit,
  onDelete,
}: {
  source: Source
  onEdit: (source: Source) => void
  onDelete: (source: Source) => void
}) {
  const update = useUpdateSource()
  const Icon = ICONS[source.type as SourceType]

  return (
    <TableRow className={rowClassName(source)}>
      <TableCell>
        <div className="source-identity">
          <span className="source-icon">
            <Icon size={25} />
          </span>
          <div>
            <strong>{source.name}</strong>
            <p>{source.is_relevant ? source.link : NOT_A_NEWS_RESOURCE}</p>
          </div>
        </div>
      </TableCell>
      <TableCell className="source-type">{TYPE_LABELS[source.type as SourceType]}</TableCell>
      <TableCell className="source-type">{frequencyLabel(source)}</TableCell>
      <TableCell>
        <Switch
          aria-label={`Отслеживание ${source.name}`}
          checked={source.is_enabled}
          disabled={!source.is_relevant || update.isPending}
          onCheckedChange={(is_enabled) =>
            update.mutate({ params: { path: { source_id: source.id } }, body: { is_enabled } })
          }
        />
      </TableCell>
      <TableCell>
        <div className="source-actions">
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Изменить ${source.name}`}
            onClick={() => onEdit(source)}
          >
            <Pencil size={16} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Удалить ${source.name}`}
            onClick={() => onDelete(source)}
          >
            <Trash2 size={16} />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}

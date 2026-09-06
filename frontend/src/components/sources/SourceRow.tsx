import { Landmark, Pencil, Rss, Send, Trash2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { TableCell, TableRow } from "@/components/ui/table"
import { Choice } from "@/components/monitoring/Shared"
import { useUpdateSource } from "@/api/sourceMutations"
import {
  REALTIME_LABEL,
  RELIABILITY_LABELS,
  TYPE_LABELS,
  frequencyOptions,
  isScheduled,
  type Source,
  type SourceType,
} from "@/api/sources"

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
  const byId = { params: { path: { source_id: source.id } } }

  return (
    <TableRow className={rowClassName(source)}>
      <TableCell>
        <div className="source-identity">
          <span className="source-icon">
            <Icon size={25} />
          </span>
          <div>
            <div className="source-name">
              <strong>{source.name}</strong>
              {!source.is_relevant && <Badge variant="destructive">{NOT_A_NEWS_RESOURCE}</Badge>}
            </div>
            <p>{source.link}</p>
          </div>
        </div>
      </TableCell>
      <TableCell className="source-type">{TYPE_LABELS[source.type as SourceType]}</TableCell>
      <TableCell className="source-type">
        {isScheduled(source) ? (
          <div className="source-frequency">
            <Choice
              label={`Частота проверки ${source.name}`}
              value={String(source.poll_interval_seconds)}
              onChange={(seconds) =>
                update.mutate({ ...byId, body: { poll_interval_seconds: Number(seconds) } })
              }
              options={frequencyOptions(source.poll_interval_seconds)}
            />
          </div>
        ) : (
          REALTIME_LABEL
        )}
      </TableCell>
      <TableCell>
        <Switch
          aria-label={`Отслеживание ${source.name}`}
          checked={source.is_enabled}
          disabled={!source.is_relevant || update.isPending}
          onCheckedChange={(is_enabled) => update.mutate({ ...byId, body: { is_enabled } })}
        />
      </TableCell>
      <TableCell className="source-type">{RELIABILITY_LABELS[source.reliability]}</TableCell>
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

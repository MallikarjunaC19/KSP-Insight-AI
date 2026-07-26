import { useState } from 'react'
import type { ChatMessageMetadata } from '../../api/assistant'
import { resolveMediaUrl } from '../../api/assistant'

function extractGraphIntent(content: string): string | null {
  const match = content.match(/\[graph intent:\s*([^\]]+)\]/)
  return match ? match[1].trim() : null
}

export function ExplainPanel({ content, metadata }: { content: string; metadata: ChatMessageMetadata | null }) {
  const [open, setOpen] = useState(false)

  if (!metadata || !metadata.tools_used || metadata.tools_used.length === 0) {
    return (
      <div className="text-xs text-slate-400 mt-1 italic">
        General knowledge — not looked up in your records
      </div>
    )
  }

  const graphIntent = metadata.tools_used.includes('graph_lookup') ? extractGraphIntent(content) : null

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-blue-600 hover:underline flex items-center gap-1"
      >
        {open ? '▾' : '▸'} Explain this answer
      </button>
      {open && (
        <div className="mt-2 bg-slate-50 border border-slate-200 rounded p-3 text-xs space-y-3">
          <div className="text-slate-500">
            Tool{metadata.tools_used.length > 1 ? 's' : ''}: {metadata.tools_used.join(', ')}
            {metadata.elapsed_ms !== undefined && ` · ${metadata.elapsed_ms}ms`}
          </div>

          {metadata.sql_trace?.map((trace, i) => (
            <div key={i}>
              <div className="font-medium text-slate-600 mb-1">Executed SQL (RBAC-scoped):</div>
              <pre className="bg-slate-900 text-slate-100 p-2 rounded overflow-x-auto whitespace-pre-wrap">{trace.executed_sql}</pre>
              <div className="text-slate-400 mt-1">{trace.row_count} row(s) returned</div>
            </div>
          ))}

          {graphIntent && (
            <div>
              <span className="font-medium text-slate-600">Relationship template matched: </span>
              {graphIntent}
            </div>
          )}

          {metadata.ml_trace?.map((trace, i) => (
            <div key={i}>
              <div className="font-medium text-slate-600 mb-1">
                QuickML model: {trace.model} → {trace.prediction} ({trace.confidence}% confidence)
              </div>
              {trace.used_defaults.length > 0 && (
                <div className="text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1 mb-1">
                  ⚠ Defaults used for: {trace.used_defaults.join(', ')} — not officer-stated values
                </div>
              )}
              <div className="text-slate-500">Top contributing factors:</div>
              <ul className="list-disc list-inside">
                {trace.top_factors.map((f, j) => (
                  <li key={j}>
                    {f.feature} = {String(f.value)} (impact {f.impact > 0 ? '+' : ''}{f.impact.toFixed(3)})
                    {f.encoded && <span className="text-slate-400"> — encoded category</span>}
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {metadata.audio_url && (
            <div>
              <span className="font-medium text-slate-600">Kannada audio: </span>
              <a href={resolveMediaUrl(metadata.audio_url)} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                Play audio
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
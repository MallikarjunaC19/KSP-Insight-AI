import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  fetchConversations, createConversation, sendMessage, sendAudioMessage, exportConversationPdf,
} from '../../api/assistant'
import { Button } from '@/components/ui/button'
import { ExplainPanel } from './ExplainPanel'
import { useVoiceRecorder } from './useVoiceRecorder'
import { useAuth } from '../../hooks/useAuth'
import { fetchPersons } from '../../api/persons'
import { PersonNetworkGraph } from '../persons/PersonNetworkGraph'
import { resolveMediaUrl } from '../../api/assistant'

export function AIAssistantPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data: conversations } = useQuery({ queryKey: ['conversations'], queryFn: fetchConversations })
  const selected = conversations?.find((c) => c.id === selectedId) ?? null

  const currentOfficer = useAuth((s) => s.officer)
  const isOwnConversation = !selected || selected.officer === currentOfficer?.id

  const { isRecording, startRecording, stopRecording } = useVoiceRecorder()

  const createMutation = useMutation({
    mutationFn: (title: string) => createConversation(title),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      setSelectedId(conv.id)
    },
  })

  const sendMutation = useMutation({
    mutationFn: (message: string) => sendMessage(selectedId!, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      setDraft('')
    },
  })

  const sendAudioMutation = useMutation({
    mutationFn: ({ convId, blob }: { convId: string; blob: Blob }) => sendAudioMessage(convId, blob),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const exportMutation = useMutation({
    mutationFn: () => exportConversationPdf(selected!.id),
    onSuccess: (data) => window.open(data.download_url, '_blank'),
  })

  const { data: persons } = useQuery({ queryKey: ['persons'], queryFn: fetchPersons })
  const [expandedGraphMsgId, setExpandedGraphMsgId] = useState<string | null>(null)

  function findPersonForMessage(userQuestionText: string) {
  if (!persons) return null
  return persons.find((p) =>
    userQuestionText.toLowerCase().includes(`${p.first_name} ${p.last_name}`.toLowerCase())
  ) ?? null
}

  const isBusy = sendMutation.isPending || createMutation.isPending || sendAudioMutation.isPending

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [selected?.messages.length])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }, [draft])

  function handleSend() {
  if (!draft.trim() || isBusy || !isOwnConversation) return
  if (!selectedId) {
    createMutation.mutate(draft.trim().slice(0, 60))
    return
  }
  sendMutation.mutate(draft.trim())
}

  async function handleMicClick() {
    if (isRecording) {
      const blob = await stopRecording()
      let convId = selectedId
      if (!convId) {
        const conv = await createConversation('Voice conversation')
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
        setSelectedId(conv.id)
        convId = conv.id
      }
      sendAudioMutation.mutate({ convId, blob })
    } else {
      startRecording()
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] -m-6 bg-white">
      {/* Sidebar */}
      <div className="w-64 flex flex-col border-r border-slate-200 bg-slate-50">
        <div className="p-3">
          <button
            onClick={() => setSelectedId(null)}
            className="w-full flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <span className="text-lg leading-none">+</span> New chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
          {conversations
            ?.slice()
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
            .map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedId(c.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                  selectedId === c.id ? 'bg-slate-200 text-slate-900' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {c.title}
              </button>
            ))}
        </div>
      </div>

      {/* Main chat column */}
      <div className="flex-1 flex flex-col">
        {selected && (
            <div className="flex justify-between items-center px-6 py-3 border-b border-slate-100">
              <div className="min-w-0">
                <span className="text-sm font-medium text-slate-500 truncate block">{selected.title}</span>
                {!isOwnConversation && (
                  <span className="text-xs text-amber-600">Viewing another officer's conversation — read only</span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled={exportMutation.isPending || selected.messages.length === 0}
                onClick={() => exportMutation.mutate()}
              >
                {exportMutation.isPending ? 'Exporting...' : 'Export PDF'}
              </Button>
            </div>
          )}

        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-6">
            {!selected || selected.messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full pt-24 text-center">
                <div className="text-2xl font-semibold text-slate-700 mb-2">KAVACH AI Assistant</div>
                <p className="text-slate-400 max-w-sm">
                  Ask about crimes, cases, relationships, or predictions — in English or Kannada,
                  by typing or speaking. Every answer shows exactly how it was derived.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {selected.messages.map((msg, idx) =>
                  msg.sender === 'USER' ? (
                    <div key={msg.id} className="flex justify-end">
                      <div className="bg-slate-100 rounded-2xl px-4 py-2.5 max-w-lg text-[15px] text-slate-800">
                        {msg.content}
                      </div>
                    </div>
                  ) : (
                    <div key={msg.id} className="flex gap-3">
                      <div className="w-7 h-7 rounded-full bg-slate-900 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-white text-xs font-bold">K</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="prose prose-sm max-w-none prose-p:my-2 prose-table:text-sm">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        </div>
                        {msg.metadata?.audio_url && (
                          <audio controls src={resolveMediaUrl(msg.metadata.audio_url)} className="mt-2 h-8" />
                        )}
                        <ExplainPanel content={msg.content} metadata={msg.metadata} />
                        {msg.metadata?.tools_used?.includes('graph_lookup') && (() => {
                          const prevUserMsg = selected.messages[idx - 1]
                          const matchedPerson = prevUserMsg ? findPersonForMessage(prevUserMsg.content) : null
                          if (!matchedPerson) return null
                          const isExpanded = expandedGraphMsgId === msg.id
                          return (
                            <div className="mt-2">
                              <button
                                onClick={() => setExpandedGraphMsgId(isExpanded ? null : msg.id)}
                                className="text-xs text-blue-600 hover:underline"
                              >
                                {isExpanded ? '▾ Hide network' : '▸ View network'}
                              </button>
                              {isExpanded && (
                                <div className="mt-2">
                                  <PersonNetworkGraph
                                    personId={matchedPerson.id}
                                    personName={`${matchedPerson.first_name} ${matchedPerson.last_name}`}
                                  />
                                </div>
                              )}
                            </div>
                          )
                        })()}
                      </div>
                    </div>
                  )
                )}
                {isBusy && (
                  <div className="flex gap-3">
                    <div className="w-7 h-7 rounded-full bg-slate-900 flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-xs font-bold">K</span>
                    </div>
                    <div className="flex items-center gap-1 pt-1.5">
                      <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:-0.3s]" />
                      <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:-0.15s]" />
                      <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" />
                    </div>
                  </div>
                )}
                {(sendMutation.isError || sendAudioMutation.isError) && (
                  <p className="text-sm text-red-600">
                    Failed to send: {((sendMutation.error ?? sendAudioMutation.error) as Error).message}
                  </p>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-slate-100 px-6 py-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white px-4 py-2 shadow-sm focus-within:border-slate-400">
              <textarea
              ref={textareaRef}
              rows={1}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={isBusy || !isOwnConversation}
              placeholder={isOwnConversation ? "Ask about crimes, cases, predictions... (type in English or Kannada)" : "Read-only — this is another officer's conversation"}
              className="flex-1 resize-none border-none outline-none text-[15px] py-1.5 max-h-40 bg-transparent placeholder:text-slate-400"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
            />
            <button
              type="button"
              onClick={handleMicClick}
              disabled={(isBusy && !isRecording) || !isOwnConversation}
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-colors ${
                isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
              title={isRecording ? 'Stop recording' : 'Record voice message (English or Kannada)'}
            >
              🎤
            </button>
            <Button
              size="sm"
              className="rounded-full w-8 h-8 p-0 flex-shrink-0"
              disabled={!draft.trim() || isBusy || !isOwnConversation}
              onClick={handleSend}
            >
              ↑
            </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

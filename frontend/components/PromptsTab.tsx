import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { ChevronRight } from "lucide-react"

export type PresetPeriod = '24h' | '7d' | '30d' | '90d' | 'custom'

export interface PromptItem { id: number; query?: string; rank?: number; executions?: number; visibility_score_individual?: number; share_of_voice_individual?: number }
export interface PromptsByTopic { topic: string; topic_total_mentions: number; prompts: PromptItem[] }

export interface PromptsTabProps {
  activePeriod: PresetPeriod
  onPresetChange: (value: PresetPeriod) => void
  selectedTopic: string
  onTopicChange: (value: string) => void
  topicOptions: string[]
  selectedModel: string
  onModelChange: (value: string) => void
  modelOptions: string[]
  isLoading: boolean
  promptsGrouped: PromptsByTopic[]
  openTopics: Record<string, boolean>
  setOpenTopics: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  openPrompt: (id: number) => void
  openEditPrompt: (id: number, query: string, topic: string, brand?: string) => void
  handleDeletePrompt: (id: number) => void
  translateTopicToSpanish: (s: string) => string
  emojiForTopic: (s: string) => string
}

export default function PromptsTab(props: PromptsTabProps) {
  const { activePeriod, onPresetChange, selectedTopic, onTopicChange, topicOptions, selectedModel, onModelChange, modelOptions, isLoading, promptsGrouped, openTopics, setOpenTopics, openPrompt, openEditPrompt, handleDeletePrompt, translateTopicToSpanish, emojiForTopic } = props
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-gray-900">Prompts</h2>
          <Select onValueChange={(value: PresetPeriod) => onPresetChange(value)} value={activePeriod}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Período" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Últimas 24 horas</SelectItem>
              <SelectItem value="7d">Últimos 7 días</SelectItem>
              <SelectItem value="30d">Últimos 30 días</SelectItem>
              <SelectItem value="90d">Últimos 90 días</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedTopic} onValueChange={(v) => onTopicChange(v)}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Todos los topics" />
            </SelectTrigger>
            <SelectContent>
              {topicOptions.map((t) => (
                <SelectItem key={t} value={t}>{t === 'all' ? 'Todos los topics' : translateTopicToSpanish(t)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedModel} onValueChange={onModelChange}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Todos los modelos" />
            </SelectTrigger>
            <SelectContent>
              {modelOptions.map((m) => (
                <SelectItem key={m} value={m}>{m === 'all' ? 'Todos los modelos' : m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card className="shadow-sm bg-white border-gray-200">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full bg-white">
              <thead className="border-b border-gray-200 bg-white">
                <tr>
                  <th className="text-left p-4 font-medium text-gray-600">Tema</th>
                  <th className="text-left p-4 font-medium text-gray-600">Puntuación de visibilidad</th>
                  <th className="text-left p-4 font-medium text-gray-600">Rank</th>
                  <th className="text-left p-4 font-medium text-gray-600">Share of Voice</th>
                  <th className="text-left p-4 font-medium text-gray-600">Executions</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={`skel-${i}`}>
                      <td className="p-4"><Skeleton className="h-8 w-48" /></td>
                      <td className="p-4"><Skeleton className="h-4 w-24" /></td>
                      <td className="p-4"><Skeleton className="h-4 w-12" /></td>
                      <td className="p-4"><Skeleton className="h-4 w-20" /></td>
                      <td className="p-4"><Skeleton className="h-4 w-12" /></td>
                    </tr>
                  ))
                ) : (
                  (() => {
                    const filtered = promptsGrouped
                    return filtered.map((group, index) => {
                      const avgVisibility = group.prompts.length > 0
                        ? group.prompts.reduce((sum, p) => sum + (p.visibility_score_individual ?? 0), 0) / group.prompts.length
                        : 0
                      const avgSov = group.prompts.length > 0
                        ? group.prompts.reduce((sum, p) => sum + (p.share_of_voice_individual ?? 0), 0) / group.prompts.length
                        : 0
                      const rank = index + 1
                      const isOpen = !!openTopics[group.topic]
                      return (
                        <React.Fragment key={group.topic}>
                          <tr
                            className="border-b border-gray-100 hover:bg-gray-50 bg-white cursor-pointer"
                            onClick={() => { setOpenTopics(prev => ({ ...prev, [group.topic]: !prev[group.topic] })) }}
                          >
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                                <div className="w-8 h-8 bg-blue-50 border border-blue-200 rounded-full flex items-center justify-center">
                                  <span className="text-base">{emojiForTopic(group.topic)}</span>
                                </div>
                                <div>
                                  <div className="font-medium text-gray-900">{translateTopicToSpanish(group.topic)}</div>
                                  <div className="text-sm text-gray-500">
                                    <Badge variant="secondary" className="text-xs">Topic</Badge>
                                    <span className="ml-2">{group.prompts.length} prompts</span>
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <span className="font-medium">{avgVisibility.toFixed(1)}%</span>
                                <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden"><div className="h-1.5 bg-gray-800" style={{ width: `${Math.min(100, Math.max(0, avgVisibility))}%` }}></div></div>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">#{rank}</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{avgSov.toFixed(1)}%</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <span className="font-medium">{group.topic_total_mentions}</span>
                            </td>
                          </tr>
                          {isOpen && (
                            <tr className="bg-white">
                              <td colSpan={5} className="p-0">
                                <div className="px-4 py-2">
                                  <div className="divide-y">
                                    {group.prompts.map((p) => (
                                      <div
                                        key={p.id}
                                        className="flex items-center justify-between py-2 rounded px-2 hover:bg-gray-50"
                                        role="button"
                                        tabIndex={0}
                                        onClick={() => openPrompt(p.id)}
                                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { openPrompt(p.id); } }}
                                      >
                                        <div className="text-sm text-gray-900 line-clamp-2 max-w-[50%]">
                                          {p.query}
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                          <div className="w-48 text-right">Visibilidad (prompt): <span className="font-medium text-gray-900">{(p.visibility_score_individual ?? 0).toFixed(1)}%</span></div>
                                          <div className="w-40 text-right">SOV (prompt): <span className="font-medium text-gray-900">{(p.share_of_voice_individual ?? 0).toFixed(1)}%</span></div>
                                          <div className="w-28 text-right">Ranking: <span className="font-medium text-gray-900">#{p.rank}</span></div>
                                          <div className="w-32 text-right">Ejecuciones: <span className="font-medium text-gray-900">{p.executions}</span></div>
                                          <div className="flex items-center gap-2">
                                            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); openEditPrompt(p.id, p.query as string, group.topic, undefined); }}>Editar</Button>
                                            <Button size="sm" variant="destructive" onClick={(e) => { e.stopPropagation(); handleDeletePrompt(p.id); }}>Eliminar</Button>
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      )
                    })
                  })()
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

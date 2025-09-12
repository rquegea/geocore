import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, ChevronDown } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, AreaChart, Area, Brush, ReferenceDot } from "recharts"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import React, { useEffect, useState } from "react"

export interface SentimentComputed {
  positivePercent: number
  neutralPercent: number
  negativePercent: number
  delta: number
  timeseries: ReadonlyArray<{ date: string; value: number }>
  negatives: ReadonlyArray<any>
  positives?: ReadonlyArray<any>
}

export interface TopicGroup { group_name: string; total_occurrences: number; topics: { topic: string; count: number; avg_sentiment?: number }[] }

export interface SentimentTabProps {
  sentimentChartType: "line" | "area"
  sentimentBrush: boolean
  posHighlightIdx: number
  negHighlightIdx: number
  topicsCloud: { topic: string; count: number; avg_sentiment?: number }[]
  topicGroups: TopicGroup[]
  openGroups: Record<string, boolean>
  setOpenGroups: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  translateTopicToSpanish: (s: string) => string
  // Nuevos props para alinear eje X con visibilidad
  isHourlyRange: boolean
  xDomain: [number, number]
  xTicks: number[]
  executionTimestamps?: number[]
  dateRange?: { from?: Date; to?: Date }
  model?: string
  topic?: string
  brandName: string
  // Prefetched data (opcional)
  initialSentimentApi?: SentimentApiResponse | null
  initialTopicsCloud?: { topic: string; count: number; avg_sentiment?: number }[]
  initialTopicGroups?: TopicGroup[]
}

import type { DateRange } from "react-day-picker"
import { getSentiment, getTopicsCloud, type TopicsCloudResponse, type SentimentApiResponse } from "@/services/api"

export default function SentimentTab(props: SentimentTabProps) {
  const { sentimentChartType, sentimentBrush, posHighlightIdx, negHighlightIdx, openGroups, setOpenGroups, translateTopicToSpanish, isHourlyRange, xDomain, xTicks, executionTimestamps, dateRange, model, topic, brandName, initialSentimentApi, initialTopicsCloud, initialTopicGroups } = props

  const [topicsCloud, setTopicsCloud] = useState<{ topic: string; count: number; avg_sentiment?: number }[]>(initialTopicsCloud || [])
  const [topicGroups, setTopicGroups] = useState<TopicGroup[]>(initialTopicGroups || [])
  const [sentimentApi, setSentimentApi] = useState<SentimentApiResponse | null>(initialSentimentApi || null)
  const [sentimentComputed, setSentimentComputed] = useState<SentimentComputed>(() => {
    if (initialSentimentApi) {
      const { distribution, timeseries, negatives, positives } = initialSentimentApi
      const total = (distribution.negative + distribution.neutral + distribution.positive) || 1
      const positivePercent = (distribution.positive / total) * 100
      const neutralPercent = (distribution.neutral / total) * 100
      const negativePercent = (distribution.negative / total) * 100
      const scaledTimeseries = (timeseries || []).map(p => ({ date: p.date, value: Math.max(0, Math.min(100, Number(p.value) || 0)) }))
      return { positivePercent, neutralPercent, negativePercent, delta: 0, timeseries: scaledTimeseries, negatives: negatives || [], positives: positives || [] }
    }
    return { positivePercent: 0, neutralPercent: 0, negativePercent: 0, delta: 0, timeseries: [], negatives: [], positives: [] }
  })

  // Fallback local: agrupar topics en categorías cuando la API no devuelve groups
  const buildFallbackGroups = (topics: { topic: string; count: number; avg_sentiment?: number }[]): TopicGroup[] => {
    const groupsMap: Record<string, { total_occurrences: number; sum_weighted_sent: number; topics: { topic: string; count: number; avg_sentiment?: number }[] }> = {}
    const ensure = (name: string) => (groupsMap[name] ||= { total_occurrences: 0, sum_weighted_sent: 0, topics: [] })
    const toKey = (s: string) => (s || '').toLowerCase().trim()
    const isBrand = (t: string) => /\bthe\s*core\b/.test(t)
    const isUniversity = (t: string) => /universidad|universitat|complutense|rey\s*juan\s*carlos|navarra|uva|upm|urjc|usc|uam|unav/.test(t)
    const isAdmissions = (t: string) => /beca|precio|coste|costo|admis|financiaci[oó]n|matr[ií]cula/.test(t)
    const isJobs = (t: string) => /empleo|empleabilidad|trabajo|salidas/.test(t)
    const isPrograms = (t: string) => /cine|audiovisual|animaci[oó]n|vfx|fotograf[ií]a|guion|gu[ií]on|ingenier[ií]a|software|programaci[oó]n|dise[nñ]o|3d|edici[oó]n|formaci[oó]n/.test(t)
    const OTHER = 'Temas Generales del Sector'
    topics.forEach((row) => {
      const topic = toKey(row.topic)
      const count = Number(row.count || 0)
      const sent = Number(row.avg_sentiment || 0)
      const push = (groupName: string) => { const g = ensure(groupName); g.total_occurrences += count; g.sum_weighted_sent += sent * count; g.topics.push({ topic: row.topic, count, avg_sentiment: sent }) }
      if (isBrand(topic)) push('Menciones de Marca Propia')
      else if (isUniversity(topic)) push('Menciones de Universidades Tradicionales')
      else if (isAdmissions(topic)) push('Becas y Admisiones')
      else if (isJobs(topic)) push('Salidas Profesionales')
      else if (isPrograms(topic)) push('Programas y Grados')
      else push(OTHER)
    })
    return Object.entries(groupsMap).map(([group_name, v]) => ({ group_name, total_occurrences: v.total_occurrences, avg_sentiment: v.total_occurrences ? v.sum_weighted_sent / v.total_occurrences : 0, topics: v.topics.sort((a, b) => (b.count || 0) - (a.count || 0)).slice(0, 100) }))
  }

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      if (!dateRange?.from || !dateRange?.to) return
      const filters = { model: model || 'all', topic: topic || 'all', brand: brandName, granularity: isHourlyRange ? 'hour' as const : 'day' as const }
      const [sentimentRes, topicsRes] = await Promise.all([
        getSentiment(dateRange as DateRange, filters),
        getTopicsCloud(dateRange as DateRange, filters),
      ])
      if (cancelled) return
      setSentimentApi(sentimentRes)
      setTopicsCloud(topicsRes.topics || [])
      const apiGroups = (topicsRes as any).groups || []
      if (apiGroups && apiGroups.length > 0) setTopicGroups(apiGroups)
      else setTopicGroups(buildFallbackGroups((topicsRes.topics || []) as any))

      // compute derived
      const { distribution, timeseries, negatives, positives } = sentimentRes
      const total = (distribution.negative + distribution.neutral + distribution.positive) || 1
      const positivePercent = (distribution.positive / total) * 100
      const neutralPercent = (distribution.neutral / total) * 100
      const negativePercent = (distribution.negative / total) * 100
      const scaledTimeseries = (timeseries || []).map(p => ({ date: p.date, value: Math.max(0, Math.min(100, Number(p.value) || 0)) }))
      setSentimentComputed({ positivePercent, neutralPercent, negativePercent, delta: 0, timeseries: scaledTimeseries, negatives: negatives || [], positives: positives || [] })
    }
    load()
    return () => { cancelled = true }
  }, [dateRange, model, topic, brandName, isHourlyRange])
  const formatMadrid = (tsMs: number) => {
    try {
      return isHourlyRange
        ? new Date(tsMs).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit', hour12: false })
        : new Date(tsMs).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short' })
    } catch {
      return String(new Date(tsMs))
    }
  }
  const labelFormatter = (label: number | string) => {
    const ts = typeof label === 'number' ? label : new Date(label).getTime()
    return isHourlyRange
      ? new Date(ts).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit', hour12: false })
      : new Date(ts).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short' })
  }

  const CustomTooltip = ({ active, label, payload }: any) => {
    if (!active) return null
    const v = payload && payload.length ? payload[0]?.value : undefined
    const num = typeof v === 'number' && isFinite(v) ? v : Number(v)
    const safe = isFinite(num) ? num : 0
    return (
      <div className="rounded-md border bg-card px-3 py-2 text-sm shadow">
        <div className="font-medium">{labelFormatter(label)}</div>
        <div className="text-muted-foreground">Positivo: {safe.toFixed(1)}%</div>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="shadow-sm bg-white">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-semibold">Análisis de sentimiento</CardTitle>
                <p className="text-sm text-muted-foreground"> Sentimiento positivo a lo largo del tiempo </p>
              </div>
            </CardHeader>
            <CardContent>
              <div className="mb-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold">{sentimentComputed.positivePercent.toFixed(1)}%</span>
                  <span className="text-sm text-muted-foreground">(de menciones positivas)</span>
                  <span className={sentimentComputed.delta >= 0 ? "text-green-500 flex items-center gap-1" : "text-red-500 flex items-center gap-1"}>
                    {sentimentComputed.delta >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {sentimentComputed.delta.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="h-64 flex items-center justify-center">
                <ResponsiveContainer width="95%" height="100%">
                  {sentimentChartType === "line" ? (
                    <LineChart data={[...(sentimentComputed.timeseries || [])]}>
                      <XAxis
                        dataKey={(d: any) => new Date(d.date).getTime()}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                        type="number"
                        scale="time"
                        domain={xDomain}
                        ticks={xTicks}
                        minTickGap={40}
                        tickFormatter={(unixTime: number) => labelFormatter(unixTime)}
                      />
                      <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} domain={[0, 100]} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#111111"
                        strokeWidth={2}
                        connectNulls
                        dot={{ fill: "#111111", strokeWidth: 2, r: 4 }}
                      />
                      {(executionTimestamps || []).map((ts, i) => (
                        <ReferenceDot key={`exec-dot-${i}`} x={ts} y={0} r={3} stroke="#6b7280" fill="#6b7280" />
                      ))}
                      {sentimentBrush && <Brush dataKey={(d: any) => new Date(d.date).getTime()} height={20} />}
                    </LineChart>
                  ) : (
                    <AreaChart data={[...(sentimentComputed.timeseries || [])]}>
                      <XAxis
                        dataKey={(d: any) => new Date(d.date).getTime()}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                        type="number"
                        scale="time"
                        domain={xDomain}
                        ticks={xTicks}
                        minTickGap={40}
                        tickFormatter={(unixTime: number) => labelFormatter(unixTime)}
                      />
                      <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} domain={[0, 100]} />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#111111"
                        fill="#111111"
                        fillOpacity={0.15}
                        connectNulls
                      />
                      {(executionTimestamps || []).map((ts, i) => (
                        <ReferenceDot key={`exec-dot-area-${i}`} x={ts} y={0} r={3} stroke="#6b7280" fill="#6b7280" />
                      ))}
                      {sentimentBrush && <Brush dataKey={(d: any) => new Date(d.date).getTime()} height={20} />}
                    </AreaChart>
                  )}
                </ResponsiveContainer>
              </div>

              <div className="mt-6">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span>Negativo</span>
                  <span>Neutral</span>
                  <span>Positivo</span>
                </div>
                <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden flex">
                  <div className="h-3 bg-red-500" style={{ width: `${Math.min(100, Math.max(0, sentimentComputed.negativePercent))}%` }}></div>
                  <div className="h-3 bg-gray-400" style={{ width: `${Math.min(100, Math.max(0, sentimentComputed.neutralPercent || 0))}%` }}></div>
                  <div className="h-3 bg-green-500" style={{ width: `${Math.min(100, Math.max(0, sentimentComputed.positivePercent))}%` }}></div>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
                  <span>{sentimentComputed.negativePercent.toFixed(1)}%</span>
                  <span>{(sentimentComputed.neutralPercent || 0).toFixed(1)}%</span>
                  <span>{sentimentComputed.positivePercent.toFixed(1)}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        <div>
          <Card className="shadow-sm bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold">Destacados</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sentimentComputed.positives && sentimentComputed.positives.length > 0 ? (
                  (() => { const p = sentimentComputed.positives![posHighlightIdx % sentimentComputed.positives!.length]; return (
                    <div key={`pos-${p.id}-${posHighlightIdx}`} className="p-3 border rounded bg-green-50 border-green-200">
                      <div className="text-xs text-green-700 mb-1">Positivo · {p.sentiment?.toFixed(2)}</div>
                      <div className="text-sm text-gray-900 line-clamp-3">{p.summary || ''}</div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {(p.key_topics || []).slice(0, 5).map((t: string, i: number) => (
                          <Badge key={`${p.id}-t-${i}`} variant="secondary" className="text-xs">{t}</Badge>
                        ))}
                      </div>
                      {p.source_url && (
                        <div className="mt-2 text-xs"><a href={p.source_url} target="_blank" rel="noreferrer" className="text-blue-600 underline">{p.source_title || p.source_url}</a></div>
                      )}
                    </div>
                  ) })()
                ) : (
                  <div className="p-3 border rounded bg-gray-50 border-gray-200 text-sm text-gray-600">No hay ninguna positiva</div>
                )}

                {sentimentComputed.negatives && sentimentComputed.negatives.length > 0 ? (
                  (() => { const m = sentimentComputed.negatives[negHighlightIdx % sentimentComputed.negatives.length]; return (
                    <div key={`neg-${m.id}-${negHighlightIdx}`} className="p-3 border rounded bg-red-50 border-red-200">
                      <div className="text-xs text-red-700 mb-1">Negativo · {m.sentiment?.toFixed(2)}</div>
                      <div className="text-sm text-gray-900 line-clamp-3">{m.summary || ''}</div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {(m.key_topics || []).slice(0, 5).map((t: string, i: number) => (
                          <Badge key={`${m.id}-t-${i}`} variant="secondary" className="text-xs">{t}</Badge>
                        ))}
                      </div>
                      {m.source_url && (
                        <div className="mt-2 text-xs"><a href={m.source_url} target="_blank" rel="noreferrer" className="text-blue-600 underline">{m.source_title || m.source_url}</a></div>
                      )}
                    </div>
                  ) })()
                ) : (
                  <div className="p-3 border rounded bg-gray-50 border-gray-200 text-sm text-gray-600">No hay ninguna negativa</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Temas por Categoría</h3>
        </div>
        <Card className="shadow-sm bg-white border-gray-200">
          <CardContent className="p-0">
            {topicGroups.length > 0 ? (
              (topicGroups.filter((g) => g.group_name !== 'Temas Generales del Sector')).map((group) => {
                const totalCount = (group?.topics || []).reduce((sum: number, t: any) => sum + (t.count || 0), 0)
                const weightedAvg = totalCount > 0 ? (group.topics.reduce((s: number, t: any) => s + ((t.avg_sentiment ?? 0) * (t.count || 0)), 0) / totalCount) : 0
                const groupAvgPercent = ((weightedAvg + 1) / 2) * 100
                const isOpen = !!openGroups[group.group_name]
                return (
                  <Collapsible key={group.group_name} open={isOpen} onOpenChange={(v) => setOpenGroups((prev) => ({ ...prev, [group.group_name]: v }))}>
                    <div className="border-b last:border-b-0">
                      <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-gray-50">
                        <div className="flex items-center gap-3">
                          <div className="font-medium text-gray-900">{group.group_name}</div>
                          <Badge variant="secondary">{group.total_occurrences} menciones</Badge>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-sm">Sentimiento Medio: <span className={`font-semibold ${weightedAvg > 0.1 ? 'text-green-600' : weightedAvg < -0.1 ? 'text-red-600' : 'text-gray-600'}`}>{groupAvgPercent.toFixed(0)}%</span></div>
                          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                        </div>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="bg-gray-50/50 p-4">
                          <table className="w-full table-fixed">
                            <colgroup>
                              <col className="w-[60%]" />
                              <col className="w-[240px]" />
                              <col className="w-[140px]" />
                            </colgroup>
                            <tbody>
                              {group.topics.map((t: any) => {
                                const sentimentScore = ((t.avg_sentiment ?? 0) + 1) / 2 * 100;
                                return (
                                  <tr key={t.topic} className="hover:bg-gray-100">
                                    <td className="p-2 font-medium text-gray-800">{translateTopicToSpanish(t.topic)}</td>
                                    <td className="p-2 w-[240px]">
                                      <div className="flex items-center justify-center gap-2">
                                        <div className="w-32 h-2 bg-gray-200 rounded-full">
                                          <div className={`h-2 rounded-full ${sentimentScore > 60 ? 'bg-green-500' : sentimentScore < 40 ? 'bg-red-500' : 'bg-yellow-500'}`} style={{ width: `${sentimentScore}%` }} />
                                        </div>
                                        <span className="text-sm font-medium">{sentimentScore.toFixed(0)}%</span>
                                      </div>
                                    </td>
                                    <td className="p-2 text-right">{t.count} ocurrencias</td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </CollapsibleContent>
                    </div>
                  </Collapsible>
                )
              })
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full bg-white table-fixed">
                  <colgroup>
                    <col className="w-[60%]" />
                    <col className="w-[240px]" />
                    <col className="w-[140px]" />
                  </colgroup>
                  <thead className="border-b border-gray-200 bg-white">
                    <tr>
                      <th className="text-left p-4 font-medium text-gray-600">Tema</th>
                      <th className="text-left p-4 font-medium text-gray-600">Nivel de Sentimiento</th>
                      <th className="text-left p-4 font-medium text-gray-600">Ocurrencias</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white">
                    {(() => {
                      // Fallback cuando no hay groups: usar topicsCloud como pseudo-grupos por topic
                      const top = topicsCloud.slice(0, 50)
                      const maxCount = Math.max(...top.map(t => t.count || 0), 1)
                      return top.map((t) => {
                        const sentimentScore = ((t.avg_sentiment ?? 0) + 1) / 2 * 100
                        return (
                          <tr key={t.topic} className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-blue-50 border border-blue-200 rounded-full flex items-center justify-center">
                                  <span className="text-base">🧩</span>
                                </div>
                                <div className="font-medium text-gray-900">{translateTopicToSpanish(t.topic)}</div>
                              </div>
                            </td>
                            <td className="p-4 w-[240px]">
                              <div className="flex items-center gap-2 justify-center">
                                <div className="w-32 h-2 bg-gray-200 rounded-full">
                                  <div className={`h-2 rounded-full ${sentimentScore > 60 ? 'bg-green-500' : sentimentScore < 40 ? 'bg-red-500' : 'bg-yellow-500'}`} style={{ width: `${sentimentScore}%` }} />
                                </div>
                                <span className="text-sm font-medium">{sentimentScore.toFixed(0)}%</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <span className="font-medium">{t.count}</span>
                                <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden"><div className="h-1.5 bg-gray-800" style={{ width: `${Math.max(0, Math.min(100, (t.count / maxCount) * 100)) }%` }}></div></div>
                              </div>
                            </td>
                          </tr>
                        )
                      })
                    })()}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}

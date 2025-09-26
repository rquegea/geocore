import React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, ReferenceDot } from "recharts"
import { format } from "date-fns"
import { es } from "date-fns/locale"
import { type PromptDetails } from "@/services/api"
import { smoothZerosWithPrevAvg } from "@/lib/utils"

export interface PromptDetailModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  promptDetails: PromptDetails | null
  promptLoading: boolean
  isHourlyRange: boolean
  xDomain: [number, number]
  xTicks: number[]
  execDialogOpen: boolean
  setExecDialogOpen: (open: boolean) => void
  execActiveIndex: number
  setExecActiveIndex: (idx: number) => void
}

const COLORS = ["#111827", "#2563eb", "#16a34a", "#f59e0b", "#ef4444", "#7c3aed", "#0ea5e9", "#84cc16", "#a855f7", "#f97316"]

export default function PromptDetailModal(props: PromptDetailModalProps) {
  const { open, onOpenChange, promptDetails, promptLoading, isHourlyRange, xDomain, xTicks, setExecDialogOpen, execActiveIndex, setExecActiveIndex } = props
  const labelFormatter = (label: number | string) => {
    const ts = typeof label === 'number' ? label : new Date(label).getTime()
    try { return format(new Date(ts), isHourlyRange ? 'HH:mm' : 'MMM d', { locale: es }) } catch { return String(label) }
  }

  const pieData = React.useMemo(() => {
    if (!promptDetails) return [] as { name: string; value: number }[]
    if (promptDetails.brand_distribution && Object.keys(promptDetails.brand_distribution).length > 0) {
      const total = Object.values(promptDetails.brand_distribution).reduce((s, v) => s + (typeof v === 'number' ? v : Number(v) || 0), 0) || 1
      const arr = Object.entries(promptDetails.brand_distribution).map(([name, count]) => ({ name, value: (Number(count) / total) * 100 }))
      return arr.sort((a, b) => b.value - a.value)
    }
    if (Array.isArray(promptDetails.platforms)) return [...promptDetails.platforms].sort((a, b) => b.value - a.value)
    return []
  }, [promptDetails])

  const MAX_LEGEND_ITEMS = 7
  const visibleLegend = pieData.slice(0, MAX_LEGEND_ITEMS)
  const hasMore = pieData.length > MAX_LEGEND_ITEMS
  const [legendOpen, setLegendOpen] = React.useState(false)
  const execDots = React.useMemo(() => {
    if (!promptDetails?.executions) return [] as { ts: number }[]
    try {
      return promptDetails.executions.map(e => ({ ts: new Date(e.created_at).getTime() }))
    } catch { return [] }
  }, [promptDetails])

  // Normalizar series para evitar NaN en tooltips y gráficos
  const visSeries = React.useMemo(() => {
    const src = promptDetails?.timeseries || []
    const mapped = src.map((d) => {
      const ts = (d as any).ts ?? new Date((d as any).date).getTime()
      const raw = (d as any).value
      const value = typeof raw === 'number' && isFinite(raw) ? raw : 0
      return { ts, value }
    })
    return smoothZerosWithPrevAvg(mapped)
  }, [promptDetails])
  const sovSeries = React.useMemo(() => {
    const src = promptDetails?.sov_timeseries || []
    return src.map((d) => {
      const ts = (d as any).ts ?? new Date((d as any).date).getTime()
      const raw = (d as any).value
      const value = typeof raw === 'number' && isFinite(raw) ? raw : 0
      return { ts, value }
    })
  }, [promptDetails])

  const tooltipValue = (v: unknown) => {
    const num = typeof v === 'number' && isFinite(v) ? v : Number(v)
    const safe = isFinite(num) ? num : 0
    return `${safe.toFixed(1)}%`
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg">{promptDetails?.query || "Prompt"}</DialogTitle>
          <p className="text-sm text-muted-foreground pt-1">
            Mostrando métricas para el prompt seleccionado en el rango de fechas y modelo actual.
          </p>
        </DialogHeader>
        {promptLoading ? (
          <div className="p-6 text-center">Cargando detalles del prompt...</div>
        ) : promptDetails ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
            <div className="flex flex-col gap-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <Card>
                  <CardHeader><CardTitle className="text-sm font-medium">Visibilidad</CardTitle></CardHeader>
                  <CardContent><p className="text-3xl font-bold">{promptDetails.visibility_score?.toFixed(1) ?? '0.0'}%</p></CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle className="text-sm font-medium">Share of Voice</CardTitle></CardHeader>
                  <CardContent><p className="text-3xl font-bold">{promptDetails.share_of_voice?.toFixed(1) ?? '0.0'}%</p></CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle className="text-sm font-medium">Ejecuciones</CardTitle></CardHeader>
                  <CardContent><p className="text-3xl font-bold">{promptDetails.total_executions ?? '0'}</p></CardContent>
                </Card>
              </div>

              {promptDetails.trends && promptDetails.trends.length > 0 && (
                <Card>
                  <CardHeader><CardTitle className="text-sm font-medium">Tendencias Clave</CardTitle></CardHeader>
                  <CardContent className="flex flex-wrap gap-2">
                    {promptDetails.trends.map((trend, index) => (
                      <Badge key={index} variant="secondary" className="text-sm">{trend}</Badge>
                    ))}
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader><CardTitle className="text-sm">Ejecuciones Recientes</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[260px] overflow-auto border rounded-lg p-3">
                    {promptDetails.executions?.map((e, idx) => (
                      <div key={e.id} className="text-xs border-b pb-2 last:border-b-0">
                        <div className="flex justify-between text-muted-foreground mb-1">
                          <span>{e.engine}</span>
                          <span>{new Date(e.created_at).toLocaleDateString()}</span>
                        </div>
                        <p className="text-sm text-foreground line-clamp-3 cursor-pointer" onClick={() => { setExecActiveIndex(idx); setExecDialogOpen(true); }}>{e.response}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="flex flex-col gap-6">
              <Card>
                <CardHeader><CardTitle className="text-sm">Puntuación de Visibilidad (Evolución)</CardTitle></CardHeader>
                <CardContent className="h-[250px] w-full">
                  <ResponsiveContainer>
                    <LineChart data={visSeries}>
                      <XAxis dataKey={(d: any) => d.ts} type="number" scale="time" domain={xDomain} ticks={xTicks} stroke="#888888" fontSize={12} tickFormatter={(t: number) => labelFormatter(t)} />
                      <YAxis stroke="#888888" fontSize={12} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                      <Tooltip formatter={(value) => [tooltipValue(value), "Visibilidad"]} labelFormatter={(t) => labelFormatter(t as number)} />
                      <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={2} dot={{ r: 3, fill: "#000" }} />
                      {execDots.map((d, i) => (
                        <ReferenceDot key={`vdot-${i}`} x={d.ts} y={0} r={3} stroke="#111827" fill="#111827" />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-sm">Share of Voice (Evolución)</CardTitle></CardHeader>
                <CardContent className="h-[250px] w-full">
                  <ResponsiveContainer>
                    <LineChart data={sovSeries}>
                      <XAxis dataKey={(d: any) => d.ts} type="number" scale="time" domain={xDomain} ticks={xTicks} stroke="#888888" fontSize={12} tickFormatter={(t: number) => labelFormatter(t)} />
                      <YAxis stroke="#888888" fontSize={12} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                      <Tooltip formatter={(value) => [tooltipValue(value), "Share of Voice"]} labelFormatter={(t) => labelFormatter(t as number)} />
                      <Line type="monotone" dataKey="value" stroke="#888" strokeWidth={2} dot={{ r: 3, fill: "#888" }} />
                      {execDots.map((d, i) => (
                        <ReferenceDot key={`sdot-${i}`} x={d.ts} y={0} r={3} stroke="#6b7280" fill="#6b7280" />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              {pieData.length > 0 && (
                <Card>
                  <CardHeader><CardTitle className="text-sm">Share of Voice por marca</CardTitle></CardHeader>
                  <CardContent className="h-[260px] w-full">
                    <div className="h-full w-full flex items-center gap-4">
                      <div className="h-full flex-1">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={50} paddingAngle={2}>
                              {pieData.map((entry, index) => (
                                <Cell key={`pie-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(value: number, name: string) => [`${Number(value).toFixed(1)}%`, name]} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="h-full w-56 overflow-auto p-1 text-xs">
                        {visibleLegend.map((d, i) => (
                          <div key={`legend-${i}`} className="flex items-center gap-1 py-0.5 leading-4">
                            <span className="inline-block w-2 h-2 rounded" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                            <span className="truncate max-w-[160px]">{d.name}</span>
                            <span className="ml-auto tabular-nums text-muted-foreground">{d.value.toFixed(1)}%</span>
                          </div>
                        ))}
                        {hasMore && (
                          <div className="pt-1 flex justify-end">
                            <Button size="sm" variant="link" className="px-0" onClick={() => setLegendOpen(true)}>Ver más</Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        ) : null}
        <Dialog open={legendOpen} onOpenChange={setLegendOpen}>
          <DialogContent className="sm:max-w-[560px]">
            <DialogHeader>
              <DialogTitle className="text-base">Todas las marcas (Share of Voice)</DialogTitle>
            </DialogHeader>
            <div className="max-h-[60vh] overflow-auto space-y-2 text-sm">
              {pieData.map((d, i) => (
                <div key={`all-${i}`} className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="flex-1 truncate">{d.name}</span>
                  <span className="text-muted-foreground">{d.value.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  )
}

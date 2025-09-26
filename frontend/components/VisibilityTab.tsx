import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, AreaChart, Area } from "recharts"
import React, { useEffect, useState } from "react"

export interface VisibilityPoint { date: string | number; value: number }
export interface VisibilityApiResponse { visibility_score: number; delta: number; series: VisibilityPoint[] }

export interface VisibilityTabProps {
  brandName: string
  isHourlyRange: boolean
  xDomain: [number, number]
  xTicks: number[]
  visibilityChartType: "line" | "area"
  visibilityChartKey: string
  dateRange?: { from?: Date; to?: Date }
  model?: string
  topic?: string
  clientId?: number
  brandId?: number
}

function computeDeltaFromSeries(series: VisibilityPoint[]): number {
  const points = (series || []).filter(p => typeof p?.value === 'number' && !Number.isNaN(p.value))
  if (points.length < 2) return 0
  const first = points[0].value
  const last = points[points.length - 1].value
  const diff = last - first
  return Math.round(diff * 10) / 10
}

import type { DateRange } from "react-day-picker"
import { getVisibility, type VisibilityApiResponse as ApiVisibility } from "@/services/api"
import { smoothZerosWithPrevAvg } from "@/lib/utils"

export default function VisibilityTab(props: VisibilityTabProps) {
  const { brandName, isHourlyRange, xDomain, xTicks, visibilityChartType, visibilityChartKey, dateRange, model, topic, clientId, brandId } = props

  const [visibility, setVisibility] = useState<ApiVisibility | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      if (!dateRange?.from || !dateRange?.to) return
      try {
        setLoading(true)
        const filters = { model: model || 'all', topic: topic || 'all', brand: brandName, granularity: isHourlyRange ? 'hour' as const : 'day' as const, clientId, brandId }
        const res = await getVisibility(dateRange as DateRange, filters)
        if (!cancelled) setVisibility(res)
      } catch {
        if (!cancelled) setVisibility(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [dateRange, model, topic, brandName, isHourlyRange, clientId, brandId])

  // Preparar serie suavizada para evitar caídas a 0 puntuales
  const baseSeries = (visibility?.series || []) as any
  const smoothedSeries = smoothZerosWithPrevAvg(baseSeries)
  const deltaFromRange = computeDeltaFromSeries(smoothedSeries as any)

  if (!visibility || loading) {
    return (
      <Card className="shadow-sm bg-white h-full min-h-[420px]">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Puntuación de visibilidad</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">{loading ? 'Cargando...' : 'Sin datos para el rango seleccionado.'}</div>
        </CardContent>
      </Card>
    )
  }
  const formatMadridTime = (tsMs: number, hourly: boolean) => {
    try {
      if (hourly) {
        return new Date(tsMs).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit', hour12: false })
      }
      const d = new Date(tsMs).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short' })
      return d
    } catch {
      return String(new Date(tsMs))
    }
  }
  const labelFormatter = (label: number | string) => {
    const ts = typeof label === 'number' ? label : new Date(label).getTime()
    return formatMadridTime(ts, isHourlyRange)
  }
  const valueFormatter = (v: number) => [`${Number(v).toFixed(1)}%`, 'Visibilidad'] as const
  const deltaPositive = deltaFromRange >= 0
  return (
    <Card className="shadow-sm bg-white h-full min-h-[420px]">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg font-semibold">Puntuación de visibilidad</CardTitle>
          <p className="text-sm text-muted-foreground"> Frecuencia con la que {brandName} aparece en respuestas generadas por IA </p>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col h-full">
        <div className="mb-4">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">{visibility.visibility_score.toFixed(1)}%</span>
            <span className={`${deltaPositive ? "text-green-500" : "text-red-500"} flex items-center gap-1`}>
              {deltaPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {deltaFromRange >= 0 ? `+${deltaFromRange.toFixed(1)}%` : `${deltaFromRange.toFixed(1)}%`}
            </span>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            {visibilityChartType === "line" ? (
              <LineChart data={smoothedSeries as any} key={visibilityChartKey}>
                <XAxis
                  dataKey={(d: any) => (typeof d.ts === 'number' ? d.ts : new Date(d.date).getTime())}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                  type="number"
                  scale="time"
                  domain={xDomain}
                  ticks={xTicks}
                  minTickGap={40}
                  tickFormatter={(unixTime: number) => formatMadridTime(unixTime, isHourlyRange)}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 100]}
                  ticks={[0,10,20,30,40,50,60,70,80,90,100]}
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                  formatter={(v: number) => valueFormatter(v)}
                  labelFormatter={labelFormatter}
                />
                <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={2} dot={{ fill: "#000", strokeWidth: 2, r: 4 }} />
              </LineChart>
            ) : (
              <AreaChart data={smoothedSeries as any} key={visibilityChartKey}>
                <XAxis
                  dataKey={(d: any) => (typeof d.ts === 'number' ? d.ts : new Date(d.date).getTime())}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                  type="number"
                  scale="time"
                  domain={xDomain}
                  ticks={xTicks}
                  minTickGap={40}
                  tickFormatter={(unixTime: number) => formatMadridTime(unixTime, isHourlyRange)}
                />
                <YAxis axisLine={false} tickLine={false} domain={[0, 100]} ticks={[0,10,20,30,40,50,60,70,80,90,100]} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                  formatter={(v: number) => valueFormatter(v)}
                  labelFormatter={labelFormatter}
                />
                <Area type="monotone" dataKey="value" stroke="#000" fill="#000" fillOpacity={0.1} />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

"use client"

// 1. IMPORTACIONES (sin cambios)
import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardFooter, CardAction } from "@/components/ui/card"
import React from "react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  BarChart3,
  Search,
  TrendingUp,
  TrendingDown,
  Settings,
  ChevronDown,
  ChevronRight,
  Zap,
  MoreHorizontal,
  Target,
  Calendar as CalendarIcon,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, PieChart, Pie, Cell, BarChart, Bar, AreaChart, Area, Brush } from "recharts"
import Image from "next/image"
import { getVisibility, getShareOfVoice, getVisibilityRanking, getMentions, getModels, getPrompts, getTopics, getPromptDetails, getSentiment, getTopicsCloud, createPrompt, updatePrompt, deletePrompt, getInsights, categorizePromptApi, type PromptsByTopic, type PromptDetails, type InsightRow, type ShareOfVoiceResponse } from "@/services/api"
import { VisibilityData, Competitor, Mention } from "@/types"
import { cn } from "@/lib/utils"
import { DateRange } from "react-day-picker"
import { format, subDays } from "date-fns"
import { es } from "date-fns/locale"
import { DateRangePicker } from "@/components/ui/date-range-picker"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import PulsingCircle from "@/components/ui/pulsing-circle"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu"

// INTERFAZ PARA LOS DATOS DE VISIBILIDAD COMPLETOS
interface VisibilityApiResponse {
  visibility_score: number;
  delta: number;
  series: VisibilityData[];
}

// TIPO PARA LOS PERIODOS PREDEFINIDOS
type PresetPeriod = '7d' | '30d' | '90d' | 'custom';
// Tipos ya exportados desde services/api

// Colores para el pie chart basados en las clases que vienen del backend
const COLOR_MAP: Record<string, string> = {
  "bg-blue-500": "#3b82f6",
  "bg-red-500": "#ef4444",
  "bg-blue-600": "#2563eb",
  "bg-yellow-500": "#eab308",
  "bg-gray-800": "#1f2937",
};

// Traducción simple de topics a español (editable/expandible)
const TOPIC_TRANSLATIONS: Record<string, string> = {
    "Credit cards": "Tarjetas de crédito",
    "Auto loans": "Préstamos de auto",
    "Banking": "Banca",
    "Mortgage": "Hipotecas",
    "Wealth management / advisor": "Gestión de patrimonio / asesor",
    "Brokerage and investment platforms": "Bróker y plataformas de inversión",
    "Personal loans": "Préstamos personales",
    "Personal lending": "Préstamo personal",
    "Peer to peer payments (P2P Payments)": "Pagos P2P",
    "Estate planning": "Planificación patrimonial",
    "Home and renters insurance": "Seguro de hogar y alquiler",
    "Auto Insurance": "Seguro de auto",
    "Target Audience Research": "Investigación del público objetivo",
    // Nuevas categorías agrupadas
    "Audience & Research": "Audiencia e Investigación",
    "Motivation & Triggers": "Motivaciones y Disparadores",
    "Parents & Family Concerns": "Padres y Preocupaciones",
    "Competition & Benchmarking": "Competencia y Benchmarking",
    "Brand & Reputation": "Marca y Reputación",
    "Digital Trends & Marketing": "Tendencias Digitales y Marketing",
    "Industry & Market": "Industria y Mercado",
    "Students & Experience": "Estudiantes y Experiencia",
    "Innovation & Technology": "Innovación y Tecnología",
    "Employment & Jobs": "Empleo y Profesiones",
    "Share of Voice & Monitoring": "Share of Voice y Monitorización",
    "Future Outlook & Trends": "Perspectivas y Tendencias",
    // Variantes sin ampersand o con nombres canónicos
    "Admissions & Enrollment": "Admisiones e Inscripción",
    "Admissions Enrollment": "Admisiones e Inscripción",
    "Scholarships & Cost": "Becas y Coste",
    "Curriculum & Programs": "Plan de estudios y Programas",
    "Curriculum Programs": "Plan de estudios y Programas",
    "Campus & Facilities": "Campus e Instalaciones",
    "Campus Facilities": "Campus e Instalaciones",
    "Events & Community": "Eventos y Comunidad",
    "Alumni & Success Stories": "Alumni y Casos de éxito",
    "Alumni Success Stories": "Alumni y Casos de éxito",
    // Otras categorías vistas en menús
    "Brand Monitoring": "Monitorización de Marca",
    "Brand Partnerships": "Alianzas de Marca",
    "Career Preferences": "Preferencias de Carrera",
    "Competition Benchmarking": "Benchmarking de Competencia",
    "Competitive Analysis": "Análisis Competitivo",
    "Competitor Benchmark": "Benchmark de Competidores",
    "Digital Marketing": "Marketing Digital",
    "Digital Trends": "Tendencias Digitales",
    "Digital Trends Marketing": "Tendencias Digitales y Marketing",
    "Employment Jobs": "Empleo y Profesiones",
    "Employment Outcomes": "Resultados de Empleabilidad",
    "Future Outlook": "Perspectivas de Futuro",
    "Future Outlook Trends": "Perspectivas y Tendencias de Futuro",
    "Industry Buzz": "Buzz del sector",
    "Industry Perception": "Percepción del Sector",
    "Innovation Perception": "Percepción de la Innovación",
    "Innovation Technology": "Innovación y Tecnología",
    "Job Market": "Mercado laboral",
    "Motivation Triggers": "Motivaciones y Disparadores",
    "Uncategorized": "Sin categoría",
};

function translateTopicToSpanish(topic: string): string {
  return TOPIC_TRANSLATIONS[topic] || topic;
}

function canonicalizeTopicFromLabel(label: string): string {
  if (!label || label === 'all') return label
  for (const [en, es] of Object.entries(TOPIC_TRANSLATIONS)) {
    if (es === label) return en
  }
  return label
}

// Emoji relacionado con el topic
function emojiForTopic(topic: string): string {
  const t = topic.toLowerCase();
  // Catálogo académico/marketing
  if (t.includes("competition") || t.includes("competencia") || t.includes("benchmark")) return "🏁"; // Competition & Benchmarking
  if (t.includes("admissions") || t.includes("admisiones") || t.includes("inscripci")) return "📝"; // Admissions & Enrollment
  if (
    t.includes("curriculum") || t.includes("programs") || t.includes("programas") ||
    t.includes("grado") || t.includes("grados") || t.includes("máster") || t.includes("master") ||
    t.includes("dónde estudiar") || t.includes("donde estudiar") || t.includes("centros de formaci")
  ) return "📚"; // Curriculum & Programs
  if (t.includes("scholarships") || t.includes("becas") || t.includes("cost") || t.includes("coste") || t.includes("precio")) return "💰"; // Scholarships & Cost
  if (t.includes("engineering") || t.includes("software") || t.includes("ingenier") || t.includes("programaci")) return "💻"; // Engineering & Software
  if (t.includes("audiovisual") || t.includes("cine") || t.includes("vfx") || t.includes("animaci") || t.includes("sonido")) return "🎬"; // Audiovisual & Media
  if (t.includes("brand") || t.includes("reputation") || t.includes("reputaci") || t.includes("marca")) return "🏷️"; // Brand & Reputation
  if (t.includes("students") || t.includes("estudiantes") || t.includes("experiencia")) return "🎓"; // Students & Experience
  if (t.includes("parents") || t.includes("padres") || t.includes("famil")) return "👨‍👩‍👧"; // Parents & Family Concerns
  if (t.includes("digital") || t.includes("marketing") || t.includes("trends") || t.includes("tendencias")) return "🌐"; // Digital Trends & Marketing
  if (t.includes("industry") || t.includes("mercado")) return "🏭"; // Industry & Market
  if (t.includes("innovation") || t.includes("innovaci") || t.includes("technology") || t.includes("tecnolog")) return "🤖"; // Innovation & Technology
  if (t.includes("employment") || t.includes("empleo") || t.includes("jobs") || t.includes("trabaj")) return "💼"; // Employment & Jobs
  if (t.includes("campus") || t.includes("instalaciones") || t.includes("facilities")) return "🏫"; // Campus & Facilities
  if (t.includes("events") || t.includes("eventos") || t.includes("community") || t.includes("comunidad")) return "📅"; // Events & Community
  if (t.includes("share of voice") || t.includes("monitor")) return "📣"; // Share of Voice & Monitoring
  if (t.includes("future") || t.includes("futuro") || t.includes("outlook")) return "🔮"; // Future Outlook & Trends
  if (t.includes("partnerships") || t.includes("colaboraciones") || t.includes("alianzas")) return "🤝"; // Partnerships & Collaborations
  if (t.includes("alumni") || t.includes("éxito") || t.includes("exito") || t.includes("testimonios")) return "🏆"; // Alumni & Success Stories
  return "🧭";
}

// Utilidad simple para exportar datos a CSV en cliente
function downloadCSV(filename: string, rows: Array<Record<string, unknown>>) {
  try {
    if (!rows || rows.length === 0) return
    const headers = Object.keys(rows[0] || {})
    const escapeCell = (value: unknown) => {
      const s = value === null || value === undefined ? "" : String(value)
      // Encerrar en comillas y escapar comillas internas
      return '"' + s.replaceAll('"', '""') + '"'
    }
    const lines = [
      headers.join(","),
      ...rows.map((r) => headers.map((h) => escapeCell((r as Record<string, unknown>)[h])).join(",")),
    ]
    const csv = lines.join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error("No se pudo exportar el CSV", e)
  }
}

export function AnalyticsDashboard() {
  // 2. ESTADOS
  const [visibility, setVisibility] = useState<VisibilityApiResponse | null>(null)
  const [competitorData, setCompetitorData] = useState<Competitor[]>([])
  const [visibilityRanking, setVisibilityRanking] = useState<Competitor[]>([])
  const [sovByTopic, setSovByTopic] = useState<Record<string, Competitor[]>>({})
  const [selectedSovTopic, setSelectedSovTopic] = useState<string>("All")
  const [mentions, setMentions] = useState<Mention[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // El rango de fechas sigue siendo la única fuente de verdad para la API
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: subDays(new Date(), 29), // Por defecto, 30 días
    to: new Date(),
  });
  // Nuevo estado para saber qué opción está activa en la UI
  const [activePeriod, setActivePeriod] = useState<PresetPeriod>('30d');
  const [isDatePopoverOpen, setIsDatePopoverOpen] = useState(false) // legacy flag (no longer used)

  const [activeTab, setActiveTab] = useState("Visibility")
  const [activeSidebarSection, setActiveSidebarSection] = useState("Answer Engine Insights")
  const [activeStrategiesTab, setActiveStrategiesTab] = useState("Estrategias")
  // Insights (estrategias / improve)
  const [insightsRows, setInsightsRows] = useState<InsightRow[]>([])
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [strategySearch, setStrategySearch] = useState("")
  const [selectedBucket, setSelectedBucket] = useState<"all" | "opportunities" | "risks" | "trends">("all")
  const [plannedItems, setPlannedItems] = useState<string[]>([])
  const [newPlanItem, setNewPlanItem] = useState<string>("")
  const [strategySort, setStrategySort] = useState<"impact" | "date" | "alpha">("impact")

  // Filtro: solo modelo (chat)
  const [modelOptions, setModelOptions] = useState<string[]>([])
  const [selectedModel, setSelectedModel] = useState<string>("all")
  // Filtro: source (oculto, siempre 'all')
  const selectedSource = "all"
  // Marca principal para filtrar sentimiento/SOV (mostrar The Core según entorno)
  const primaryBrandName = process.env.NEXT_PUBLIC_BRAND || 'The Core School'
  // Visibilidad ya usa 'Índice de Visibilidad' en backend
  const sovTopics = useMemo(() => Object.keys(sovByTopic || {}), [sovByTopic])

  // Prompts data
  const [promptsGrouped, setPromptsGrouped] = useState<PromptsByTopic[]>([])
  const [selectedTopic, setSelectedTopic] = useState<string>("all")
  const [topicOptions, setTopicOptions] = useState<string[]>(["all"]) 
  const [openTopics, setOpenTopics] = useState<Record<string, boolean>>({})
  const [promptModalOpen, setPromptModalOpen] = useState(false)
  const [promptDetails, setPromptDetails] = useState<PromptDetails | null>(null)
  const [promptLoading, setPromptLoading] = useState(false)
  // Estado del modal de ejecuciones (detalle de respuesta)
  const [execDialogOpen, setExecDialogOpen] = useState(false)
  const [execActiveIndex, setExecActiveIndex] = useState(0)
  const [execFilterEngine, setExecFilterEngine] = useState<string>('all')
  // Crear Prompt
  const [addPromptOpen, setAddPromptOpen] = useState(false)
  const [newPromptQuery, setNewPromptQuery] = useState("")
  const [newPromptTopic, setNewPromptTopic] = useState("")
  const [newPromptBrand, setNewPromptBrand] = useState("")
  const [autoDetectedTopic, setAutoDetectedTopic] = useState<string>("")
  const [autoDetectConfidence, setAutoDetectConfidence] = useState<number>(0)
  const [autoDetectSuggestion, setAutoDetectSuggestion] = useState<string>("")
  const [autoDetectSuggestionIsNew, setAutoDetectSuggestionIsNew] = useState<boolean>(false)
  const [addPromptStep, setAddPromptStep] = React.useState<'input' | 'thinking' | 'suggestion' | 'error'>('input')
  // Editar/Eliminar Prompt
  const [editPromptOpen, setEditPromptOpen] = useState(false)
  const [editPromptId, setEditPromptId] = useState<number | null>(null)
  const [editPromptQuery, setEditPromptQuery] = useState("")
  const [editPromptTopic, setEditPromptTopic] = useState("")
  const [editPromptBrand, setEditPromptBrand] = useState("")

  // Sentiment API-backed state
  const [sentimentApi, setSentimentApi] = useState<{ timeseries: { date: string; avg: number }[]; distribution: { negative: number; neutral: number; positive: number }; negatives: { id: number; summary: string | null; key_topics: string[]; source_title: string | null; source_url: string | null; sentiment: number; created_at: string | null }[]; positives?: { id: number; summary: string | null; key_topics: string[]; source_title: string | null; source_url: string | null; sentiment: number; created_at: string | null }[] } | null>(null)
  const [topicsCloud, setTopicsCloud] = useState<{ topic: string; count: number; avg_sentiment?: number }[]>([])
  const [topicGroups, setTopicGroups] = useState<any[]>([])
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({})
  // Resumen por tema aplicando filtros globales a cada tema individualmente
  // eliminado: topicSummaries (ahora usamos datos de API directamente)

  // Configuración de gráficos (3 opciones): tipo, zoom (brush) y exportar
  const [visibilityChartType, setVisibilityChartType] = useState<"line" | "area">("line")
  const [visibilityBrush, setVisibilityBrush] = useState(false)
  const [sovDonut, setSovDonut] = useState(true)
  const [sovShowLabels, setSovShowLabels] = useState(false)
  const [sentimentChartType, setSentimentChartType] = useState<"line" | "area">("line")
  const [sentimentBrush, setSentimentBrush] = useState(false)

  // Índices para rotación de highlights
  const [negHighlightIdx, setNegHighlightIdx] = useState(0)
  const [posHighlightIdx, setPosHighlightIdx] = useState(0)
  // Barra global de filtros reutilizable
  const GlobalFiltersToolbar = () => (
    <div className="flex items-center gap-2">
      {/* Presets de periodo */}
      <Select onValueChange={(value: PresetPeriod) => handlePresetChange(value)} value={activePeriod}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Seleccionar período" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="7d">Últimos 7 días</SelectItem>
          <SelectItem value="30d">Últimos 30 días</SelectItem>
          <SelectItem value="90d">Últimos 90 días</SelectItem>
          {activePeriod === 'custom' && <SelectItem value="custom" disabled>Rango Personalizado</SelectItem>}
        </SelectContent>
      </Select>

      {/* Calendario */}
      <DateRangePicker value={dateRange} onChange={handleCustomDateChange} />

      {/* Tema (traducción visible) */}
      <Select value={selectedTopic} onValueChange={(v) => setSelectedTopic(v)}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Tema" />
        </SelectTrigger>
        <SelectContent>
          {topicOptions.map((t) => (
            <SelectItem key={t} value={t}>{t === 'all' ? 'Todos los temas' : translateTopicToSpanish(t)}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Modelo a la derecha del selector de temas */}
      <Select value={selectedModel} onValueChange={setSelectedModel}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Modelo" />
        </SelectTrigger>
        <SelectContent>
          {modelOptions.map((m) => (
            <SelectItem key={m} value={m}>{m === 'all' ? 'Todos los modelos' : m}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )


  const openPrompt = async (promptId: number) => {
    try {
      setPromptLoading(true)
      const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic }
      const details = await getPromptDetails(promptId, dateRange!, filters)
      setPromptDetails(details)
      setPromptModalOpen(true)
    } catch (e) {
      console.error("No se pudo cargar el detalle del prompt", e)
    } finally {
      setPromptLoading(false)
    }
  }

  // Datos derivados (hooks SIEMPRE antes de cualquier return condicional)
  const pieData = useMemo(() => (
    competitorData.map(c => ({
      name: c.name,
      value: parseFloat(String(c.score).replace('%','')) || 0,
      color: COLOR_MAP[c.color] || "#8884d8",
    }))
  ), [competitorData])

  // Rankings eliminados por solicitud (solo tabla de topics + prompts)

  // Sentiment derived data from API (usar % de menciones positivas)
  const sentimentComputed = useMemo(() => {
    if (!sentimentApi) {
      return {
        positivePercent: 0,
        neutralPercent: 0,
        negativePercent: 0,
        delta: 0,
        timeseries: [],
        negatives: [],
        positives: [],
      } as const
    }

    const { distribution, timeseries, negatives, positives } = sentimentApi
    const total = (distribution.negative + distribution.neutral + distribution.positive) || 1

    // Métrica principal: % de menciones positivas
    const positivePercent = (distribution.positive / total) * 100
    const neutralPercent = (distribution.neutral / total) * 100
    const negativePercent = (distribution.negative / total) * 100

    // Mantener delta simple por ahora
    const delta = 0

    // Escalar serie a 0-100 según promedio de score (opcional)
    const scaledTimeseries = (timeseries || []).map(p => ({
      date: p.date,
      value: Math.max(0, Math.min(100, ((p.avg + 1) / 2) * 100))
    }))

    return {
      positivePercent,
      neutralPercent,
      negativePercent,
      delta,
      timeseries: scaledTimeseries,
      negatives: negatives || [],
      positives: positives || [],
    } as const
  }, [sentimentApi])

  // Resetear índices cuando cambien las listas
  useEffect(() => { setNegHighlightIdx(0) }, [sentimentComputed.negatives?.length])
  useEffect(() => { setPosHighlightIdx(0) }, [sentimentComputed.positives?.length])

  // Rotación automática cada 8s
  useEffect(() => {
    const negLen = sentimentComputed.negatives?.length || 0
    const posLen = sentimentComputed.positives?.length || 0
    const id = setInterval(() => {
      if (negLen > 1) setNegHighlightIdx(i => (i + 1) % negLen)
      if (posLen > 1) setPosHighlightIdx(i => (i + 1) % posLen)
    }, 8000)
    return () => clearInterval(id)
  }, [sentimentComputed.negatives, sentimentComputed.positives])

  // Mantener sincronizado el selector de SOV con el filtro global de tema
  useEffect(() => {
    if (selectedTopic === 'all') {
      setSelectedSovTopic('All')
    } else if (sovTopics.includes(selectedTopic)) {
      setSelectedSovTopic(selectedTopic)
    } else {
      setSelectedSovTopic('All')
    }
  }, [selectedTopic, sovTopics])

  // Estado de granularidad para Visibilidad
  const [visibilityGranularity, setVisibilityGranularity] = useState<'day' | 'hour'>('day')

  // 3. USEEFFECT (sin cambios en su lógica, siempre depende de dateRange)
  useEffect(() => {
    if (!dateRange?.from || !dateRange?.to) {
        return;
    }
    const loadDashboardData = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic, brand: primaryBrandName, granularity: visibilityGranularity }
        const [visibilityResponse, visibilityRankingRes, sovResponse, mentionsResponse, promptsRes, sentimentRes, topicsCloudRes] = await Promise.all([
          getVisibility(dateRange, filters),
          getVisibilityRanking(dateRange, filters),
          getShareOfVoice(dateRange, filters),
          getMentions(dateRange, filters),
          getPrompts(dateRange, filters),
          getSentiment(dateRange, filters),
          getTopicsCloud(dateRange, filters),
        ]);
        setVisibility(visibilityResponse);
        setVisibilityRanking(visibilityRankingRes.ranking || [])
        setCompetitorData((sovResponse as ShareOfVoiceResponse).overall_ranking);
        setSovByTopic((sovResponse as ShareOfVoiceResponse).by_topic || {});
        setMentions(mentionsResponse.mentions);
        setPromptsGrouped(promptsRes.topics);
        setSentimentApi(sentimentRes);
        setTopicsCloud(topicsCloudRes.topics);
        setTopicGroups((topicsCloudRes as any).groups || []);
      } catch (err) {
        setError("No se pudieron cargar los datos. Por favor, revisa la consola o el estado del backend.")
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadDashboardData()
  }, [dateRange, selectedModel, selectedTopic, primaryBrandName, visibilityGranularity]);

  // cargar opciones de filtros (models y topics independientes del filtro activo)
  useEffect(() => {
    const loadFiltersLists = async () => {
      try {
        const [modelsRes, topicsRes] = await Promise.all([
          getModels(),
          getTopics(),
        ])
        setModelOptions(["all", ...modelsRes.models])
        // Los topics deben ser globales para poder cambiar entre ellos sin que la lista se bloquee
        setTopicOptions(["all", ...(topicsRes.topics || [])])
      } catch (e) {
        console.error("No se pudieron cargar los listados de filtros", e)
      }
    }
    loadFiltersLists()
  }, [])

  // eliminado: carga de resumen por tema (usamos métricas de API como avg_sentiment)

  // Cargar insights reales cuando estemos en "Estrategias y objetivos"
  useEffect(() => {
    if (activeSidebarSection !== "Estrategias y objetivos") return
    if (!dateRange?.from || !dateRange?.to) return
    const load = async () => {
      try {
        setInsightsLoading(true)
        const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic }
        const res = await getInsights(dateRange, filters, 100, 0)
        setInsightsRows(res.insights || [])
      } catch (e) {
        console.error("No se pudieron cargar los insights", e)
        setInsightsRows([])
      } finally {
        setInsightsLoading(false)
      }
    }
    load()
  }, [activeSidebarSection, dateRange, selectedModel, selectedTopic])

  type StrategyItem = { id: string; text: string; impact: "Alto" | "Medio" | "Bajo"; createdAt: string | null; themes?: string[] }
  const aggregatedInsights = useMemo(() => {
    const data: { opportunities: StrategyItem[]; risks: StrategyItem[]; trends: StrategyItem[]; quotes: string[]; ctas: string[] } = { opportunities: [], risks: [], trends: [], quotes: [], ctas: [] }
    // Impacto mejorado: combina magnitud de sentimiento y frecuencia de temas del insight
    const impactFrom = (row: any): "Alto" | "Medio" | "Bajo" => {
      const s = typeof row?.avg_sentiment === 'number' ? Math.min(1, Math.abs(row.avg_sentiment)) : 0.2
      const tf = row?.topic_frequency && typeof row.topic_frequency === 'object' ? Math.min(1, (Math.max(0, ...Object.values(row.topic_frequency as any)) as number) / 5) : 0
      const score = 0.5 * s + 0.5 * tf
      if (score >= 0.6) return "Alto"
      if (score >= 0.35) return "Medio"
      return "Bajo"
    }
    insightsRows.forEach((row) => {
      const p = row.payload || ({} as any)
      const imp = impactFrom(p)
      const themes = Array.isArray(p.top_themes) ? (p.top_themes as string[]) : []
      if (Array.isArray(p.opportunities)) p.opportunities.forEach((t: string, idx: number) => data.opportunities.push({ id: `opp-${row.id}-${idx}-${t}`, text: t, impact: imp, createdAt: row.created_at, themes }))
      if (Array.isArray(p.risks)) p.risks.forEach((t: string, idx: number) => data.risks.push({ id: `risk-${row.id}-${idx}-${t}`, text: t, impact: imp, createdAt: row.created_at, themes }))
      if (Array.isArray(p.trends)) p.trends.forEach((t: string, idx: number) => data.trends.push({ id: `trend-${row.id}-${idx}-${t}`, text: t, impact: imp, createdAt: row.created_at, themes }))
      if (Array.isArray(p.quotes)) data.quotes.push(...p.quotes)
      if (Array.isArray(p.calls_to_action)) data.ctas.push(...p.calls_to_action)
    })
    const term = strategySearch.trim().toLowerCase()
    const filterItem = (arr: StrategyItem[]) => term ? arr.filter(it => it.text.toLowerCase().includes(term)) : arr
    const sorters: Record<string, (a: StrategyItem, b: StrategyItem) => number> = {
      impact: (a, b) => ({"Alto":0, "Medio":1, "Bajo":2}[a.impact] - {"Alto":0, "Medio":1, "Bajo":2}[b.impact]),
      date: (a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime(),
      alpha: (a, b) => a.text.localeCompare(b.text),
    }
    const sorter = sorters[strategySort]
    return {
      opportunities: filterItem(data.opportunities).sort(sorter),
      risks: filterItem(data.risks).sort(sorter),
      trends: filterItem(data.trends).sort(sorter),
      quotes: term ? data.quotes.filter(t => t.toLowerCase().includes(term)) : data.quotes,
      ctas: term ? data.ctas.filter(t => t.toLowerCase().includes(term)) : data.ctas,
    }
  }, [insightsRows, strategySearch, strategySort])

  // Agregados por tema y métricas para KPIs y matriz
  const themeAggregates = useMemo(() => {
    const themeMap: Record<string, { count: number; impactSum: number }> = {}
    const allItems: StrategyItem[] = [...aggregatedInsights.opportunities, ...aggregatedInsights.risks, ...aggregatedInsights.trends]
    const toNum = (imp: "Alto" | "Medio" | "Bajo") => imp === 'Alto' ? 1 : imp === 'Medio' ? 0.5 : 0.2
    allItems.forEach((it) => {
      const themes = it.themes && it.themes.length ? it.themes : ['Otros']
      themes.forEach((th) => {
        if (!themeMap[th]) themeMap[th] = { count: 0, impactSum: 0 }
        themeMap[th].count += 1
        themeMap[th].impactSum += toNum(it.impact)
      })
    })
    const list = Object.entries(themeMap).map(([theme, v]) => ({ theme, freq: v.count, impactAvg: v.impactSum / Math.max(v.count, 1) }))
    const maxFreq = Math.max(1, ...list.map(l => l.freq))
    return { list, maxFreq }
  }, [aggregatedInsights])

  const [matrixSelectedTheme, setMatrixSelectedTheme] = useState<string | null>(null)

  // Sugerir CTAs cuando no existan en los insights: derivar de oportunidades/ riesgos/ tendencias
  const suggestedCtas: string[] = useMemo(() => {
    if (aggregatedInsights.ctas && aggregatedInsights.ctas.length > 0) {
      return aggregatedInsights.ctas
    }
    const derived: string[] = []
    aggregatedInsights.opportunities.slice(0, 10).forEach((o) => {
      derived.push(`Aprovechar oportunidad: ${o.text}`)
    })
    aggregatedInsights.trends.slice(0, 10).forEach((t) => {
      derived.push(`Capitalizar tendencia: ${t.text}`)
    })
    aggregatedInsights.risks.slice(0, 10).forEach((r) => {
      derived.push(`Mitigar riesgo: ${r.text}`)
    })
    return derived
  }, [aggregatedInsights])

  const refreshPromptsAndTopics = async () => {
    try {
      const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic }
      const promptsRes = await getPrompts(dateRange!, filters)
      setPromptsGrouped(promptsRes.topics)
      // Refrescar catálogo completo de topics desde la API global
      try {
        const topicsRes = await getTopics()
        setTopicOptions(["all", ...(topicsRes.topics || [])])
      } catch {}
    } catch (e) {
      console.error("No se pudieron refrescar prompts/topics", e)
    }
  }

  // eliminado: cálculo remoto de métricas por topic; ahora se resume a partir de prompts

  const handleCreatePrompt = async () => {
    try {
      if (!newPromptQuery.trim()) return
      // Usamos el tópico que el usuario ha aceptado explícitamente.
      const detected = autoDetectedTopic || newPromptTopic.trim() || undefined
      await createPrompt({ query: newPromptQuery.trim(), topic: detected, brand: newPromptBrand.trim() || undefined })
      
      // --- INICIO DE LA CORRECCIÓN ---
      // Resetear TODOS los estados del modal a sus valores iniciales
      setAddPromptOpen(false)
      setNewPromptQuery("")
      setNewPromptTopic("")
      setNewPromptBrand("")
      setAutoDetectedTopic("")
      setAddPromptStep('input'); // <-- ESTA LÍNEA ES LA CLAVE
      // --- FIN DE LA CORRECCIÓN ---

      await refreshPromptsAndTopics()
    } catch (e) {
      console.error("No se pudo crear el prompt", e)
      // Opcional: mostrar un paso de error si la creación falla
      setAddPromptStep('error');
    }
  } 

  const openEditPrompt = (id: number, query: string, topic?: string | null, brand?: string | null) => {
    setEditPromptId(id)
    setEditPromptQuery(query || "")
    setEditPromptTopic(topic || "")
    setEditPromptBrand(brand || "")
    setEditPromptOpen(true)
  }

  const handleUpdatePrompt = async () => {
    if (!editPromptId) return
    try {
      await updatePrompt(editPromptId, {
        query: editPromptQuery,
        topic: editPromptTopic || undefined,
        brand: editPromptBrand || undefined,
      })
      setEditPromptOpen(false)
      await refreshPromptsAndTopics()
    } catch (e) {
      console.error("No se pudo actualizar el prompt", e)
    }
  }

  const handleDeletePrompt = async (id: number) => {
    try {
      await deletePrompt(id)
      await refreshPromptsAndTopics()
    } catch (e) {
      console.error("No se pudo eliminar el prompt", e)
    }
  }

  // 4. MANEJADORES DE EVENTOS PARA LOS FILTROS
  const handlePresetChange = (period: PresetPeriod) => {
    if (period === 'custom') return; // 'custom' se maneja por el calendario
    setActivePeriod(period);
    const days = parseInt(period.replace('d', ''));
    setDateRange({
        from: subDays(new Date(), days - 1),
        to: new Date(),
    });
  };

  const handleCustomDateChange = (range: DateRange | undefined) => {
    setDateRange(range)
    setActivePeriod('custom')
  }

  // 5. MANEJO DE CARGA Y ERROR (sin cambios)
  if (isLoading) { return <div className="flex h-screen w-full items-center justify-center"><p>Cargando datos del dashboard...</p></div> }
  if (error) { return <div className="flex h-screen w-full items-center justify-center bg-red-50 p-4"><p className="text-red-600">{error}</p></div> }
  
  const selectedCompetitor = competitorData.find(c => c.selected);
  const sovBrand = competitorData.find(c => c.name === primaryBrandName) || selectedCompetitor || competitorData[0];

  

  // 6. RENDERIZADO con los filtros separados
  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar (sin cambios) */}
      <div className="w-64 bg-white border-r border-gray-200 shadow-sm flex flex-col min-h-0">
        <div className="p-4 flex-1 overflow-hidden">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-white border border-gray-200 rounded flex items-center justify-center shadow-sm">
              <BarChart3 className="w-4 h-4 text-gray-700" />
            </div>
            <span className="text-black font-semibold">Analítica</span>
          </div>
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Buscar"
              className="pl-10 bg-white border-gray-200 text-black placeholder:text-gray-500 shadow-sm"
            />
          </div>
          <nav className="space-y-1">
            <Button variant="ghost" className={`w-full justify-start text-black rounded-md hover:bg-gradient-to-r hover:from-gray-200 hover:to-gray-100 ${ activeSidebarSection === "Answer Engine Insights" ? "bg-gray-100" : "" }`} onClick={() => setActiveSidebarSection("Answer Engine Insights")}> <Zap className="w-4 h-4 mr-3" /> Insights del Answer Engine </Button>
            <Button variant="ghost" className={`w-full justify-start text-black hover:text-black hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 rounded-md text-left ${ activeSidebarSection === "Estrategias y objetivos" ? "bg-gray-100" : "" }`} onClick={() => setActiveSidebarSection("Estrategias y objetivos")}> <Target className="w-4 h-4 mr-3 flex-shrink-0" /> <span className="truncate">Estrategias y objetivos </span> </Button>
          </nav>
        </div>
        <div className="p-4 border-t border-gray-200 flex-shrink-0">
          <div className="space-y-2">
            <Button variant="ghost" className="w-full justify-start text-black hover:text-black hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 rounded-md text-sm"> <Settings className="w-4 h-4 mr-3" /> Soporte </Button>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-xs text-white font-semibold shadow-sm flex-shrink-0"> B </div>
              <span className="text-sm text-black truncate">Breno Lasserre</span>
            </div>
          </div>
        </div>
      </div>
      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-white">
        {activeSidebarSection === "Estrategias y objetivos" ? (
          <>
            <div className="border-b border-gray-200 bg-white shadow-sm">
              <div className="flex items-center justify-between p-6">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Image src="/the-core-logo.png" alt="The Core School" width={28} height={28} className="w-7 h-7 object-contain" />
                    <h1 className="text-xl font-semibold text-black"> The Core School </h1>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <GlobalFiltersToolbar />
                  <Button variant="ghost" size="sm"> <MoreHorizontal className="w-4 h-4" /> </Button>
                </div>
              </div>
              <div className="flex items-center gap-6 px-6 bg-white">
                <Button
                  variant="ghost"
                  className={
                    activeStrategiesTab === "Estrategias"
                      ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black"
                      : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  }
                  onClick={() => setActiveStrategiesTab("Estrategias")}
                >
                  Estrategias
                </Button>
                <Button
                  variant="ghost"
                  className={
                    activeStrategiesTab === "Improve"
                      ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black"
                      : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  }
                  onClick={() => setActiveStrategiesTab("Improve")}
                >
                  Improve
                </Button>
              </div>
            </div>
            <div className="p-6 space-y-6 bg-white">
              {activeStrategiesTab === "Estrategias" && (
                <Card className="shadow-sm bg-white">
                  <CardHeader>
                    <CardTitle className="text-lg font-semibold">Estrategias</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Toolbar */}
                    <div className="flex items-center justify-between mb-4 gap-3">
                      <div className="flex items-center gap-2">
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                          <Input value={strategySearch} onChange={(e) => setStrategySearch(e.target.value)} placeholder="Buscar ideas…" className="pl-10 w-64" />
                        </div>
                        <Button variant={selectedBucket === "all" ? "secondary" : "outline"} onClick={() => setSelectedBucket("all")}>Todas</Button>
                        <Button variant={selectedBucket === "opportunities" ? "secondary" : "outline"} onClick={() => setSelectedBucket("opportunities")}>Oportunidades <Badge variant="secondary" className="ml-2">{aggregatedInsights.opportunities.length}</Badge></Button>
                        <Button variant={selectedBucket === "risks" ? "secondary" : "outline"} onClick={() => setSelectedBucket("risks")}>Riesgos <Badge variant="secondary" className="ml-2">{aggregatedInsights.risks.length}</Badge></Button>
                        <Button variant={selectedBucket === "trends" ? "secondary" : "outline"} onClick={() => setSelectedBucket("trends")}>Tendencias <Badge variant="secondary" className="ml-2">{aggregatedInsights.trends.length}</Badge></Button>
                        <Select value={strategySort} onValueChange={(v: any) => setStrategySort(v)}>
                          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Ordenar por" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="impact">Impacto</SelectItem>
                            <SelectItem value="date">Fecha</SelectItem>
                            <SelectItem value="alpha">Alfabético</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="text-sm text-muted-foreground">{insightsRows.length} insights analizados</div>
                    </div>

                    {insightsLoading ? (<div>Cargando insights...</div>) : (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Oportunidades */}
                        {(selectedBucket === "all" || selectedBucket === "opportunities") && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-sm font-semibold flex items-center gap-2"><Lightbulb className="w-4 h-4" /> Oportunidades</h3>
                              <Badge variant="secondary">{aggregatedInsights.opportunities.length}</Badge>
                            </div>
                            <div className="space-y-2">
                              {aggregatedInsights.opportunities.slice(0, 30).map((item) => (
                                <Collapsible key={item.id}>
                                  <Card className={`${item.impact === 'Alto' ? 'border-l-4 border-blue-500' : ''}`}>
                                    <CardHeader className="flex items-center justify-between gap-2 cursor-pointer">
                                      <CollapsibleTrigger asChild>
                                        <div className="w-full flex items-center justify-between">
                                        <div className="flex-1">
                                          <div className="text-xs text-green-700 mb-1 flex items-center gap-2">Oportunidad
                                            <Badge variant="outline" className={`${item.impact === 'Alto' ? 'text-red-600 border-red-200 bg-red-50' : item.impact === 'Medio' ? 'text-yellow-700 border-yellow-200 bg-yellow-50' : 'text-gray-700 border-gray-200 bg-gray-50'}`}>{item.impact}</Badge>
                                            {plannedItems.includes(item.text) && <CheckCircle2 className="w-4 h-4 text-green-600" />}
                                          </div>
                                          <CardTitle className="text-sm text-gray-900">{item.text}</CardTitle>
                                        </div>
                                        <CardAction>
                                          <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                              <Button size="icon" variant="ghost"><MoreHorizontal className="w-4 h-4" /></Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                              <DropdownMenuItem onClick={() => setPlannedItems((prev) => [...prev, item.text])}>Añadir al plan</DropdownMenuItem>
                                              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(item.text)}>Copiar</DropdownMenuItem>
                                              <DropdownMenuSeparator />
                                              <DropdownMenuItem variant="destructive">Archivar</DropdownMenuItem>
                                            </DropdownMenuContent>
                                          </DropdownMenu>
                                        </CardAction>
                                        </div>
                                      </CollapsibleTrigger>
                                    </CardHeader>
                                    <CollapsibleContent>
                                      <CardContent>
                                        <p className="text-sm text-muted-foreground">Detalle adicional del insight.</p>
                                      </CardContent>
                                      <CardFooter>
                                        <span className="text-xs text-muted-foreground">Creado: {item.createdAt || '—'}</span>
                                      </CardFooter>
                                    </CollapsibleContent>
                                  </Card>
                                </Collapsible>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Riesgos */}
                        {(selectedBucket === "all" || selectedBucket === "risks") && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-sm font-semibold flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Riesgos</h3>
                              <Badge variant="secondary">{aggregatedInsights.risks.length}</Badge>
                            </div>
                            <div className="space-y-2">
                              {aggregatedInsights.risks.slice(0, 30).map((item) => (
                                <Collapsible key={item.id}>
                                  <Card className={`${item.impact === 'Alto' ? 'border-l-4 border-blue-500' : ''}`}>
                                    <CardHeader className="flex items-center justify-between gap-2 cursor-pointer">
                                      <CollapsibleTrigger asChild>
                                        <div className="w-full flex items-center justify-between">
                                        <div className="flex-1">
                                          <div className="text-xs text-red-700 mb-1 flex items-center gap-2">Riesgo
                                            <Badge variant="outline" className={`${item.impact === 'Alto' ? 'text-red-600 border-red-200 bg-red-50' : item.impact === 'Medio' ? 'text-yellow-700 border-yellow-200 bg-yellow-50' : 'text-gray-700 border-gray-200 bg-gray-50'}`}>{item.impact}</Badge>
                                            {plannedItems.includes(item.text) && <CheckCircle2 className="w-4 h-4 text-green-600" />}
                                          </div>
                                          <CardTitle className="text-sm text-gray-900">{item.text}</CardTitle>
                                        </div>
                                        <CardAction>
                                          <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                              <Button size="icon" variant="ghost"><MoreHorizontal className="w-4 h-4" /></Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                              <DropdownMenuItem onClick={() => setPlannedItems((prev) => [...prev, item.text])}>Añadir al plan</DropdownMenuItem>
                                              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(item.text)}>Copiar</DropdownMenuItem>
                                              <DropdownMenuSeparator />
                                              <DropdownMenuItem variant="destructive">Archivar</DropdownMenuItem>
                                            </DropdownMenuContent>
                                          </DropdownMenu>
                                        </CardAction>
                                        </div>
                                      </CollapsibleTrigger>
                                    </CardHeader>
                                    <CollapsibleContent>
                                      <CardContent>
                                        <p className="text-sm text-muted-foreground">Detalle adicional del insight.</p>
                                      </CardContent>
                                      <CardFooter>
                                        <span className="text-xs text-muted-foreground">Creado: {item.createdAt || '—'}</span>
                                      </CardFooter>
                                    </CollapsibleContent>
                                  </Card>
                                </Collapsible>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Tendencias */}
                        {(selectedBucket === "all" || selectedBucket === "trends") && (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-sm font-semibold flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Tendencias</h3>
                              <Badge variant="secondary">{aggregatedInsights.trends.length}</Badge>
                            </div>
                            <div className="space-y-2">
                              {aggregatedInsights.trends.slice(0, 30).map((item) => (
                                <Collapsible key={item.id}>
                                  <Card className={`${item.impact === 'Alto' ? 'border-l-4 border-blue-500' : ''}`}>
                                    <CardHeader className="flex items-center justify-between gap-2 cursor-pointer">
                                      <CollapsibleTrigger asChild>
                                        <div className="w-full flex items-center justify-between">
                                        <div className="flex-1">
                                          <div className="text-xs text-blue-700 mb-1 flex items-center gap-2">Tendencia
                                            <Badge variant="outline" className={`${item.impact === 'Alto' ? 'text-red-600 border-red-200 bg-red-50' : item.impact === 'Medio' ? 'text-yellow-700 border-yellow-200 bg-yellow-50' : 'text-gray-700 border-gray-200 bg-gray-50'}`}>{item.impact}</Badge>
                                            {plannedItems.includes(item.text) && <CheckCircle2 className="w-4 h-4 text-green-600" />}
                                          </div>
                                          <CardTitle className="text-sm text-gray-900">{item.text}</CardTitle>
                                        </div>
                                        <CardAction>
                                          <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                              <Button size="icon" variant="ghost"><MoreHorizontal className="w-4 h-4" /></Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                              <DropdownMenuItem onClick={() => setPlannedItems((prev) => [...prev, item.text])}>Añadir al plan</DropdownMenuItem>
                                              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(item.text)}>Copiar</DropdownMenuItem>
                                              <DropdownMenuSeparator />
                                              <DropdownMenuItem variant="destructive">Archivar</DropdownMenuItem>
                                            </DropdownMenuContent>
                                          </DropdownMenu>
                                        </CardAction>
                                        </div>
                                      </CollapsibleTrigger>
                                    </CardHeader>
                                    <CollapsibleContent>
                                      <CardContent>
                                        <p className="text-sm text-muted-foreground">Detalle adicional del insight.</p>
                                      </CardContent>
                                      <CardFooter>
                                        <span className="text-xs text-muted-foreground">Creado: {item.createdAt || '—'}</span>
                                      </CardFooter>
                                    </CollapsibleContent>
                                  </Card>
                                </Collapsible>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
              {activeStrategiesTab === "Improve" && (
                <Card className="shadow-sm bg-white">
                  <CardHeader>
                    <CardTitle className="text-lg font-semibold">Improve</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {insightsLoading ? (
                      <div>Cargando acciones...</div>
                    ) : (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div className="lg:col-span-2 space-y-2">
                          {(suggestedCtas.length > 0 ? suggestedCtas : aggregatedInsights.ctas).slice(0, 50).map((cta, i) => (
                            <div key={`cta-${i}`} className="flex items-start gap-2 p-2 border rounded">
                              <div className="mt-1 w-2 h-2 rounded-full bg-green-500" />
                              <div className="text-sm text-gray-900">{cta}</div>
                              <div className="ml-auto flex items-center gap-2">
                                <Button size="sm" variant="outline" onClick={() => setPlannedItems((prev) => [...prev, cta])}>Añadir al plan</Button>
                                <Button size="sm" variant="ghost" onClick={() => navigator.clipboard.writeText(cta)}>Copiar</Button>
                              </div>
                            </div>
                          ))}
                          {aggregatedInsights.quotes.slice(0, 8).map((q, i) => (
                            <div key={`q-${i}`} className="p-3 border rounded bg-gray-50 text-sm italic text-gray-700">"{q}"</div>
                          ))}
                          {suggestedCtas.length === 0 && aggregatedInsights.quotes.length === 0 && (
                            <div className="p-6 border rounded text-sm text-muted-foreground bg-gray-50">
                              No hay recomendaciones para este rango y filtros. Ajusta los filtros o genera nuevas menciones para ver sugerencias aquí.
                            </div>
                          )}
                        </div>
                        <div className="lg:col-span-1">
                          <Card className="shadow-sm bg-white sticky top-4">
                            <CardHeader>
                              <CardTitle className="text-sm">Plan de acción ({plannedItems.length})</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2 max-h-[360px] overflow-auto">
                                {plannedItems.length === 0 ? (
                                  <div className="text-sm text-muted-foreground">Añade elementos desde las listas para construir tu plan.</div>
                                ) : (
                                  plannedItems.map((p, i) => (
                                    <div key={`plan-${i}`} className="flex items-start gap-2 p-2 border rounded bg-white">
                                      <div className="mt-1 w-2 h-2 rounded-full bg-blue-500" />
                                      <div className="text-sm text-gray-900 flex-1">{p}</div>
                                      <Button size="icon" variant="ghost" onClick={() => setPlannedItems(prev => prev.filter((_, idx) => idx !== i))}>×</Button>
                                    </div>
                                  ))
                                )}
                              </div>
                              <div className="mt-3 flex gap-2">
                                <Input value={newPlanItem} onChange={(e) => setNewPlanItem(e.target.value)} placeholder="Añadir nota rápida" />
                                <Button
                                  onClick={() => {
                                    if (!newPlanItem.trim()) return
                                    setPlannedItems((prev) => [...prev, newPlanItem.trim()])
                                    setNewPlanItem("")
                                  }}
                                >Añadir</Button>
                              </div>
                              <div className="mt-3 flex gap-2">
                                <Button className="flex-1" onClick={() => navigator.clipboard.writeText(plannedItems.join("\n"))}>Copiar plan</Button>
                                <Button variant="outline" onClick={() => setPlannedItems([])}>Limpiar</Button>
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </>
        ) : (
          <>
            {/* Header */}
            <div className="border-b border-gray-200 bg-white shadow-sm">
              <div className="flex items-center justify-between p-6">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Image src="/the-core-logo.png" alt="The Core School" width={28} height={28} className="w-7 h-7 object-contain" />
                    <h1 className="text-xl font-semibold text-black"> The Core School </h1>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm"> <MoreHorizontal className="w-4 h-4" /> </Button>
                </div>
              </div>
              {/* Navigation Tabs */}
              <div className="flex items-center gap-6 px-6 bg-white">
                <Button variant="ghost" className={ activeTab === "Visibility" ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black" : "text-gray-600 hover:text-gray-800 hover:bg-gray-100" } onClick={() => setActiveTab("Visibility")}>Visibilidad</Button>
                <Button variant="ghost" className={ activeTab === "Prompts" ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black" : "text-gray-600 hover:text-gray-800 hover:bg-gray-100" } onClick={() => setActiveTab("Prompts")}>Prompts</Button>
                <Button variant="ghost" className={ activeTab === "Sentiment" ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black" : "text-gray-600 hover:text-gray-800 hover:bg-gray-100" } onClick={() => setActiveTab("Sentiment")}>Sentimiento</Button>
                
                {/* Filtro de modelo se movió al toolbar de filtros globales */}
              </div>
            </div>
            {/* Dashboard Content */}
            <div className="p-6 space-y-6 bg-white">
                {activeTab === 'Visibility' && (
                  <>
                    <div className="flex items-center justify-between">
                      <GlobalFiltersToolbar />
                      <div className="flex items-center gap-2"></div>
                    </div>
                    
                    {/* Contenido de visibilidad condicionado a que haya datos */}
                    {visibility ? (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
                      <div className="lg:col-span-2 h-full">
                        <Card className="shadow-sm bg-white h-full min-h-[420px]">
                          <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                              <CardTitle className="text-lg font-semibold">Puntuación de visibilidad</CardTitle>
                              <p className="text-sm text-muted-foreground"> Frecuencia con la que The Core School aparece en respuestas generadas por IA </p>
                            </div>
                            <div className="flex items-center gap-1 border p-1 rounded-md bg-gray-50">
                              <Button
                                size="sm"
                                variant={visibilityGranularity === 'day' ? 'secondary' : 'ghost'}
                                onClick={() => setVisibilityGranularity('day')}
                                className="text-xs"
                              >
                                Día
                              </Button>
                              <Button
                                size="sm"
                                variant={visibilityGranularity === 'hour' ? 'secondary' : 'ghost'}
                                onClick={() => setVisibilityGranularity('hour')}
                                className="text-xs"
                              >
                                Poll
                              </Button>
                            </div>
                          </CardHeader>
                          <CardContent className="flex flex-col h-full">
                            <div className="mb-4">
                              <div className="flex items-baseline gap-2">
                                <span className="text-3xl font-bold">{visibility.visibility_score.toFixed(1)}%</span>
                                <span className={visibility.delta >= 0 ? "text-green-500 flex items-center gap-1" : "text-red-500 flex items-center gap-1"}>
                                  {visibility.delta >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                  {visibility.delta.toFixed(1)}%
                                </span>
                              </div>
                            </div>
                            <div className="flex-1 flex items-center justify-center">
                              <ResponsiveContainer width="100%" height="100%">
                                {visibilityChartType === "line" ? (
                                  <LineChart data={visibility.series}>
                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
                                    <YAxis
                                      axisLine={false}
                                      tickLine={false}
                                      domain={[0, 100]}
                                      ticks={[0,10,20,30,40,50,60,70,80,90,100]}
                                      tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                                      tickFormatter={(v: number) => `${v}%`}
                                    />
                                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} formatter={(v: number) => [`${Number(v).toFixed(1)}%`, 'Índice de Visibilidad']} />
                                    <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={2} dot={{ fill: "#000", strokeWidth: 2, r: 4 }} />
                                    {visibilityBrush && <Brush dataKey="date" height={20} />}
                                  </LineChart>
                                ) : (
                                  <AreaChart data={visibility.series}>
                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
                                    <YAxis
                                      axisLine={false}
                                      tickLine={false}
                                      domain={[0, 100]}
                                      ticks={[0,10,20,30,40,50,60,70,80,90,100]}
                                      tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                                      tickFormatter={(v: number) => `${v}%`}
                                    />
                                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} formatter={(v: number) => [`${Number(v).toFixed(1)}%`, 'Índice de Visibilidad']} />
                                    <Area type="monotone" dataKey="value" stroke="#000" fill="hsl(var(--chart-2))" fillOpacity={0.2} />
                                    {visibilityBrush && <Brush dataKey="date" height={20} />}
                                  </AreaChart>
                                )}
                              </ResponsiveContainer>
                            </div>
                            {/* Leyendas y enlaces removidos por solicitud */}
                          </CardContent>
                        </Card>
                      </div>
                      <div className="h-full">
                        <Card className="shadow-sm bg-white h-full min-h-[420px]">
                          <CardHeader>
                            <CardTitle className="text-lg font-semibold">Ranking de visibilidad</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="mb-4">
                               {selectedCompetitor && (
                                <div className="flex items-baseline gap-2">
                                  <span className="text-3xl font-bold">#{selectedCompetitor.rank}</span>
                                  <span className="text-green-500 flex items-center gap-1">
                                    <TrendingUp className="w-4 h-4" />1
                                  </span>
                                </div>
                               )}
                            </div>
                            <div className="space-y-3">
                              <div className="flex items-center justify-between text-sm font-medium text-muted-foreground">
                                <span>Activo</span>
                                <span>Puntuación de visibilidad</span>
                              </div>
                              {visibilityRanking.map((competitor) => (
                                <div
                                  key={competitor.rank}
                                  className={`flex items-center justify-between p-2 rounded ${
                                    competitor.selected ? "bg-accent/20" : ""
                                  }`}
                                >
                                  <div className="flex items-center gap-3">
                                    <span className="text-sm text-muted-foreground">{competitor.rank}.</span>
                                    <div className={`w-3 h-3 rounded-full ${competitor.color}`}></div>
                                    <span className="text-sm font-medium">
                                      {competitor.name}
                                      {competitor.selected && (
                                        <Badge variant="secondary" className="ml-2 text-xs">
                                          Seleccionado
                                        </Badge>
                                      )}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">{competitor.score}</span>
                                    <span
                                      className={`text-xs ${competitor.positive ? "text-green-500" : "text-red-500"}`}
                                    >
                                      {competitor.change}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                            <Button variant="link" className="w-full mt-4 text-sm"> Expandir </Button>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                    ) : (
                      <Card className="shadow-sm bg-white">
                        <CardContent>
                          <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
                            Sin datos para el rango o filtros seleccionados.
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Share of Voice Section - conectado a /api/industry/ranking */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
                      <div className="lg:col-span-2 h-full">
                        <Card className="shadow-sm bg-white h-full min-h-[420px]">
                          <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                              <CardTitle className="text-lg font-semibold">Share of Voice</CardTitle>
                              <p className="text-sm text-muted-foreground"> Menciones de {primaryBrandName} en respuestas generadas por IA en relación con competidores </p>
                            </div>
                            {/* Controles de configuración removidos por solicitud */}
                          </CardHeader>
                          <CardContent className="flex flex-col h-full">
                            {/* Pie chart comparativo de share of voice por marca */}
                            <div className="flex-1 flex items-center justify-center">
                              <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={sovDonut ? 50 : 0} paddingAngle={2} label={sovShowLabels}>
                                    {pieData.map((entry, index) => (
                                      <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                  </Pie>
                                  <Tooltip formatter={(value, name) => [`${Number(value).toFixed(1)}%`, name as string]} />
                                </PieChart>
                              </ResponsiveContainer>
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      <div className="h-full">
                        <Card className="shadow-sm bg-white h-full">
                          <CardHeader>
                            <CardTitle className="text-lg font-semibold">Ranking de Share of Voice</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="mb-4">
                              {sovBrand && (
                                <div className="flex items-baseline gap-2">
                                  <span className="text-3xl font-bold">#{sovBrand.rank}</span>
                                  <span className={`${sovBrand.positive ? "text-green-500" : "text-red-500"} flex items-center gap-1`}>
                                    {sovBrand.positive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                    1
                                  </span>
                                </div>
                              )}
                            </div>

                            <div className="space-y-3">
                              <div className="flex items-center justify-between text-sm font-medium text-muted-foreground">
                                <span>Activo</span>
                                <span>Share of Voice</span>
                              </div>
                              {competitorData.map((competitor) => (
                                <div
                                  key={competitor.rank}
                                  className={`flex items-center justify-between p-2 rounded ${competitor.name === primaryBrandName ? "bg-accent/20" : ""}`}
                                >
                                  <div className="flex items-center gap-3">
                                    <span className="text-sm text-muted-foreground">{competitor.rank}.</span>
                                    <div className={`w-3 h-3 rounded-full ${competitor.color}`}></div>
                                    <span className="text-sm font-medium">{competitor.name}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">{competitor.score}</span>
                                    <span className={`text-xs ${competitor.positive ? "text-green-500" : "text-red-500"}`}>{competitor.change}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </div>

                    
                  </>
                )}
                {activeTab === 'Sentiment' && (
                  <>
                    <div className="flex items-center justify-between">
                      <GlobalFiltersToolbar />
                      <div className="flex items-center gap-2"></div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      <div className="lg:col-span-2">
                        <Card className="shadow-sm bg-white">
                          <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                              <CardTitle className="text-lg font-semibold">Análisis de sentimiento</CardTitle>
                              <p className="text-sm text-muted-foreground"> Sentimiento positivo a lo largo del tiempo </p>
                            </div>
                            {/* Controles de configuración removidos por solicitud */}
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
                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} domain={[0, 100]} />
                                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Positivo']} />
                                    <Line type="monotone" dataKey="value" stroke="hsl(var(--chart-1))" strokeWidth={2} dot={{ fill: "hsl(var(--chart-1))", strokeWidth: 2, r: 4 }} />
                                    {sentimentBrush && <Brush dataKey="date" height={20} />}
                                  </LineChart>
                                ) : (
                                  <AreaChart data={[...(sentimentComputed.timeseries || [])]}>
                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} domain={[0, 100]} />
                                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Positivo']} />
                                    <Area type="monotone" dataKey="value" stroke="hsl(var(--chart-1))" fill="hsl(var(--chart-1))" fillOpacity={0.2} />
                                    {sentimentBrush && <Brush dataKey="date" height={20} />}
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
                              {/* Positivo */}
                              {sentimentComputed.positives && sentimentComputed.positives.length > 0 ? (
                                (() => { const p = sentimentComputed.positives[posHighlightIdx % sentimentComputed.positives.length]; return (
                                  <div key={`pos-${p.id}-${posHighlightIdx}`} className="p-3 border rounded bg-green-50 border-green-200">
                                    <div className="text-xs text-green-700 mb-1">Positivo · {p.sentiment?.toFixed(2)}</div>
                                    <div className="text-sm text-gray-900 line-clamp-3">{p.summary || ''}</div>
                                    <div className="mt-2 flex flex-wrap gap-1">
                                      {(p.key_topics || []).slice(0, 5).map((t, i) => (
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

                              {/* Negativo */}
                              {sentimentComputed.negatives && sentimentComputed.negatives.length > 0 ? (
                                (() => { const m = sentimentComputed.negatives[negHighlightIdx % sentimentComputed.negatives.length]; return (
                                  <div key={`neg-${m.id}-${negHighlightIdx}`} className="p-3 border rounded bg-red-50 border-red-200">
                                    <div className="text-xs text-red-700 mb-1">Negativo · {m.sentiment?.toFixed(2)}</div>
                                    <div className="text-sm text-gray-900 line-clamp-3">{m.summary || ''}</div>
                                    <div className="mt-2 flex flex-wrap gap-1">
                                      {(m.key_topics || []).slice(0, 5).map((t, i) => (
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

                    {/* Topics cloud (AHORA AGRUPADO) */}
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
                                                        <div
                                                          className={`h-2 rounded-full ${sentimentScore > 60 ? 'bg-green-500' : sentimentScore < 40 ? 'bg-red-500' : 'bg-yellow-500'}`}
                                                          style={{ width: `${sentimentScore}%` }}
                                                        />
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
                                                <div
                                                  className={`h-2 rounded-full ${sentimentScore > 60 ? 'bg-green-500' : sentimentScore < 40 ? 'bg-red-500' : 'bg-yellow-500'}`}
                                                  style={{ width: `${sentimentScore}%` }}
                                                />
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
                )}
                {activeTab === 'Prompts' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <h2 className="text-xl font-semibold text-gray-900">Prompts</h2>
                        {/* Filtro de Tema igual al de Visibilidad */}
                        <Select value={selectedTopic} onValueChange={(v) => setSelectedTopic(v)}>
                          <SelectTrigger className="w-[220px]">
                            <SelectValue placeholder="Todos los topics" />
                          </SelectTrigger>
                          <SelectContent>
                            {topicOptions.map((t) => (
                              <SelectItem key={t} value={t}>{t === 'all' ? 'Todos los topics' : translateTopicToSpanish(t)}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {/* Filtro de modelo (entre topics y añadir) */}
                        <Select value={selectedModel} onValueChange={setSelectedModel}>
                          <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Todos los modelos" />
                          </SelectTrigger>
                          <SelectContent>
                            {modelOptions.map((m) => (
                              <SelectItem key={m} value={m}>{m === 'all' ? 'Todos los modelos' : m}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Button size="sm" onClick={() => setAddPromptOpen(true)} className="shadow-sm">+ Añadir Prompt</Button>
                      </div>
                      {/* Buscador de temas eliminado por solicitud */}
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
                                // --- ESTADO DE CARGA (SKELETON) ---
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
                                // --- RENDERIZADO DE DATOS REALES ---
                                (() => {
                                  // Sin buscador: usar todos los grupos
                                  const filtered = promptsGrouped
                                  return filtered.map((group, index) => {
                                    // --- LÓGICA DE CÁLCULO UNIFICADA Y CORRECTA ---
                                    const avgVisibility = group.prompts.length > 0
                                      ? group.prompts.reduce((sum, p) => sum + (p.visibility_score_individual ?? 0), 0) / group.prompts.length
                                      : 0
                                    // SOV del topic = media de los SOV de sus prompts
                                    const avgSov = group.prompts.length > 0
                                      ? group.prompts.reduce((sum, p) => sum + (p.share_of_voice_individual ?? 0), 0) / group.prompts.length
                                      : 0
                                    const rank = index + 1
                                    const isOpen = !!openTopics[group.topic]
                                    return (
                                      <React.Fragment key={group.topic}>
                                        <tr
                                          className="border-b border-gray-100 hover:bg-gray-50 bg-white cursor-pointer"
                                          onClick={() => {
                                            setOpenTopics(prev => ({ ...prev, [group.topic]: !prev[group.topic] }))
                                          }}
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

                    {/* Rankings laterales eliminados por solicitud */}
                  </div>
                )}
                {/* Modal de detalle de prompt */}
                <Dialog open={promptModalOpen} onOpenChange={setPromptModalOpen}>
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
                        {/* Columna Izquierda: Métricas + Tendencias */}
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

                        {/* Columna Derecha: Gráficos */}
                        <div className="flex flex-col gap-6">
                          <Card>
                            <CardHeader><CardTitle className="text-sm">Puntuación de Visibilidad (Evolución)</CardTitle></CardHeader>
                            <CardContent className="h-[250px] w-full">
                              <ResponsiveContainer>
                                <LineChart data={promptDetails.timeseries}>
                                  <XAxis dataKey="date" stroke="#888888" fontSize={12} />
                                  <YAxis stroke="#888888" fontSize={12} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                  <Tooltip formatter={(value) => [`${value}%`, "Visibilidad"]} />
                                  <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={2} dot={{ r: 3, fill: "#000" }} />
                                </LineChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                          <Card>
                            <CardHeader><CardTitle className="text-sm">Share of Voice (Evolución)</CardTitle></CardHeader>
                            <CardContent className="h-[250px] w-full">
                              <ResponsiveContainer>
                                <LineChart data={promptDetails.sov_timeseries}>
                                  <XAxis dataKey="date" stroke="#888888" fontSize={12} />
                                  <YAxis stroke="#888888" fontSize={12} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                                  <Tooltip formatter={(value) => [`${value}%`, "Share of Voice"]} />
                                  <Line type="monotone" dataKey="value" stroke="#000" strokeWidth={2} dot={{ r: 3, fill: "#000" }} />
                                </LineChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </div>
                      </div>
                    ) : (<div className="p-6 text-center">No se encontraron detalles para este prompt.</div>)}
                  </DialogContent>
                </Dialog>

                {/* Dialogo de respuesta completa y navegación entre ejecuciones */}
                <Dialog open={execDialogOpen} onOpenChange={setExecDialogOpen}>
                  <DialogContent className="w-[96vw] max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle className="text-base">Respuesta completa</DialogTitle>
                    </DialogHeader>
                    {promptDetails && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <span>Motor:</span>
                            <Badge variant="secondary">{(promptDetails.executions[execActiveIndex] || {}).engine}</Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button size="sm" variant="outline" onClick={() => setExecActiveIndex((i) => Math.max(0, i - 1))}>Anterior</Button>
                            <Button size="sm" onClick={() => setExecActiveIndex((i) => Math.min((promptDetails.executions.length - 1), i + 1))}>Siguiente</Button>
                          </div>
                        </div>
                        <div className="whitespace-pre-wrap text-sm border rounded-lg p-3 bg-background/80">
                          {(promptDetails.executions[execActiveIndex] || {}).response}
                        </div>
                      </div>
                    )}
                  </DialogContent>
                </Dialog>

                {/* Modal por pasos para crear nuevo prompt */}
                <Dialog open={addPromptOpen} onOpenChange={(isOpen) => {
                  setAddPromptOpen(isOpen);
                  if (!isOpen) {
                    setAddPromptStep('input');
                    setNewPromptQuery('');
                    setAutoDetectedTopic('');
                  }
                }}>
                  <DialogContent className="sm:max-w-[520px]">
                    {addPromptStep === 'input' && (
                      <>
                        <DialogHeader>
                          <DialogTitle className="text-xl font-semibold text-center">¿Qué prompt quieres monitorizar?</DialogTitle>
                        </DialogHeader>
                        <div className="flex items-center gap-2 pt-4">
                          <Input
                            id="prompt-input"
                            value={newPromptQuery}
                            onChange={(e) => setNewPromptQuery(e.target.value)}
                            placeholder="Ej: becas y ayudas para estudiar cine..."
                            className="w-full"
                            onKeyDown={async (e) => {
                              if (e.key === 'Enter' && newPromptQuery.trim().length >= 10) {
                                setAddPromptStep('thinking');
                                const res = await categorizePromptApi(newPromptQuery);
                                const suggestion = res.suggestion || 'Inclasificable';
                                if (suggestion === 'Inclasificable') {
                                  setAddPromptStep('error');
                                } else {
                                  setAutoDetectedTopic(suggestion);
                                  setAddPromptStep('suggestion');
                                }
                              }
                            }}
                          />
                          <Button 
                            size="icon" 
                            onClick={async () => {
                              if (newPromptQuery.trim().length >= 10) {
                                setAddPromptStep('thinking');
                                const res = await categorizePromptApi(newPromptQuery);
                                const suggestion = res.suggestion || 'Inclasificable';
                                if (suggestion === 'Inclasificable') {
                                  setAddPromptStep('error');
                                } else {
                                  setAutoDetectedTopic(suggestion);
                                  setAddPromptStep('suggestion');
                                }
                              }
                            }} 
                            disabled={newPromptQuery.trim().length < 10}
                          >
                            <ChevronRight className="w-4 h-4" />
                          </Button>
                        </div>
                      </>
                    )}

                    {addPromptStep === 'thinking' && (
                      <div className="flex flex-col items-center justify-center gap-4 py-8">
                        <PulsingCircle position="center" size={120} />
                        <p className="text-sm text-gray-600 animate-pulse">Analizando prompt...</p>
                      </div>
                    )}

                    {addPromptStep === 'suggestion' && (
                      <>
                        <DialogHeader>
                          <DialogTitle className="text-xl font-semibold text-center">Topic Sugerido</DialogTitle>
                        </DialogHeader>
                        <div className="flex flex-col items-center gap-4 py-4">
                          <Badge variant="secondary" className="text-lg px-4 py-2">
                            {translateTopicToSpanish(autoDetectedTopic)}
                          </Badge>
                          <div className="w-full flex justify-end gap-2 mt-4">
                            <Button variant="outline" onClick={() => setAddPromptStep('input')}>Corregir</Button>
                            <Button onClick={handleCreatePrompt}>Aceptar y Añadir</Button>
                          </div>
                        </div>
                      </>
                    )}

                    {addPromptStep === 'error' && (
                      <>
                        <DialogHeader>
                          <DialogTitle className="text-xl font-semibold text-center">No he entendido el prompt</DialogTitle>
                        </DialogHeader>
                        <div className="flex flex-col items-center gap-4 py-4 text-center">
                          <p className="text-sm text-gray-600">
                            La consulta es demasiado ambigua. Por favor, prueba a reformularla siendo más específico sobre lo que quieres monitorizar.
                          </p>
                          <Button onClick={() => setAddPromptStep('input')} className="mt-4">Volver a intentarlo</Button>
                        </div>
                      </>
                    )}
                  </DialogContent>
                </Dialog>

                {/* Modal para editar prompt */}
                <Dialog open={editPromptOpen} onOpenChange={setEditPromptOpen}>
                  <DialogContent className="sm:max-w-[520px]">
                    <DialogHeader>
                      <DialogTitle className="text-lg">Editar Prompt</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Consulta</label>
                        <Input value={editPromptQuery} onChange={(e) => setEditPromptQuery(e.target.value)} />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Topic (opcional)</label>
                        <Input value={editPromptTopic} onChange={(e) => setEditPromptTopic(e.target.value)} />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Brand (opcional)</label>
                        <Input value={editPromptBrand} onChange={(e) => setEditPromptBrand(e.target.value)} />
                      </div>
                      <div className="flex justify-end gap-2 pt-2">
                        <Button variant="outline" onClick={() => setEditPromptOpen(false)}>Cancelar</Button>
                        <Button onClick={handleUpdatePrompt} disabled={!editPromptQuery.trim()}>Guardar</Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
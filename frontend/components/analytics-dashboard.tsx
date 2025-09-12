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
import { getVisibility, getShareOfVoice, getVisibilityRanking, getMentions, getModels, getPrompts, getTopics, getPromptDetails, getSentiment, getTopicsCloud, createPrompt, updatePrompt, deletePrompt, getInsights, categorizePromptApi, type PromptsByTopic, type PromptDetails, type InsightRow, type ShareOfVoiceResponse, type SentimentApiResponse } from "@/services/api"
import { VisibilityData, Competitor, Mention } from "@/types"
import { cn } from "@/lib/utils"
import { DateRange } from "react-day-picker"
import { format, subDays, startOfDay, addDays, addHours, startOfHour } from "date-fns"
import { es } from "date-fns/locale"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import PulsingCircle from "@/components/ui/pulsing-circle"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu"
import GlobalFiltersToolbar, { type PresetPeriod as ToolbarPresetPeriod, type OptionItem as ToolbarOptionItem } from "@/components/GlobalFiltersToolbar"
import VisibilityTab from "@/components/VisibilityTab"
import SentimentTab from "@/components/SentimentTab"
import PromptsTab from "@/components/PromptsTab"
import PromptDetailModal from "@/components/PromptDetailModal"

// INTERFAZ PARA LOS DATOS DE VISIBILIDAD COMPLETOS
interface VisibilityApiResponse {
  visibility_score: number;
  delta: number;
  series: VisibilityData[];
}

// TIPO PARA LOS PERIODOS PREDEFINIDOS
type PresetPeriod = '24h' | '7d' | '30d' | '90d' | 'custom';
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
  const brandName = process.env.NEXT_PUBLIC_BRAND_NAME || 'The Core School'
  const primaryBrandName = brandName
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
  const [sentimentApi, setSentimentApi] = useState<SentimentApiResponse | null>(null)
  const [topicsCloud, setTopicsCloud] = useState<{ topic: string; count: number; avg_sentiment?: number }[]>([])
  const [topicGroups, setTopicGroups] = useState<any[]>([])
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({})
  // Resumen por tema aplicando filtros globales a cada tema individualmente
  // eliminado: topicSummaries (ahora usamos datos de API directamente)

  // Configuración de gráficos (3 opciones): tipo, zoom (brush) y exportar
  const [visibilityChartType, setVisibilityChartType] = useState<"line" | "area">("line")
  // Brush eliminado por solicitud
  const [visibilityBrush, setVisibilityBrush] = useState(false)
  const [visibilityBrushStart, setVisibilityBrushStart] = useState<number | undefined>(undefined)
  const [visibilityBrushEnd, setVisibilityBrushEnd] = useState<number | undefined>(undefined)
  const [visibilityChartKey, setVisibilityChartKey] = useState<string>("")
  const [sovDonut, setSovDonut] = useState(true)
  const [sovShowLabels, setSovShowLabels] = useState(false)
  const [sentimentChartType, setSentimentChartType] = useState<"line" | "area">("line")
  const [sentimentBrush, setSentimentBrush] = useState(false)

  // Índices para rotación de highlights
  const [negHighlightIdx, setNegHighlightIdx] = useState(0)
  const [posHighlightIdx, setPosHighlightIdx] = useState(0)
  // Barra global de filtros reutilizable

  const openPrompt = async (promptId: number) => {
    try {
      setPromptLoading(true)
      const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic, granularity: isHourlyRange ? 'hour' as const : 'day' as const, brand: primaryBrandName }
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

    // Métrica principal: % de menciones positivas (de la marca)
    const positivePercent = (distribution.positive / total) * 100
    const neutralPercent = (distribution.neutral / total) * 100
    const negativePercent = (distribution.negative / total) * 100

    // Mantener delta simple por ahora
    const delta = 0

    // La serie ya viene en porcentaje de positivos
    const scaledTimeseries = (timeseries || []).map(p => ({
      date: p.date,
      value: Math.max(0, Math.min(100, Number(p.value) || 0))
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

  // Ticks y dominio del eje X según rango seleccionado
  const isHourlyRange = useMemo(() => activePeriod.includes('h'), [activePeriod])
  const xDomain = useMemo((): [number, number] => {
    if (!dateRange?.from || !dateRange?.to) return [0, 0]
    if (isHourlyRange) {
      return [dateRange.from.getTime(), dateRange.to.getTime()]
    }
    const start = startOfDay(dateRange.from).getTime()
    const end = startOfDay(dateRange.to).getTime() + 24 * 60 * 60 * 1000
    return [start, end]
  }, [dateRange, isHourlyRange])
  const xTicks = useMemo((): number[] => {
    if (!dateRange?.from || !dateRange?.to) return []
    if (isHourlyRange) {
      const startHour = startOfHour(dateRange.from)
      const end = dateRange.to.getTime()
      const ticks: number[] = []
      for (let d = startHour; d.getTime() <= end; d = addHours(d, 1)) {
        ticks.push(d.getTime())
      }
      return ticks
    }
    const ticks: number[] = []
    for (let d = startOfDay(dateRange.from); d <= startOfDay(dateRange.to); d = addDays(d, 1)) {
      ticks.push(d.getTime())
    }
    return ticks
  }, [dateRange, isHourlyRange])

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

  // Vista única por ejecución (granularidad fija por poll/ejecución)
  const visibilityGranularity: 'day' | 'hour' = 'hour'

  // 3. USEEFFECT (sin cambios en su lógica, siempre depende de dateRange)
  useEffect(() => {
    if (!dateRange?.from || !dateRange?.to) {
        return;
    }
    // Reset del visor (Brush) cuando cambia el rango
    try {
      const start = dateRange.from.getTime()
      const end = dateRange.to.getTime()
      setVisibilityBrushStart(start)
      setVisibilityBrushEnd(end)
      // Forzar remount del chart para que Brush se reinicialice visualmente
      setVisibilityChartKey(`${start}-${end}`)
    } catch {}
    const loadDashboardData = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic, brand: primaryBrandName, granularity: visibilityGranularity }
        // Cargar TODO en paralelo (incluye topics-cloud) para que Sentimientos salga de inmediato
        const [visibilityResponse, visibilityRankingRes, sovResponse, promptsRes, sentimentRes, topicsCloudRes] = await Promise.all([
          getVisibility(dateRange, filters),
          getVisibilityRanking(dateRange, filters),
          getShareOfVoice(dateRange, filters),
          getPrompts(dateRange, filters),
          getSentiment(dateRange, filters),
          getTopicsCloud(dateRange, filters),
        ]);
        setVisibility(visibilityResponse);
        setVisibilityRanking(visibilityRankingRes.ranking || [])
        setCompetitorData((sovResponse as ShareOfVoiceResponse).overall_ranking);
        setSovByTopic((sovResponse as ShareOfVoiceResponse).by_topic || {});
        // Cargar menciones después, sin bloquear render inicial
        getMentions(dateRange, filters).then((m) => setMentions(m.mentions)).catch(() => setMentions([]))
        setPromptsGrouped(promptsRes.topics);
        setSentimentApi(sentimentRes);
        // Temas por categoría: usar grupos de la API o agrupar por defecto
        try {
          const tc = topicsCloudRes as any
          setTopicsCloud((tc?.topics ?? []) as any)
          const apiGroups = (tc?.groups ?? []) as any[]
          if (apiGroups && apiGroups.length > 0) {
            setTopicGroups(apiGroups)
          } else {
            const competitorNames = ((sovResponse as ShareOfVoiceResponse).overall_ranking || []).map(c => (c.name || '').toLowerCase())
            const fallbackGroups = (() => {
              const groupsMap: Record<string, { total_occurrences: number; sum_weighted_sent: number; topics: { topic: string; count: number; avg_sentiment?: number }[] }> = {}
              const ensure = (name: string) => groupsMap[name] || (groupsMap[name] = { total_occurrences: 0, sum_weighted_sent: 0, topics: [] })
              const toKey = (s: string) => (s || '').toLowerCase()
              const isBrand = (t: string) => /\bthe\s*core\b/.test(t)
              const isCompetitor = (t: string) => competitorNames.some(n => n && t.includes(n))
              const isUniversity = (t: string) => /universidad|universitat|complutense|rey\s*juan\s*carlos|navarra/.test(t)
              const isAdmissions = (t: string) => /beca|precio|coste|costo|admis|financiaci[oó]n|matr[ií]cula/.test(t)
              const isJobs = (t: string) => /empleo|empleabilidad|trabajo|salidas/.test(t)
              const isPrograms = (t: string) => /cine|audiovisual|animaci[oó]n|vfx|fotograf[ií]a|guion|gu[ií]on|ingenier[ií]a|software|programaci[oó]n|dise[nñ]o|3d|edici[oó]n/.test(t)
              const OTHER = 'Temas Generales del Sector'
              ;((tc?.topics ?? []) as any[]).forEach((row: any) => {
                const topic = toKey(row.topic)
                const count = Number(row.count || 0)
                const sent = Number(row.avg_sentiment || 0)
                const push = (groupName: string) => {
                  const g = ensure(groupName)
                  g.total_occurrences += count
                  g.sum_weighted_sent += sent * count
                  g.topics.push({ topic: row.topic, count, avg_sentiment: sent })
                }
                if (isBrand(topic)) push('Menciones de Marca Propia')
                else if (isCompetitor(topic)) push('Menciones de Competidores Directos')
                else if (isUniversity(topic)) push('Menciones de Universidades Tradicionales')
                else if (isAdmissions(topic)) push('Becas y Admisiones')
                else if (isJobs(topic)) push('Salidas Profesionales')
                else if (isPrograms(topic)) push('Programas y Grados')
                else push(OTHER)
              })
              return Object.entries(groupsMap).map(([group_name, v]) => ({
                group_name,
                total_occurrences: v.total_occurrences,
                avg_sentiment: v.total_occurrences ? v.sum_weighted_sent / v.total_occurrences : 0,
                topics: v.topics.sort((a, b) => (b.count || 0) - (a.count || 0)).slice(0, 100),
              }))
            })()
            setTopicGroups(fallbackGroups)
          }
        } catch (e) {
          console.error('Error procesando topics-cloud', e)
          setTopicsCloud([])
          setTopicGroups([])
        }
      } catch (err) {
        setError("No se pudieron cargar los datos. Por favor, revisa la consola o el estado del backend.")
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadDashboardData()
  }, [dateRange, selectedModel, selectedTopic, primaryBrandName]);

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
        const filters = { model: selectedModel, source: selectedSource, topic: selectedTopic, brand: primaryBrandName }
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
      const tf = (() => {
        const obj = row?.topic_frequency
        if (obj && typeof obj === 'object') {
          const vals = Object.values(obj as Record<string, number>).map((x) => (typeof x === 'number' ? x : Number(x) || 0))
          const maxVal = vals.length ? Math.max(0, ...vals) : 0
          return Math.min(1, maxVal / 5)
        }
        return 0
      })()
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
    const now = new Date();
    let fromDate: Date;
    if (period.includes('h')) {
      const hours = parseInt(period.replace('h', '')) || 24;
      fromDate = new Date(now.getTime() - hours * 60 * 60 * 1000);
    } else {
      const days = parseInt(period.replace('d', '')) || 30;
      // Incluir el día de hoy en el conteo
      fromDate = subDays(now, days - 1);
    }
    setDateRange({ from: fromDate, to: now });
  };

  // Eliminado el cambio de rango personalizado (DateRangePicker)

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
              <Image src="/juanjo-siguero.jpg" alt="Juanjo Siguero" width={24} height={24} className="w-6 h-6 rounded-full object-cover flex-shrink-0" />
              <span className="text-sm text-black truncate">Juanjo Siguero</span>
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
                    <Image src="/the-core-logo.png" alt={brandName} width={28} height={28} className="w-7 h-7 object-contain" />
                    <h1 className="text-xl font-semibold text-black"> {brandName} </h1>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <GlobalFiltersToolbar
                    activePeriod={activePeriod as ToolbarPresetPeriod}
                    onPresetChange={handlePresetChange}
                    selectedTopic={selectedTopic}
                    onTopicChange={setSelectedTopic}
                    topicOptions={topicOptions.map<ToolbarOptionItem>((t) => ({ value: t, label: t === 'all' ? 'Todos los temas' : translateTopicToSpanish(t) }))}
                    selectedModel={selectedModel}
                    onModelChange={setSelectedModel}
                    modelOptions={modelOptions}
                  />
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
                    <Image src="/the-core-logo.png" alt={brandName} width={28} height={28} className="w-7 h-7 object-contain" />
                    <h1 className="text-xl font-semibold text-black"> {brandName} </h1>
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
                      <GlobalFiltersToolbar
                        activePeriod={activePeriod as ToolbarPresetPeriod}
                        onPresetChange={handlePresetChange}
                        selectedTopic={selectedTopic}
                        onTopicChange={setSelectedTopic}
                        topicOptions={topicOptions.map<ToolbarOptionItem>((t) => ({ value: t, label: t === 'all' ? 'Todos los temas' : translateTopicToSpanish(t) }))}
                        selectedModel={selectedModel}
                        onModelChange={setSelectedModel}
                        modelOptions={modelOptions}
                      />
                      <div className="flex items-center gap-2"></div>
                    </div>
                    
                    {/* Contenido de visibilidad se muestra únicamente junto al ranking más abajo */}

                    {/* Sección superior: Puntuación de visibilidad + Ranking */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
                      <div className="lg:col-span-2 h-full">
                        <VisibilityTab
                          visibility={visibility as any}
                          brandName={brandName}
                          isHourlyRange={isHourlyRange}
                          xDomain={xDomain}
                          xTicks={xTicks}
                          visibilityChartType={visibilityChartType}
                          visibilityChartKey={visibilityChartKey}
                        />
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
                                  <span className={`${selectedCompetitor.positive ? "text-green-500" : "text-red-500"} flex items-center gap-1`}>
                                    {selectedCompetitor.positive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                    {selectedCompetitor.change}
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
                                  className={`flex items-center justify-between p-2 rounded ${competitor.selected ? "bg-accent/20" : ""}`}
                                >
                                  <div className="flex items-center gap-3">
                                    <span className="text-sm text-muted-foreground">{competitor.rank}.</span>
                                    <div className={`w-3 h-3 rounded-full ${competitor.color}`}></div>
                                    <span className="text-sm font-medium">
                                      {competitor.name}
                                      {competitor.selected && (
                                        <Badge variant="secondary" className="ml-2 text-xs">Seleccionado</Badge>
                                      )}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">{competitor.score}</span>
                                    <span className={`text-xs ${competitor.positive ? "text-green-500" : "text-red-500"}`}>{competitor.change}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                            <Button variant="link" className="w-full mt-4 text-sm">Expandir</Button>
                          </CardContent>
                        </Card>
                      </div>
                    </div>

                    {/* Sección inferior: Share of Voice + Ranking */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch mt-6">
                      <div className="lg:col-span-2 h-full">
                        <Card className="shadow-sm bg-white h-full min-h-[420px]">
                          <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                              <CardTitle className="text-lg font-semibold">Share of Voice</CardTitle>
                              <p className="text-sm text-muted-foreground"> Menciones de {brandName} en respuestas generadas por IA en relación con competidores </p>
                            </div>
                          </CardHeader>
                          <CardContent className="flex flex-col h-full">
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
                                  className={`flex items-center justify-between p-2 rounded ${competitor.name === brandName ? "bg-accent/20" : ""}`}
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
                      <GlobalFiltersToolbar
                        activePeriod={activePeriod as ToolbarPresetPeriod}
                        onPresetChange={handlePresetChange}
                        selectedTopic={selectedTopic}
                        onTopicChange={setSelectedTopic}
                        topicOptions={topicOptions.map<ToolbarOptionItem>((t) => ({ value: t, label: t === 'all' ? 'Todos los temas' : translateTopicToSpanish(t) }))}
                        selectedModel={selectedModel}
                        onModelChange={setSelectedModel}
                        modelOptions={modelOptions}
                      />
                      <div className="flex items-center gap-2"></div>
                    </div>

                    <SentimentTab
                      sentimentComputed={sentimentComputed}
                      sentimentChartType={sentimentChartType}
                      sentimentBrush={sentimentBrush}
                      posHighlightIdx={posHighlightIdx}
                      negHighlightIdx={negHighlightIdx}
                      topicsCloud={topicsCloud}
                      topicGroups={topicGroups as any}
                      openGroups={openGroups}
                      setOpenGroups={setOpenGroups}
                      translateTopicToSpanish={translateTopicToSpanish}
                      isHourlyRange={isHourlyRange}
                      xDomain={xDomain}
                      xTicks={xTicks}
                    />
                  </>
                )}
                {activeTab === 'Prompts' && (
                  <PromptsTab
                    activePeriod={activePeriod as PresetPeriod}
                    onPresetChange={handlePresetChange}
                    selectedTopic={selectedTopic}
                    onTopicChange={setSelectedTopic}
                    topicOptions={topicOptions}
                    selectedModel={selectedModel}
                    onModelChange={setSelectedModel}
                    modelOptions={modelOptions}
                    isLoading={isLoading}
                    promptsGrouped={promptsGrouped}
                    openTopics={openTopics}
                    setOpenTopics={setOpenTopics}
                    openPrompt={openPrompt}
                    openEditPrompt={openEditPrompt}
                    handleDeletePrompt={handleDeletePrompt}
                    translateTopicToSpanish={translateTopicToSpanish}
                    emojiForTopic={emojiForTopic}
                  />
                )}
                {/* Modal de detalle de prompt */}
                <PromptDetailModal
                  open={promptModalOpen}
                  onOpenChange={setPromptModalOpen}
                  promptDetails={promptDetails}
                  promptLoading={promptLoading}
                  isHourlyRange={isHourlyRange}
                  xDomain={xDomain}
                  xTicks={xTicks}
                  execDialogOpen={execDialogOpen}
                  setExecDialogOpen={setExecDialogOpen}
                  execActiveIndex={execActiveIndex}
                  setExecActiveIndex={setExecActiveIndex}
                />

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
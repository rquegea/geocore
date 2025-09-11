import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import React from "react"

export type PresetPeriod = '24h' | '7d' | '30d' | '90d' | 'custom'

export interface OptionItem {
  value: string
  label: string
}

export interface GlobalFiltersToolbarProps {
  activePeriod: PresetPeriod
  onPresetChange: (value: PresetPeriod) => void
  selectedTopic: string
  onTopicChange: (value: string) => void
  topicOptions: OptionItem[]
  selectedModel: string
  onModelChange: (value: string) => void
  modelOptions: string[]
}

export default function GlobalFiltersToolbar(props: GlobalFiltersToolbarProps) {
  const { activePeriod, onPresetChange, selectedTopic, onTopicChange, topicOptions, selectedModel, onModelChange, modelOptions } = props
  return (
    <div className="flex items-center gap-2">
      <Select onValueChange={(value: PresetPeriod) => onPresetChange(value)} value={activePeriod}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Seleccionar período" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="24h">Últimas 24 horas</SelectItem>
          <SelectItem value="7d">Últimos 7 días</SelectItem>
          <SelectItem value="30d">Últimos 30 días</SelectItem>
          <SelectItem value="90d">Últimos 90 días</SelectItem>
          {activePeriod === 'custom' && <SelectItem value="custom" disabled>Rango Personalizado</SelectItem>}
        </SelectContent>
      </Select>

      <Select value={selectedTopic} onValueChange={(v) => onTopicChange(v)}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Tema" />
        </SelectTrigger>
        <SelectContent>
          {topicOptions.map((t) => (
            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedModel} onValueChange={onModelChange}>
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
}

"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DateRange } from "react-day-picker";
import { type PromptsByTopic, getPrompts } from "@/services/api";

interface PromptsTabProps {
  activePeriod: string;
  selectedTopic: string;
  selectedModel: string;
  dateRange: DateRange | undefined;
  openPrompt: (id: number) => void;
  openEditPrompt: (id: number, query: string, topic?: string | null, brand?: string | null) => void;
  handleDeletePrompt: (id: number) => void;
  translateTopicToSpanish: (t: string) => string;
  emojiForTopic: (t: string) => string;
}

// Tipos de análisis del índice solicitados
const ANALYSIS_TYPES = [
  "Análisis de Competencia",
  "Análisis de Marketing y Estrategia",
  "Análisis de Mercado",
  "Análisis Contextual",
  "Análisis de Oportunidades",
  "Análisis de Riesgos",
  "Análisis de Sentimiento y Reputación",
];

const PromptsTab: React.FC<PromptsTabProps> = (props) => {
  const { activePeriod, selectedTopic, selectedModel, dateRange, translateTopicToSpanish, openPrompt, openEditPrompt, handleDeletePrompt } = props;

  const [analysisType] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [groups, setGroups] = useState<PromptsByTopic[]>([]);

  useEffect(() => {
    const load = async () => {
      if (!dateRange?.from || !dateRange?.to) return;
      try {
        setLoading(true);
        const filters = { model: selectedModel, topic: selectedTopic };
        const res = await getPrompts(dateRange, filters);
        setGroups(res.topics || []);
      } catch (e) {
        console.error("No se pudieron cargar los prompts", e);
        setGroups([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [dateRange, selectedModel, selectedTopic]);

  // Filtrado por tipo de análisis: usamos el topic del prompt como categoría de negocio
  const filteredGroups = useMemo(() => {
    if (!groups?.length) return [] as PromptsByTopic[];
    // Usa el topic global si no es 'all'; si es 'all' usar el selector interno si estuviera definido
    const topic = (selectedTopic && selectedTopic !== 'all') ? selectedTopic : analysisType;
    if (!topic) return groups;
    return groups.filter((g) => (g?.topic || "").toLowerCase() === topic.toLowerCase());
  }, [groups, analysisType, selectedTopic]);

  if (loading) return <div className="p-4">Cargando prompts...</div>;

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">Periodo: {activePeriod}</div>

      {filteredGroups.length === 0 && (
        <div className="p-6 border rounded bg-gray-50 text-sm text-muted-foreground">No hay prompts para este tipo de análisis y filtros.</div>
      )}

      {filteredGroups.map((group) => (
        <Card key={group.topic} className="shadow-sm bg-white">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <span>{props.emojiForTopic(group.topic)}</span>
              <span>{translateTopicToSpanish(group.topic)}</span>
              <Badge variant="secondary" className="ml-2">{group.topic_total_mentions} menciones</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {group.prompts.map((p) => (
                <div key={p.id} className="p-3 border rounded flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{p.query}</div>
                    <div className="text-xs text-muted-foreground mt-1 flex items-center gap-3">
                      <span>Visibilidad: <strong>{p.visibility_score_individual ?? p.visibility_score}%</strong></span>
                      <span>SOV: <strong>{p.share_of_voice_individual ?? p.share_of_voice}%</strong></span>
                      <span>Ejecuciones: {p.executions}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    <Button size="sm" variant="outline" onClick={() => openPrompt(p.id)}>Detalle</Button>
                    <Button size="sm" variant="ghost" onClick={() => openEditPrompt(p.id, p.query, group.topic, undefined)}>Editar</Button>
                    <Button size="sm" variant="ghost" onClick={() => handleDeletePrompt(p.id)}>Eliminar</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default PromptsTab;

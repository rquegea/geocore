"use client";

import React, { useState, useEffect } from "react";
import { getPromptsByProjectId } from "@/services/api";
import { Prompt } from "@/types";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PromptsTabProps {
  projectId: number;
}

const PromptsTab: React.FC<PromptsTabProps> = ({ projectId }) => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        setLoading(true);
        const data = await getPromptsByProjectId(projectId);
        setPrompts(data);
      } catch (error) {
        console.error("Failed to fetch prompts:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPrompts();
  }, [projectId]);

  const groupedPrompts = prompts.reduce((acc, prompt) => {
    const category = (prompt as any).category || 'Sin Categoría';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(prompt);
    return acc;
  }, {} as Record<string, Prompt[]>);

  if (loading) {
    return <div>Cargando prompts...</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Catálogo de Análisis (Prompts)</h2>
      <Accordion type="single" collapsible className="w-full">
        {Object.entries(groupedPrompts).map(([category, promptsInCategory]) => (
          <AccordionItem value={category} key={category}>
            <AccordionTrigger className="text-lg font-semibold">{category}</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4 p-2">
                {promptsInCategory.map((prompt) => (
                  <Card key={prompt.id}>
                    <CardHeader>
                      <CardTitle className="text-md">Prompt ID: {prompt.id}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-100 dark:bg-gray-800 p-4 rounded-md">
                        {JSON.stringify((prompt as any).payload ?? prompt, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
};

export default PromptsTab;

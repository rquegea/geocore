"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  BarChart3,
  Search,
  TrendingUp,
  TrendingDown,
  Settings,
  Hash,
  Filter,
  ChevronDown,
  Zap,
  MoreHorizontal,
  Target,
} from "lucide-react"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"

const visibilityData = [
  { date: "Jun 18", value: 12.0 },
  { date: "Jun 19", value: 12.1 },
  { date: "Jun 20", value: 11.9 },
  { date: "Jun 21", value: 11.8 },
  { date: "Jun 22", value: 11.7 },
  { date: "Jun 23", value: 13.8 },
  { date: "Jun 24", value: 11.2 },
]

const competitorData = [
  { rank: 1, name: "SoFi", score: "13.5%", change: "+0.9%", positive: true, color: "bg-blue-500" },
  { rank: 2, name: "State Farm", score: "12.7%", change: "-0.2%", positive: false, color: "bg-red-500" },
  {
    rank: 3,
    name: "American Express",
    score: "12.2%",
    change: "-0.2%",
    positive: false,
    color: "bg-blue-600",
    selected: true,
  },
  { rank: 4, name: "PayPal", score: "11.7%", change: "-0.9%", positive: false, color: "bg-yellow-500" },
  { rank: 5, name: "Capital One", score: "11.3%", change: "-0.9%", positive: false, color: "bg-gray-800" },
]

const promptsData = [
  {
    topic: "Credit cards",
    tag: "Topic",
    prompts: 19,
    visibilityScore: "79.7%",
    change: "+2.2%",
    positive: true,
    rank: "#1",
    rankChange: "+1",
    shareOfVoice: "10.4%",
    shareChange: "+0.2%",
    executions: 694,
  },
  {
    topic: "Auto loans",
    tag: "Topic",
    prompts: 14,
    visibilityScore: "43%",
    change: "+2.2%",
    positive: true,
    rank: "#3",
    rankChange: "+1",
    shareOfVoice: "6.1%",
    shareChange: "+0.7%",
    executions: 695,
  },
  {
    topic: "Banking",
    tag: "Topic",
    prompts: 14,
    visibilityScore: "38.8%",
    change: "-1.2%",
    positive: false,
    rank: "#4",
    rankChange: "-",
    shareOfVoice: "6.9%",
    shareChange: "-0.4%",
    executions: 693,
  },
  {
    topic: "Mortgage",
    tag: "Topic",
    prompts: 14,
    visibilityScore: "28.8%",
    change: "+6.2%",
    positive: true,
    rank: "#2",
    rankChange: "+2",
    shareOfVoice: "5.5%",
    shareChange: "+1.5%",
    executions: 692,
  },
  {
    topic: "Wealth management / advisor",
    tag: "Topic",
    prompts: 10,
    visibilityScore: "13.4%",
    change: "-5%",
    positive: false,
    rank: "#9",
    rankChange: "+1",
    shareOfVoice: "3.2%",
    shareChange: "-0.2%",
    executions: 692,
  },
  {
    topic: "Brokerage and investment platforms",
    tag: "Topic",
    prompts: 10,
    visibilityScore: "5.7%",
    change: "+6.7%",
    positive: true,
    rank: "#24",
    rankChange: "+1",
    shareOfVoice: "1.2%",
    shareChange: "+0.2%",
    executions: 691,
  },
  {
    topic: "Personal loans",
    tag: "Topic",
    prompts: 9,
    visibilityScore: "5.1%",
    change: "-3.6%",
    positive: false,
    rank: "#22",
    rankChange: "+19",
    shareOfVoice: "1.2%",
    shareChange: "+1%",
    executions: 695,
  },
  {
    topic: "Personal lending",
    tag: "Topic",
    prompts: 9,
    visibilityScore: "3.4%",
    change: "-1.6%",
    positive: false,
    rank: "#29",
    rankChange: "+8",
    shareOfVoice: "0.5%",
    shareChange: "+0.2%",
    executions: 694,
  },
  {
    topic: "Peer to peer payments (P2P Payments)",
    tag: "Topic",
    prompts: 9,
    visibilityScore: "1.4%",
    change: "+6.8%",
    positive: true,
    rank: "#19",
    rankChange: "+8",
    shareOfVoice: "0.2%",
    shareChange: "+0.1%",
    executions: 694,
  },
  {
    topic: "Estate planning",
    tag: "Topic",
    prompts: 7,
    visibilityScore: "0.4%",
    change: "+6.1%",
    positive: true,
    rank: "#228",
    rankChange: "+52",
    shareOfVoice: "0.1%",
    shareChange: "+0.1%",
    executions: 692,
  },
  {
    topic: "Home and renters insurance",
    tag: "Topic",
    prompts: 7,
    visibilityScore: "0%",
    change: "-",
    positive: null,
    rank: "-",
    rankChange: "-",
    shareOfVoice: "0%",
    shareChange: "-",
    executions: 691,
  },
  {
    topic: "Auto Insurance",
    tag: "Topic",
    prompts: 6,
    visibilityScore: "0%",
    change: "-",
    positive: null,
    rank: "-",
    rankChange: "-",
    shareOfVoice: "0%",
    shareChange: "-",
    executions: 693,
  },
]

const sentimentData = [
  { date: "Jun 18", value: 62.1 },
  { date: "Jun 19", value: 61.8 },
  { date: "Jun 20", value: 60.5 },
  { date: "Jun 21", value: 59.2 },
  { date: "Jun 22", value: 61.8 },
  { date: "Jun 23", value: 65.4 },
  { date: "Jun 24", value: 63.9 },
]

const themesData = [
  {
    theme: "Fast Funding",
    sentiment: "Positive",
    occurrences: 38,
    change: "+5",
    positive: true,
  },
  {
    theme: "High Annual Fee",
    sentiment: "Negative",
    occurrences: 32,
    change: "-2",
    positive: false,
  },
  {
    theme: "Rewards Program",
    sentiment: "Positive",
    occurrences: 28,
    change: "+8",
    positive: true,
  },
  {
    theme: "Limited Acceptance",
    sentiment: "Negative",
    occurrences: 24,
    change: "+1",
    positive: true,
  },
  {
    theme: "Premium Benefits",
    sentiment: "Positive",
    occurrences: 22,
    change: "+3",
    positive: true,
  },
]

export function AnalyticsDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState("Last 7 Days")
  const [activeTab, setActiveTab] = useState("Visibility")
  const [activeSidebarSection, setActiveSidebarSection] = useState("Answer Engine Insights")

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 shadow-sm flex flex-col min-h-0">
        <div className="p-4 flex-1 overflow-hidden">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-white border border-gray-200 rounded flex items-center justify-center shadow-sm">
              <BarChart3 className="w-4 h-4 text-gray-700" />
            </div>
            <span className="text-black font-semibold">Analytics</span>
          </div>

          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Search"
              className="pl-10 bg-white border-gray-200 text-black placeholder:text-gray-500 shadow-sm"
            />
          </div>

          <nav className="space-y-1">
            <Button
              variant="ghost"
              className={`w-full justify-start text-black hover:text-black hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 rounded-md ${
                activeSidebarSection === "Overview" ? "bg-gray-100" : ""
              }`}
              onClick={() => setActiveSidebarSection("Overview")}
            >
              <BarChart3 className="w-4 h-4 mr-3" />
              Overview
            </Button>
            <Button
              variant="ghost"
              className={`w-full justify-start text-black hover:text-black rounded-md hover:bg-gradient-to-r hover:from-gray-200 hover:to-gray-100 ${
                activeSidebarSection === "Answer Engine Insights" ? "bg-gray-100" : ""
              }`}
              onClick={() => setActiveSidebarSection("Answer Engine Insights")}
            >
              <Zap className="w-4 h-4 mr-3" />
              Answer Engine Insights
            </Button>
            <Button
              variant="ghost"
              className={`w-full justify-start text-black hover:text-black hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 rounded-md text-left ${
                activeSidebarSection === "Estrategias y objetivos" ? "bg-gray-100" : ""
              }`}
              onClick={() => setActiveSidebarSection("Estrategias y objetivos")}
            >
              <Target className="w-4 h-4 mr-3 flex-shrink-0" />
              <span className="truncate">Estrategias y objetivos </span>
            </Button>
          </nav>
        </div>

        <div className="p-4 border-t border-gray-200 flex-shrink-0">
          <div className="space-y-2">
            <Button
              variant="ghost"
              className="w-full justify-start text-black hover:text-black hover:bg-gradient-to-r hover:from-gray-100 hover:to-gray-50 rounded-md text-sm"
            >
              <Settings className="w-4 h-4 mr-3" />
              Support
            </Button>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-xs text-white font-semibold shadow-sm flex-shrink-0">
                B
              </div>
              <span className="text-sm text-black truncate">Breno Lasserre</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-white">
        {activeSidebarSection === "Overview" ? (
          <div className="p-6">
            <div className="text-center py-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Overview</h2>
              <p className="text-gray-600">
                Esta página está en construcción. Aquí podrás agregar más datos y métricas generales.
              </p>
            </div>
          </div>
        ) : activeSidebarSection === "Estrategias y objetivos" ? (
          <div className="p-6">
            <div className="text-center py-20">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Estrategias y objetivos</h2>
              <p className="text-gray-600">
                Esta página está en construcción. Aquí podrás agregar estrategias, oportunidades y análisis de riesgos.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="border-b border-gray-200 bg-white shadow-sm">
              <div className="flex items-center justify-between p-6">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center shadow-sm">
                      <span className="text-xs text-white font-semibold">A</span>
                    </div>
                    <h1 className="text-xl font-semibold text-black">
                      {activeTab === "Prompts"
                        ? "180 prompts"
                        : activeTab === "Sentiment"
                          ? "Sentiment Analysis"
                          : "American Express"}
                    </h1>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex items-center gap-6 px-6 bg-white">
                <Button
                  variant="ghost"
                  className={
                    activeTab === "Visibility"
                      ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black"
                      : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  }
                  onClick={() => setActiveTab("Visibility")}
                >
                  Visibility
                </Button>
                <Button
                  variant="ghost"
                  className={
                    activeTab === "Sentiment"
                      ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black"
                      : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  }
                  onClick={() => setActiveTab("Sentiment")}
                >
                  Sentiment
                </Button>
                <Button
                  variant="ghost"
                  className={
                    activeTab === "Prompts"
                      ? "text-blue-600 border-b-2 border-blue-600 rounded-none hover:bg-gray-100 hover:text-black"
                      : "text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  }
                  onClick={() => setActiveTab("Prompts")}
                >
                  Prompts
                </Button>
              </div>
            </div>

            {/* Dashboard Content */}
            <div className="p-6 space-y-6 bg-white">
              {activeTab === "Sentiment" ? (
                <>
                  {/* Sentiment Page Controls */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                        <SelectTrigger className="w-40 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Last 7 Days">Last 7 Days</SelectItem>
                          <SelectItem value="Last 30 Days">Last 30 Days</SelectItem>
                          <SelectItem value="Last 90 Days">Last 90 Days</SelectItem>
                        </SelectContent>
                      </Select>
                      <span className="text-gray-600">vs</span>
                      <Select defaultValue="Previous Period">
                        <SelectTrigger className="w-40 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Previous Period">Previous Period</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select defaultValue="Daily">
                        <SelectTrigger className="w-24 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Daily">Daily</SelectItem>
                          <SelectItem value="Weekly">Weekly</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                      >
                        <Hash className="w-4 h-4 mr-2" />
                        Topics
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                      >
                        <Filter className="w-4 h-4 mr-2" />
                        Platforms
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </div>

                  {/* Sentiment Analysis Section */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card className="shadow-sm bg-white">
                      <CardHeader className="flex flex-row items-center justify-between">
                        <div>
                          <CardTitle className="text-lg font-semibold">Sentiment Analysis</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            How positively AI responses reference American Express
                          </p>
                        </div>
                        <Button variant="outline" size="sm">
                          Chart Config
                          <ChevronDown className="w-4 h-4 ml-2" />
                        </Button>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div>
                            <div className="flex items-baseline gap-2 mb-1">
                              <span className="text-sm text-muted-foreground">Positive Sentiment</span>
                            </div>
                            <div className="flex items-baseline gap-2">
                              <span className="text-3xl font-bold">63.9%</span>
                              <span className="text-green-500 flex items-center gap-1">
                                <TrendingUp className="w-4 h-4" />
                                +6.8%
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground">36.1%</p>
                          </div>

                          <div className="pt-8 border-t">
                            <div className="flex items-center gap-4 text-sm">
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                                <span>Current Period</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full border-2 border-gray-300 bg-white"></div>
                                <span>Previous Period</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="shadow-sm bg-white">
                      <CardContent className="p-6">
                        <div className="space-y-6">
                          <div>
                            <div className="text-green-600 font-medium mb-2">63.9% Positive</div>
                            <p className="text-sm text-gray-600 leading-relaxed">
                              Coverage for Accidental Damage, Valuable Purchase Protection, Value in Membership Rewards
                              Points
                            </p>
                          </div>

                          <div>
                            <div className="text-red-500 font-medium mb-2">36.1% Negative</div>
                            <p className="text-sm text-gray-600 leading-relaxed">
                              No Home or Renters Insurance, Limited Advantages Over Other Platforms, High Advisory Fee
                            </p>
                          </div>

                          <div className="space-y-2">
                            <div className="flex h-4 rounded-full overflow-hidden">
                              <div className="bg-green-500 flex-1" style={{ width: "63.9%" }}></div>
                              <div className="bg-red-500 flex-1" style={{ width: "36.1%" }}></div>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>63.9%</span>
                              <span>36.1%</span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Themes Section */}
                  <Card className="shadow-sm bg-white">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg font-semibold">Themes</CardTitle>
                          <p className="text-sm text-muted-foreground">
                            Key themes and patterns surfaced by AI when referencing American Express
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                          >
                            Filter themes
                          </Button>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mt-4">
                        <Button variant="outline" size="sm" className="bg-blue-50 text-blue-600 border-blue-200">
                          All
                        </Button>
                        <Button variant="ghost" size="sm" className="text-gray-600">
                          Positive
                        </Button>
                        <Button variant="ghost" size="sm" className="text-gray-600">
                          Negative
                        </Button>
                        <Button variant="ghost" size="sm" className="text-gray-600">
                          Trending
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full bg-white">
                          <thead className="border-b border-gray-200 bg-white">
                            <tr>
                              <th className="text-left p-4 font-medium text-gray-600">Theme</th>
                              <th className="text-left p-4 font-medium text-gray-600">Sentiment</th>
                              <th className="text-left p-4 font-medium text-gray-600">Occurrences</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white">
                            {themesData.map((item, index) => (
                              <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 bg-white">
                                <td className="p-4">
                                  <div className="font-medium text-gray-900">{item.theme}</div>
                                </td>
                                <td className="p-4">
                                  <Badge
                                    variant="secondary"
                                    className={`${
                                      item.sentiment === "Positive"
                                        ? "bg-green-100 text-green-700"
                                        : "bg-red-100 text-red-700"
                                    }`}
                                  >
                                    {item.sentiment}
                                  </Badge>
                                </td>
                                <td className="p-4">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{item.occurrences}</span>
                                    <span className={`text-sm ${item.positive ? "text-green-500" : "text-red-500"}`}>
                                      {item.change}
                                    </span>
                                    <div className="w-16 h-2 bg-gray-200 rounded-full">
                                      <div
                                        className="h-2 bg-gray-800 rounded-full"
                                        style={{ width: `${(item.occurrences / 40) * 100}%` }}
                                      ></div>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : activeTab === "Prompts" ? (
                <>
                  {/* Prompts Page Controls */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                        <SelectTrigger className="w-40 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Last 7 Days">Last 7 Days</SelectItem>
                          <SelectItem value="Last 30 Days">Last 30 Days</SelectItem>
                          <SelectItem value="Last 90 Days">Last 90 Days</SelectItem>
                        </SelectContent>
                      </Select>
                      <span className="text-gray-600">vs</span>
                      <Select defaultValue="Previous Period">
                        <SelectTrigger className="w-40 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Previous Period">Previous Period</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button variant="outline" size="sm" className="shadow-sm bg-white border-gray-200">
                        Group by: Topic
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input placeholder="Search Topics" className="pl-10 w-48 shadow-sm bg-white" />
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                      >
                        <Hash className="w-4 h-4 mr-2" />
                        Topics
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                      >
                        <Filter className="w-4 h-4 mr-2" />
                        Platforms
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </div>

                  {/* Prompts Data Table */}
                  <Card className="shadow-sm bg-white border-gray-200">
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full bg-white">
                          <thead className="border-b border-gray-200 bg-white">
                            <tr>
                              <th className="text-left p-4 font-medium text-gray-600">Topic</th>
                              <th className="text-left p-4 font-medium text-gray-600">Visibility Score</th>
                              <th className="text-left p-4 font-medium text-gray-600">Rank</th>
                              <th className="text-left p-4 font-medium text-gray-600">Share of Voice</th>
                              <th className="text-left p-4 font-medium text-gray-600">Executions</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white">
                            {promptsData.map((item, index) => (
                              <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 bg-white">
                                <td className="p-4">
                                  <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                      <span className="text-xs text-white font-semibold">
                                        {item.topic.charAt(0).toUpperCase()}
                                      </span>
                                    </div>
                                    <div>
                                      <div className="font-medium text-gray-900">{item.topic}</div>
                                      <div className="text-sm text-gray-500">
                                        <Badge variant="secondary" className="text-xs">
                                          {item.tag}
                                        </Badge>
                                        <span className="ml-2">{item.prompts} prompts</span>
                                      </div>
                                    </div>
                                  </div>
                                </td>
                                <td className="p-4">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{item.visibilityScore}</span>
                                    {item.positive !== null && (
                                      <span
                                        className={`text-sm flex items-center gap-1 ${item.positive ? "text-green-500" : "text-red-500"}`}
                                      >
                                        {item.positive ? (
                                          <TrendingUp className="w-3 h-3" />
                                        ) : (
                                          <TrendingDown className="w-3 h-3" />
                                        )}
                                        {item.change}
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td className="p-4">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{item.rank}</span>
                                    {item.rankChange !== "-" && (
                                      <span className="text-sm text-green-500">{item.rankChange}</span>
                                    )}
                                  </div>
                                </td>
                                <td className="p-4">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{item.shareOfVoice}</span>
                                    {item.shareChange !== "-" && (
                                      <span
                                        className={`text-sm ${item.shareChange.startsWith("+") ? "text-green-500" : "text-red-500"}`}
                                      >
                                        {item.shareChange}
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td className="p-4">
                                  <span className="font-medium">{item.executions}</span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <>
                  {/* Original Visibility Dashboard Content */}
                  {/* Controls */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                        <SelectTrigger className="w-40 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Last 7 Days">Last 7 Days</SelectItem>
                          <SelectItem value="Last 30 Days">Last 30 Days</SelectItem>
                          <SelectItem value="Last 90 Days">Last 90 Days</SelectItem>
                        </SelectContent>
                      </Select>
                      <span className="text-gray-600">vs</span>
                      <Select defaultValue="Previous Period">
                        <SelectTrigger className="w-40 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Previous Period">Previous Period</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select defaultValue="Daily">
                        <SelectTrigger className="w-24 shadow-sm bg-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          <SelectItem value="Daily">Daily</SelectItem>
                          <SelectItem value="Weekly">Weekly</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                      >
                        <Hash className="w-4 h-4 mr-2" />
                        Topics
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="shadow-sm bg-white border-gray-200 hover:bg-gray-100 hover:text-gray-800"
                      >
                        <Filter className="w-4 h-4 mr-2" />
                        Platforms
                        <ChevronDown className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </div>

                  {/* Visibility Score Section */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                      <Card className="shadow-sm bg-white">
                        <CardHeader className="flex flex-row items-center justify-between">
                          <div>
                            <CardTitle className="text-lg font-semibold">Visibility Score</CardTitle>
                            <p className="text-sm text-muted-foreground">
                              How often American Express appears in AI-generated answers
                            </p>
                          </div>
                          <Button variant="outline" size="sm">
                            Chart Config
                            <ChevronDown className="w-4 h-4 ml-2" />
                          </Button>
                        </CardHeader>
                        <CardContent>
                          <div className="mb-6">
                            <div className="flex items-baseline gap-2">
                              <span className="text-3xl font-bold">12.2%</span>
                              <span className="text-red-500 flex items-center gap-1">
                                <TrendingDown className="w-4 h-4" />
                                -0.2%
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground">14.3%</p>
                          </div>

                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={visibilityData}>
                                <XAxis
                                  dataKey="date"
                                  axisLine={false}
                                  tickLine={false}
                                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                                />
                                <YAxis
                                  axisLine={false}
                                  tickLine={false}
                                  tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                                  domain={["dataMin - 0.5", "dataMax + 0.5"]}
                                />
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: "hsl(var(--card))",
                                    border: "1px solid hsl(var(--border))",
                                    borderRadius: "8px",
                                  }}
                                />
                                <Line
                                  type="monotone"
                                  dataKey="value"
                                  stroke="hsl(var(--chart-2))"
                                  strokeWidth={2}
                                  dot={{ fill: "hsl(var(--chart-2))", strokeWidth: 2, r: 4 }}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>

                          <div className="flex items-center gap-4 mt-4">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full bg-chart-2"></div>
                              <span className="text-sm">Current Period</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full bg-muted"></div>
                              <span className="text-sm">Previous Period</span>
                            </div>
                            <Button variant="link" className="text-sm p-0 h-auto">
                              Compare competitors
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    <div>
                      <Card className="shadow-sm bg-white">
                        <CardHeader>
                          <CardTitle className="text-lg font-semibold">Visibility Score Rank</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="mb-4">
                            <div className="flex items-baseline gap-2">
                              <span className="text-3xl font-bold">#3</span>
                              <span className="text-green-500 flex items-center gap-1">
                                <TrendingUp className="w-4 h-4" />1
                              </span>
                            </div>
                          </div>

                          <div className="space-y-3">
                            <div className="flex items-center justify-between text-sm font-medium text-muted-foreground">
                              <span>Asset</span>
                              <span>Visibility Score</span>
                            </div>
                            {competitorData.map((competitor) => (
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
                                        Selected
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

                          <Button variant="link" className="w-full mt-4 text-sm">
                            Expand
                          </Button>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {/* Share of Voice Section */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                      <Card className="shadow-sm bg-white">
                        <CardHeader className="flex flex-row items-center justify-between">
                          <div>
                            <CardTitle className="text-lg font-semibold">Share of Voice</CardTitle>
                            <p className="text-sm text-muted-foreground">
                              Mentions of American Express in AI-generated answers in relation to competitors
                            </p>
                          </div>
                          <Button variant="outline" size="sm">
                            Chart Config
                            <ChevronDown className="w-4 h-4 ml-2" />
                          </Button>
                        </CardHeader>
                        <CardContent>
                          <div className="mb-6">
                            <div className="flex items-baseline gap-2">
                              <span className="text-3xl font-bold">2.2%</span>
                              <span className="text-green-500 flex items-center gap-1">
                                <TrendingUp className="w-4 h-4" />
                                +0.1%
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full bg-sidebar"></div>
                              <span className="text-sm">Support</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 rounded-full bg-sidebar-primary"></div>
                              <span className="text-sm">Breno Lasserre</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    <div>
                      <Card className="shadow-sm bg-white">
                        <CardHeader>
                          <CardTitle className="text-lg font-semibold">Share of Voice Rank</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="mb-4">
                            <div className="flex items-baseline gap-2">
                              <span className="text-3xl font-bold">#3</span>
                              <span className="text-green-500 flex items-center gap-1">
                                <TrendingUp className="w-4 h-4" />1
                              </span>
                            </div>
                          </div>

                          <div className="space-y-3">
                            <div className="flex items-center justify-between text-sm font-medium text-muted-foreground">
                              <span>Asset</span>
                              <span>Share of Voice</span>
                            </div>
                            {competitorData.slice(0, 3).map((competitor) => (
                              <div
                                key={competitor.rank}
                                className={`flex items-center justify-between p-2 rounded ${
                                  competitor.selected ? "bg-accent/20" : ""
                                }`}
                              >
                                <div className="flex items-center gap-3">
                                  <span className="text-sm text-muted-foreground">{competitor.rank}.</span>
                                  <div className={`w-3 h-3 rounded-full ${competitor.color}`}></div>
                                  <span className="text-sm font-medium">{competitor.name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium">
                                    {competitor.rank === 1 ? "3.1%" : competitor.rank === 2 ? "2.8%" : "2.2%"}
                                  </span>
                                  <span
                                    className={`text-xs ${competitor.rank === 1 ? "text-green-500" : "text-red-500"}`}
                                  >
                                    {competitor.rank === 1 ? "+0.2%" : competitor.rank === 2 ? "+0.1%" : "+0.1%"}
                                  </span>
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
            </div>
          </>
        )}
      </div>
    </div>
  )
}

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MetricCard } from "@/components/MetricCard";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from "recharts";
import { 
  TrendingUp, 
  Download, 
  Calendar,
  Filter,
  BarChart3,
  PieChart as PieChartIcon,
  Activity
} from "lucide-react";
import { useAppContext } from "@/contexts/AppContext";

// Mock analytics data
const performanceData = [
  { date: '2024-01-08', tickets: 12, resolved: 10, avg_time: 2.3 },
  { date: '2024-01-09', tickets: 15, resolved: 13, avg_time: 1.8 },
  { date: '2024-01-10', tickets: 18, resolved: 16, avg_time: 2.1 },
  { date: '2024-01-11', tickets: 22, resolved: 19, avg_time: 1.9 },
  { date: '2024-01-12', tickets: 16, resolved: 15, avg_time: 1.6 },
  { date: '2024-01-13', tickets: 20, resolved: 18, avg_time: 2.0 },
  { date: '2024-01-14', tickets: 25, resolved: 22, avg_time: 1.7 },
  { date: '2024-01-15', tickets: 19, resolved: 17, avg_time: 1.9 }
];

const categoryData = [
  { name: 'Integration', value: 35, color: '#3B82F6' },
  { name: 'Authentication', value: 25, color: '#10B981' },
  { name: 'Performance', value: 20, color: '#F59E0B' },
  { name: 'Security', value: 12, color: '#EF4444' },
  { name: 'Mobile', value: 8, color: '#8B5CF6' }
];

const resolutionTimeData = [
  { hour: '00:00', avg_time: 3.2 },
  { hour: '04:00', avg_time: 2.8 },
  { hour: '08:00', avg_time: 1.9 },
  { hour: '12:00', avg_time: 1.5 },
  { hour: '16:00', avg_time: 1.8 },
  { hour: '20:00', avg_time: 2.4 }
];

const agentPerformanceData = [
  { step: 'Analysis', success_rate: 0.98, avg_time: 1.2 },
  { step: 'KB Search', success_rate: 0.94, avg_time: 2.1 },
  { step: 'Similar Cases', success_rate: 0.89, avg_time: 2.8 },
  { step: 'Solution Gen', success_rate: 0.85, avg_time: 3.5 },
  { step: 'Confidence', success_rate: 0.92, avg_time: 0.8 }
];

export default function Analytics() {
  const [timeRange, setTimeRange] = useState("7d");
  const [chartType, setChartType] = useState("performance");
  
  const { metrics, metricsLoading } = useAppContext();

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.dataKey}: {entry.value}
              {entry.dataKey.includes('time') && 'h'}
              {entry.dataKey.includes('rate') && '%'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Performance insights and AI agent metrics
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Tickets"
          value={metrics?.total_tickets || 147}
          format="number"
          loading={metricsLoading}
          change={{
            value: 23,
            direction: 'up',
            period: 'last week'
          }}
          status="positive"
        />
        
        <MetricCard
          title="Auto-Resolution Rate"
          value={metrics?.success_rate || 0.87}
          format="percentage"
          loading={metricsLoading}
          change={{
            value: 0.05,
            direction: 'up',
            period: 'last week'
          }}
          status="positive"
        />
        
        <MetricCard
          title="Avg Resolution Time"
          value={metrics?.avg_resolution_time_hours || 1.9}
          format="duration"
          loading={metricsLoading}
          change={{
            value: 0.3,
            direction: 'down',
            period: 'last week'
          }}
          status="negative"
        />
        
        <MetricCard
          title="Agent Efficiency"
          value={0.94}
          format="percentage"
          loading={metricsLoading}
          change={{
            value: 0.02,
            direction: 'up',
            period: 'last week'
          }}
          status="positive"
        />
      </div>

      {/* Chart Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium">Chart Type:</span>
            </div>
            <div className="flex gap-2">
              <Button
                variant={chartType === "performance" ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType("performance")}
              >
                Performance Trends
              </Button>
              <Button
                variant={chartType === "categories" ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType("categories")}
              >
                Category Breakdown
              </Button>
              <Button
                variant={chartType === "resolution" ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType("resolution")}
              >
                Resolution Times
              </Button>
              <Button
                variant={chartType === "agent" ? "default" : "outline"}
                size="sm"
                onClick={() => setChartType("agent")}
              >
                Agent Performance
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Primary Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {chartType === "performance" && <TrendingUp className="w-5 h-5 text-blue-600" />}
              {chartType === "categories" && <PieChartIcon className="w-5 h-5 text-blue-600" />}
              {chartType === "resolution" && <Activity className="w-5 h-5 text-blue-600" />}
              {chartType === "agent" && <BarChart3 className="w-5 h-5 text-blue-600" />}
              
              {chartType === "performance" && "Daily Performance Trends"}
              {chartType === "categories" && "Ticket Categories Distribution"}
              {chartType === "resolution" && "Resolution Time by Hour"}
              {chartType === "agent" && "AI Agent Step Performance"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              {chartType === "performance" && (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tickFormatter={formatDate} />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip content={<CustomTooltip />} />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="tickets"
                      stackId="1"
                      stroke="#3B82F6"
                      fill="#3B82F6"
                      fillOpacity={0.3}
                    />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="resolved"
                      stackId="2"
                      stroke="#10B981"
                      fill="#10B981"
                      fillOpacity={0.3}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="avg_time"
                      stroke="#F59E0B"
                      strokeWidth={2}
                      dot={{ fill: '#F59E0B' }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
              
              {chartType === "categories" && (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
              
              {chartType === "resolution" && (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={resolutionTimeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="avg_time"
                      stroke="#3B82F6"
                      strokeWidth={3}
                      dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
              
              {chartType === "agent" && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={agentPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="step" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar yAxisId="left" dataKey="success_rate" fill="#10B981" />
                    <Bar yAxisId="right" dataKey="avg_time" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {categoryData.map((category, index) => (
                <div key={category.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: category.color }}
                    />
                    <span className="text-sm font-medium">{category.name}</span>
                  </div>
                  <span className="text-sm text-gray-600">{category.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resolution Efficiency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm">Auto-Resolved</span>
                <span className="font-medium">87%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Human Escalated</span>
                <span className="font-medium">8%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Failed Processing</span>
                <span className="font-medium">5%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm">Fastest Resolution</span>
                <span className="font-medium text-green-600">0.3h</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Slowest Resolution</span>
                <span className="font-medium text-red-600">4.2h</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Peak Hour</span>
                <span className="font-medium">12:00 PM</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
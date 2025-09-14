import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DatePickerWithRange } from "@/components/ui/date-picker";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { DataTable } from "@/components/DataTable";
import { 
  Download, 
  Calendar, 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  PieChart,
  FileText,
  Clock,
  Users,
  Target,
  Zap
} from "lucide-react";
import { formatDistanceToNow, format, subDays, startOfDay, endOfDay } from "date-fns";

// Mock data for reports
const performanceData = [
  { date: '2024-01-08', tickets: 12, resolved: 10, avg_time: 2.3, satisfaction: 4.2 },
  { date: '2024-01-09', tickets: 15, resolved: 13, avg_time: 1.8, satisfaction: 4.5 },
  { date: '2024-01-10', tickets: 18, resolved: 16, avg_time: 2.1, satisfaction: 4.1 },
  { date: '2024-01-11', tickets: 22, resolved: 19, avg_time: 1.9, satisfaction: 4.3 },
  { date: '2024-01-12', tickets: 16, resolved: 15, avg_time: 1.6, satisfaction: 4.6 },
  { date: '2024-01-13', tickets: 20, resolved: 18, avg_time: 2.0, satisfaction: 4.4 },
  { date: '2024-01-14', tickets: 25, resolved: 22, avg_time: 1.7, satisfaction: 4.5 },
  { date: '2024-01-15', tickets: 19, resolved: 17, avg_time: 1.9, satisfaction: 4.2 }
];

const categoryBreakdown = [
  { name: 'Integration', value: 35, tickets: 42, avg_time: 1.8 },
  { name: 'Authentication', value: 25, tickets: 30, avg_time: 1.2 },
  { name: 'Performance', value: 20, tickets: 24, avg_time: 2.1 },
  { name: 'Security', value: 12, tickets: 14, avg_time: 3.2 },
  { name: 'Mobile', value: 8, tickets: 10, avg_time: 1.5 }
];

const agentPerformance = [
  { step: 'Ticket Analysis', success_rate: 98, avg_time: 1.2, total_processed: 120 },
  { step: 'Knowledge Search', success_rate: 94, avg_time: 2.1, total_processed: 118 },
  { step: 'Similar Cases', success_rate: 89, avg_time: 2.8, total_processed: 111 },
  { step: 'Solution Generation', success_rate: 85, avg_time: 3.5, total_processed: 99 },
  { step: 'Confidence Check', success_rate: 92, avg_time: 0.8, total_processed: 84 }
];

const detailedTickets = [
  {
    id: 1,
    title: "Email integration not working",
    category: "Integration",
    priority: "high",
    status: "resolved",
    created_at: "2024-01-15T10:30:00Z",
    resolved_at: "2024-01-15T12:15:00Z",
    resolution_time: 1.75,
    agent_confidence: 0.92,
    customer_satisfaction: 5
  },
  {
    id: 2,
    title: "Password reset broken",
    category: "Authentication",
    priority: "medium",
    status: "resolved",
    created_at: "2024-01-15T09:15:00Z",
    resolved_at: "2024-01-15T10:30:00Z",
    resolution_time: 1.25,
    agent_confidence: 0.95,
    customer_satisfaction: 4
  },
  {
    id: 3,
    title: "Dashboard loading slowly",
    category: "Performance",
    priority: "low",
    status: "escalated",
    created_at: "2024-01-15T08:45:00Z",
    resolved_at: null,
    resolution_time: null,
    agent_confidence: 0.45,
    customer_satisfaction: null
  }
];

export default function Reports() {
  const [dateRange, setDateRange] = useState({
    from: subDays(new Date(), 30),
    to: new Date()
  });
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [reportType, setReportType] = useState("overview");

  const summaryStats = useMemo(() => {
    const totalTickets = performanceData.reduce((sum, day) => sum + day.tickets, 0);
    const totalResolved = performanceData.reduce((sum, day) => sum + day.resolved, 0);
    const avgResolutionTime = performanceData.reduce((sum, day) => sum + day.avg_time, 0) / performanceData.length;
    const avgSatisfaction = performanceData.reduce((sum, day) => sum + day.satisfaction, 0) / performanceData.length;
    
    return {
      totalTickets,
      totalResolved,
      resolutionRate: (totalResolved / totalTickets) * 100,
      avgResolutionTime,
      avgSatisfaction
    };
  }, []);

  const handleExportReport = (format: 'pdf' | 'csv' | 'excel') => {
    // Simulate export
    console.log(`Exporting report as ${format}`);
  };

  const ticketColumns = [
    {
      key: 'id' as const,
      label: 'ID',
      sortable: true,
      width: '80px',
      render: (value: number) => `#${value}`
    },
    {
      key: 'title' as const,
      label: 'Title',
      sortable: true,
      render: (value: string) => (
        <div className="max-w-xs truncate font-medium">{value}</div>
      )
    },
    {
      key: 'category' as const,
      label: 'Category',
      sortable: true,
      render: (value: string) => (
        <Badge variant="outline">{value}</Badge>
      )
    },
    {
      key: 'priority' as const,
      label: 'Priority',
      sortable: true,
      render: (value: string) => (
        <Badge variant={value === 'high' ? 'destructive' : value === 'medium' ? 'default' : 'secondary'}>
          {value}
        </Badge>
      )
    },
    {
      key: 'resolution_time' as const,
      label: 'Resolution Time',
      sortable: true,
      render: (value: number | null) => value ? `${value.toFixed(1)}h` : '-'
    },
    {
      key: 'agent_confidence' as const,
      label: 'AI Confidence',
      sortable: true,
      render: (value: number) => (
        <span className={`font-medium ${
          value >= 0.9 ? 'text-green-600' : 
          value >= 0.7 ? 'text-yellow-600' : 
          'text-red-600'
        }`}>
          {(value * 100).toFixed(0)}%
        </span>
      )
    },
    {
      key: 'customer_satisfaction' as const,
      label: 'Satisfaction',
      sortable: true,
      render: (value: number | null) => value ? `${value}/5` : '-'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
          <p className="text-gray-600 mt-1">
            Comprehensive insights into AI agent performance and ticket metrics
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="overview">Overview</SelectItem>
              <SelectItem value="performance">Performance</SelectItem>
              <SelectItem value="satisfaction">Satisfaction</SelectItem>
              <SelectItem value="efficiency">Efficiency</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={() => handleExportReport('pdf')}>
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <DatePickerWithRange
                date={dateRange}
                onDateChange={setDateRange}
              />
            </div>
            
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categoryBreakdown.map(cat => (
                  <SelectItem key={cat.name} value={cat.name.toLowerCase()}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Tickets</p>
                <p className="text-2xl font-bold">{summaryStats.totalTickets}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
            <div className="flex items-center mt-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600">+12% from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Resolution Rate</p>
                <p className="text-2xl font-bold">{summaryStats.resolutionRate.toFixed(1)}%</p>
              </div>
              <Target className="w-8 h-8 text-green-600" />
            </div>
            <div className="flex items-center mt-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600">+5% from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Resolution Time</p>
                <p className="text-2xl font-bold">{summaryStats.avgResolutionTime.toFixed(1)}h</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
            <div className="flex items-center mt-2 text-sm">
              <TrendingDown className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600">-15% from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Customer Satisfaction</p>
                <p className="text-2xl font-bold">{summaryStats.avgSatisfaction.toFixed(1)}/5</p>
              </div>
              <Users className="w-8 h-8 text-purple-600" />
            </div>
            <div className="flex items-center mt-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600">+0.3 from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">AI Efficiency</p>
                <p className="text-2xl font-bold">94%</p>
              </div>
              <Zap className="w-8 h-8 text-yellow-600" />
            </div>
            <div className="flex items-center mt-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600">+2% from last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Tables */}
      <Tabs defaultValue="performance" className="space-y-6">
        <TabsList>
          <TabsTrigger value="performance">Performance Trends</TabsTrigger>
          <TabsTrigger value="categories">Category Analysis</TabsTrigger>
          <TabsTrigger value="agent">AI Agent Performance</TabsTrigger>
          <TabsTrigger value="tickets">Detailed Tickets</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PerformanceChart
              data={performanceData}
              type="area"
              title="Daily Ticket Volume"
              dataKey="tickets"
              xAxisKey="date"
              color="#3B82F6"
              formatValue={(value) => `${value} tickets`}
            />
            
            <PerformanceChart
              data={performanceData}
              type="line"
              title="Resolution Time Trend"
              dataKey="avg_time"
              xAxisKey="date"
              color="#10B981"
              formatValue={(value) => `${value}h`}
            />
          </div>
          
          <PerformanceChart
            data={performanceData}
            type="bar"
            title="Customer Satisfaction Over Time"
            dataKey="satisfaction"
            xAxisKey="date"
            color="#8B5CF6"
            formatValue={(value) => `${value}/5`}
            height={250}
          />
        </TabsContent>

        <TabsContent value="categories" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PerformanceChart
              data={categoryBreakdown}
              type="pie"
              title="Tickets by Category"
              dataKey="value"
              height={300}
            />
            
            <Card>
              <CardHeader>
                <CardTitle>Category Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {categoryBreakdown.map((category) => (
                    <div key={category.name} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium">{category.name}</span>
                          <span className="text-sm text-gray-600">{category.tickets} tickets</span>
                        </div>
                        <div className="flex items-center justify-between text-sm text-gray-500">
                          <span>Avg resolution: {category.avg_time}h</span>
                          <span>{category.value}% of total</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="agent" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>AI Agent Step Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {agentPerformance.map((step, index) => (
                  <div key={step.step} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{step.step}</h4>
                      <Badge variant="outline">
                        {step.success_rate}% success
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="block font-medium">Success Rate</span>
                        <span className="text-lg font-bold text-gray-900">{step.success_rate}%</span>
                      </div>
                      <div>
                        <span className="block font-medium">Avg Time</span>
                        <span className="text-lg font-bold text-gray-900">{step.avg_time}s</span>
                      </div>
                      <div>
                        <span className="block font-medium">Processed</span>
                        <span className="text-lg font-bold text-gray-900">{step.total_processed}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tickets" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Ticket Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={detailedTickets}
                columns={ticketColumns}
                rowKey="id"
                selectable
                actions={[
                  {
                    label: 'View Details',
                    icon: FileText,
                    onClick: (ticket) => console.log('View ticket', ticket.id)
                  },
                  {
                    label: 'Export Data',
                    icon: Download,
                    onClick: (ticket) => console.log('Export ticket', ticket.id)
                  }
                ]}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
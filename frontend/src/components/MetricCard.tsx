import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
    period: string;
  };
  format: 'number' | 'percentage' | 'duration' | 'currency';
  status?: 'positive' | 'negative' | 'neutral';
  loading?: boolean;
}

const formatValue = (value: number | string, format: MetricCardProps['format']): string => {
  if (typeof value === 'string') return value;
  
  switch (format) {
    case 'percentage':
      return `${(value * 100).toFixed(1)}%`;
    case 'duration':
      if (value < 1) return `${(value * 60).toFixed(0)}m`;
      return `${value.toFixed(1)}h`;
    case 'currency':
      return `$${value.toLocaleString()}`;
    case 'number':
    default:
      return value.toLocaleString();
  }
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  format,
  status = 'neutral',
  loading = false,
}) => {
  const getTrendIcon = () => {
    if (!change) return null;
    
    switch (change.direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  const getTrendColor = () => {
    if (!change) return 'text-gray-500';
    
    // For metrics like resolution time, down is good
    const isGoodDirection = (change.direction === 'up' && status === 'positive') ||
                           (change.direction === 'down' && status === 'negative');
    
    if (change.direction === 'neutral') return 'text-gray-500';
    return isGoodDirection ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-20 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-16"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formatValue(value, format)}</div>
        {change && (
          <div className={cn("flex items-center text-xs", getTrendColor())}>
            {getTrendIcon()}
            <span className="ml-1">
              {change.direction === 'up' ? '+' : change.direction === 'down' ? '-' : ''}
              {formatValue(Math.abs(change.value), format)} from {change.period}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
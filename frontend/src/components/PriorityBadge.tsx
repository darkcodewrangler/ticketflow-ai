import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { AlertTriangle, Circle, AlertCircle, Zap } from "lucide-react";

interface PriorityBadgeProps {
  priority: 'low' | 'medium' | 'high' | 'urgent';
  showIcon?: boolean;
  className?: string;
}

const priorityConfig = {
  low: {
    label: 'Low',
    className: 'bg-gray-100 text-gray-800 border-gray-200',
    icon: Circle,
  },
  medium: {
    label: 'Medium',
    className: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: Circle,
  },
  high: {
    label: 'High',
    className: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: AlertTriangle,
  },
  urgent: {
    label: 'Urgent',
    className: 'bg-red-100 text-red-800 border-red-200',
    icon: Zap,
  },
};

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ 
  priority, 
  showIcon = false, 
  className 
}) => {
  const config = priorityConfig[priority];
  const Icon = config.icon;
  
  return (
    <Badge
      variant="outline"
      className={cn(config.className, className)}
    >
      {showIcon && <Icon className="w-3 h-3 mr-1" />}
      {config.label}
    </Badge>
  );
};
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: 'new' | 'processing' | 'resolved' | 'escalated';
  pulse?: boolean;
  className?: string;
}

const statusConfig = {
  new: {
    variant: 'secondary' as const,
    label: 'New',
    className: 'bg-blue-100 text-blue-800 border-blue-200',
  },
  processing: {
    variant: 'default' as const,
    label: 'Processing',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  },
  resolved: {
    variant: 'default' as const,
    label: 'Resolved',
    className: 'bg-green-100 text-green-800 border-green-200',
  },
  escalated: {
    variant: 'destructive' as const,
    label: 'Escalated',
    className: 'bg-red-100 text-red-800 border-red-200',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  pulse = false, 
  className 
}) => {
  const config = statusConfig[status];
  
  return (
    <Badge
      variant={config.variant}
      className={cn(
        config.className,
        pulse && status === 'processing' && 'animate-pulse',
        className
      )}
    >
      {config.label}
    </Badge>
  );
};
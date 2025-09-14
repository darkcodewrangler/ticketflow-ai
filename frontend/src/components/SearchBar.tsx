import { useState, useCallback, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command";
import { 
  Search, 
  Filter, 
  X, 
  Calendar,
  Tag,
  User,
  Hash,
  Clock
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchFilter {
  type: 'status' | 'priority' | 'category' | 'assignee' | 'date' | 'tag';
  label: string;
  value: string;
  color?: string;
}

interface SearchBarProps {
  placeholder?: string;
  onSearch: (query: string, filters: SearchFilter[]) => void;
  availableFilters?: {
    statuses?: string[];
    priorities?: string[];
    categories?: string[];
    assignees?: string[];
    tags?: string[];
  };
  className?: string;
}

const filterIcons = {
  status: Hash,
  priority: AlertTriangle,
  category: Tag,
  assignee: User,
  date: Calendar,
  tag: Tag
};

const filterColors = {
  status: 'bg-blue-100 text-blue-800 border-blue-200',
  priority: 'bg-orange-100 text-orange-800 border-orange-200',
  category: 'bg-green-100 text-green-800 border-green-200',
  assignee: 'bg-purple-100 text-purple-800 border-purple-200',
  date: 'bg-gray-100 text-gray-800 border-gray-200',
  tag: 'bg-pink-100 text-pink-800 border-pink-200'
};

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = "Search...",
  onSearch,
  availableFilters = {},
  className = ""
}) => {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilter[]>([]);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const handleQueryChange = useCallback((value: string) => {
    setQuery(value);
    onSearch(value, filters);
  }, [filters, onSearch]);

  const addFilter = useCallback((filter: SearchFilter) => {
    const newFilters = [...filters, filter];
    setFilters(newFilters);
    onSearch(query, newFilters);
    setIsFilterOpen(false);
  }, [filters, query, onSearch]);

  const removeFilter = useCallback((index: number) => {
    const newFilters = filters.filter((_, i) => i !== index);
    setFilters(newFilters);
    onSearch(query, newFilters);
  }, [filters, query, onSearch]);

  const clearAll = useCallback(() => {
    setQuery("");
    setFilters([]);
    onSearch("", []);
  }, [onSearch]);

  const filterOptions = useMemo(() => {
    const options: { type: SearchFilter['type']; label: string; values: string[] }[] = [];
    
    if (availableFilters.statuses?.length) {
      options.push({ type: 'status', label: 'Status', values: availableFilters.statuses });
    }
    if (availableFilters.priorities?.length) {
      options.push({ type: 'priority', label: 'Priority', values: availableFilters.priorities });
    }
    if (availableFilters.categories?.length) {
      options.push({ type: 'category', label: 'Category', values: availableFilters.categories });
    }
    if (availableFilters.assignees?.length) {
      options.push({ type: 'assignee', label: 'Assignee', values: availableFilters.assignees });
    }
    if (availableFilters.tags?.length) {
      options.push({ type: 'tag', label: 'Tag', values: availableFilters.tags });
    }
    
    return options;
  }, [availableFilters]);

  return (
    <div className={cn("space-y-3", className)}>
      {/* Search Input */}
      <div className="relative flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder={placeholder}
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            className="pl-10 pr-4"
          />
        </div>
        
        <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Filters
              {filters.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {filters.length}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-0" align="end">
            <Command>
              <CommandInput placeholder="Search filters..." />
              <CommandEmpty>No filters found.</CommandEmpty>
              {filterOptions.map((option) => (
                <CommandGroup key={option.type} heading={option.label}>
                  {option.values.map((value) => {
                    const Icon = filterIcons[option.type];
                    return (
                      <CommandItem
                        key={`${option.type}-${value}`}
                        onSelect={() => addFilter({
                          type: option.type,
                          label: option.label,
                          value,
                          color: filterColors[option.type]
                        })}
                        className="flex items-center gap-2"
                      >
                        <Icon className="w-4 h-4" />
                        {value}
                      </CommandItem>
                    );
                  })}
                </CommandGroup>
              ))}
            </Command>
          </PopoverContent>
        </Popover>

        {(query || filters.length > 0) && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Active Filters */}
      {filters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {filters.map((filter, index) => {
            const Icon = filterIcons[filter.type];
            return (
              <Badge
                key={index}
                variant="outline"
                className={cn("flex items-center gap-1 pr-1", filter.color)}
              >
                <Icon className="w-3 h-3" />
                <span className="text-xs">{filter.label}:</span>
                <span className="font-medium">{filter.value}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 ml-1 hover:bg-transparent"
                  onClick={() => removeFilter(index)}
                >
                  <X className="w-3 h-3" />
                </Button>
              </Badge>
            );
          })}
        </div>
      )}
    </div>
  );
};
import { Sidebar } from "./Sidebar";
import { useAppContext } from "@/contexts/AppContext";
import { cn } from "@/lib/utils";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { sidebarCollapsed } = useAppContext();

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className={cn(
        "flex-1 overflow-auto transition-all duration-300",
        sidebarCollapsed ? "ml-0" : "ml-0"
      )}>
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
};
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { Sidebar } from "./sidebar";
import { useUnreadCount } from "@/lib/use-unread-count";
import { useUiStore } from "@/store/ui-store";

interface BreadcrumbItem {
  label: string;
  onClick?: () => void;
}

interface AppShellProps {
  crumbs: BreadcrumbItem[];
  action?: ReactNode;
  children: ReactNode;
}

export function AppShell({
  crumbs,
  action,
  children,
}: AppShellProps) {
  const { pathname } = useLocation();
  const unreadCount = useUnreadCount();
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleCollapse = useUiStore((s) => s.toggleSidebar);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        pathname={pathname}
        unreadCount={unreadCount}
        collapsed={collapsed}
        onToggleCollapse={toggleCollapse}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar */}
        <div className="flex items-center justify-between gap-4 border-b border-border bg-background px-6 py-[18px]">
          <nav
            className="flex items-center gap-1.5 text-[13px] text-muted-foreground"
            aria-label="breadcrumb"
          >
            {crumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1.5">
                {i > 0 && (
                  <ChevronRight className="h-3.5 w-3.5 opacity-50" />
                )}
                {crumb.onClick && i < crumbs.length - 1 ? (
                  <button
                    type="button"
                    onClick={crumb.onClick}
                    className="cursor-pointer hover:text-foreground"
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span
                    className={
                      i === crumbs.length - 1
                        ? "font-medium text-foreground"
                        : ""
                    }
                  >
                    {crumb.label}
                  </span>
                )}
              </span>
            ))}
          </nav>
          {action}
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1280px] p-6">{children}</div>
        </div>
      </div>
    </div>
  );
}

import {
  LayoutDashboard,
  Map,
  MessageSquare,
  BookOpenText,
  PanelLeftClose,
  PanelLeft,
  Swords,
  Database,
  Target,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  icon: LucideIcon;
  label: string;
  to: string;
  badge?: number;
  match?: (pathname: string) => boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    icon: LayoutDashboard,
    label: "ダッシュボード",
    to: "/",
    match: (p) => p === "/",
  },
  {
    icon: Map,
    label: "ロードマップ",
    to: "/roadmaps",
    match: (p) => p.startsWith("/roadmaps") || p.startsWith("/sessions"),
  },
  {
    icon: Swords,
    label: "競プロ",
    to: "/algorithm-quiz",
    match: (p) => p.startsWith("/algorithm-quiz"),
  },
  {
    icon: Target,
    label: "競プロうさぎ",
    to: "/algorithm-foundations",
    match: (p) => p.startsWith("/algorithm-foundations"),
  },
  {
    icon: Database,
    label: "SQL道場",
    to: "/sql-dojo",
    match: (p) => p.startsWith("/sql-dojo"),
  },
  { icon: MessageSquare, label: "フィードバック", to: "/feedbacks" },
];

interface SidebarProps {
  pathname: string;
  unreadCount?: number;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({
  pathname,
  unreadCount = 0,
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  function isActive(item: NavItem) {
    if (item.match) return item.match(pathname);
    return pathname.startsWith(item.to);
  }

  return (
    <aside
      className={cn(
        "flex shrink-0 flex-col gap-1 border-r border-border bg-card py-4 transition-[width] duration-150",
        collapsed ? "w-16 px-2" : "w-60 px-3",
      )}
    >
      {/* Brand + Collapse toggle */}
      <div
        className={cn(
          "mb-2 flex items-center px-2 py-2",
          collapsed ? "flex-col gap-1.5" : "gap-2.5",
        )}
      >
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-indigo-500">
          <BookOpenText className="h-4 w-4 text-white" />
        </div>
        {!collapsed && (
          <span className="flex-1 text-sm font-semibold tracking-tight">
            Obsidian Quiz
          </span>
        )}
        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-[rgb(51_65_85/0.4)] hover:text-foreground"
            aria-label={collapsed ? "サイドバーを展開" : "サイドバーを折りたたむ"}
          >
            {collapsed ? (
              <PanelLeft className="h-3.5 w-3.5" />
            ) : (
              <PanelLeftClose className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>

      {/* Navigation */}
      {NAV_ITEMS.map((item) => {
        const active = isActive(item);
        const badge =
          item.to === "/feedbacks" && unreadCount > 0
            ? unreadCount
            : undefined;

        return (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            aria-label={collapsed ? item.label : undefined}
            className={cn(
              "relative flex items-center rounded-md py-2 text-[13px] transition-colors",
              collapsed
                ? "justify-center px-0"
                : "gap-2.5 px-2.5",
              active
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:bg-[rgb(51_65_85/0.4)] hover:text-foreground",
            )}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
            {badge != null && (
              <span
                className={cn(
                  "inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-primary font-mono text-[11px] font-semibold text-white",
                  collapsed ? "absolute -top-1 -right-1 px-1" : "ml-auto px-1.5",
                )}
              >
                {badge > 99 ? "99+" : badge}
              </span>
            )}
          </NavLink>
        );
      })}

    </aside>
  );
}

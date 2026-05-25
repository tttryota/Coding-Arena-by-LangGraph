import { MoreHorizontal, ArrowRightLeft, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

interface OverflowMenuProps {
  onMove: () => void;
  onDelete: () => void;
}

export function OverflowMenu({ onMove, onDelete }: OverflowMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="inline-flex h-7 w-7 cursor-pointer items-center justify-center rounded-[5px] border-0 bg-transparent text-muted-foreground transition-colors duration-[120ms] hover:bg-[rgb(51_65_85/0.6)] hover:text-foreground"
        aria-label="メニュー"
        onClick={(e) => e.stopPropagation()}
      >
        <MoreHorizontal className="h-4 w-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={4}>
        <DropdownMenuItem onClick={onMove}>
          <ArrowRightLeft className="h-3.5 w-3.5" />
          移動
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" onClick={onDelete}>
          <Trash2 className="h-3.5 w-3.5" />
          削除
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

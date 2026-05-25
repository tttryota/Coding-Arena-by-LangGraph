import { useNavigate } from "react-router-dom";
import { BookOpenText, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

const STEPS = [
  {
    num: "01",
    title: "トピックを選ぶ",
    desc: "プリセットから選ぶか、ノートから検出された候補を選択",
  },
  {
    num: "02",
    title: "ロードマップを生成",
    desc: "AIが大枠 → 中枠 → 具体 の3層構造を構築",
  },
  {
    num: "03",
    title: "クイズで理解度を測定",
    desc: "未着手 / 不十分 / 部分的 / 十分 の4段階で進捗を可視化",
  },
] as const;

export function DashboardWelcome() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto mt-6 max-w-[640px] px-8 pb-16 pt-12 text-center">
      {/* Icon mark */}
      <div
        className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-[14px] border border-[rgb(59_130_246/0.28)]"
        style={{
          background:
            "linear-gradient(135deg, rgb(59 130 246 / 0.18) 0%, rgb(99 102 241 / 0.12) 100%)",
        }}
      >
        <BookOpenText size={28} className="text-[#60a5fa]" />
      </div>

      {/* Title */}
      <h2 className="mb-2.5 text-[22px] font-semibold tracking-[-0.02em]">
        学習を始めましょう
      </h2>

      {/* Description */}
      <p className="mx-auto mb-7 max-w-[460px] text-[13px] leading-[1.7] text-muted-foreground">
        Obsidian
        のノートからロードマップを生成し、AIがクイズを出題して理解度を測定します。
        最初のロードマップを作成するところから始まります。
      </p>

      {/* CTA */}
      <div className="mb-10 flex justify-center">
        <Button onClick={() => navigate("/roadmaps")}>
          <Plus className="h-4 w-4" />
          ロードマップを作成する
        </Button>
      </div>

      {/* Step guide */}
      <div className="mx-auto grid max-w-[580px] grid-cols-3 gap-4 text-left max-[720px]:grid-cols-1">
        {STEPS.map((step) => (
          <div
            key={step.num}
            className="flex items-start gap-2.5 rounded-lg border border-border bg-card px-4 py-3.5"
          >
            <span className="mt-px shrink-0 rounded bg-[rgb(51_65_85/0.5)] px-1.5 py-0.5 font-mono text-[11px] font-semibold tracking-[0.05em] text-muted-foreground">
              {step.num}
            </span>
            <div>
              <div className="mb-0.5 text-[13px] font-semibold tracking-[-0.005em]">
                {step.title}
              </div>
              <div className="text-xs leading-[1.5] text-muted-foreground">
                {step.desc}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

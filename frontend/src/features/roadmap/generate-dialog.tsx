import { useState, useEffect, useRef, useCallback } from "react";
import {
  AlertTriangle,
  Check,
  CircleDashed,
  Plus,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TopicCandidateList } from "./topic-candidate-list";
import { useTopicCandidates, useRegisterTopic } from "./use-topic-candidates";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { GenerateResponse, GenerationJobResponse } from "@/types/api";

type DialogPhase = "input" | "generating" | "failed";

interface GenerateRoadmapDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (roadmapId: string) => void;
}

export function GenerateRoadmapDialog({
  open,
  onClose,
  onSuccess,
}: GenerateRoadmapDialogProps) {
  const qc = useQueryClient();
  const [phase, setPhase] = useState<DialogPhase>("input");
  const [selected, setSelected] = useState<string | null>(null);
  const [freeInput, setFreeInput] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [failMessage, setFailMessage] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: candidates = [] } = useTopicCandidates();
  const registerTopic = useRegisterTopic();

  const generateMutation = useMutation({
    mutationFn: async (topic: string) => {
      const res = await apiFetch("/roadmaps/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      return res.json() as Promise<GenerateResponse>;
    },
  });

  // Reset state when dialog opens/closes — key-based remount avoids useEffect setState
  const resetKey = open ? "open" : "closed";
  useEffect(() => {
    // Cleanup timers when dialog closes
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [resetKey]);

  // Elapsed timer — starts when phase becomes "generating"
  useEffect(() => {
    if (phase !== "generating") {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }
    timerRef.current = setInterval(() => setElapsed((t) => t + 1), 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  // Job polling
  useEffect(() => {
    if (phase !== "generating" || !jobId) {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }
    pollRef.current = setInterval(async () => {
      try {
        const res = await apiFetch(`/roadmaps/generate/${jobId}`);
        const data = (await res.json()) as GenerationJobResponse;
        if (data.status === "completed" && data.roadmap_id) {
          if (pollRef.current) clearInterval(pollRef.current);
          onSuccess(data.roadmap_id);
        } else if (data.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setFailMessage(data.error_message);
          setPhase("failed");
        }
      } catch {
        // polling error — continue retrying
      }
    }, 3000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [phase, jobId, onSuccess]);

  const handleGenerate = useCallback(async () => {
    if (!selected) return;
    setPhase("generating");
    try {
      const result = await generateMutation.mutateAsync(selected);
      setJobId(result.job_id);
    } catch {
      setPhase("failed");
    }
  }, [selected, generateMutation]);

  const handleAddTopic = useCallback(() => {
    const name = freeInput.trim();
    if (!name) {
      setInputError("トピック名を入力してください");
      return;
    }
    setInputError(null);
    const existing = candidates.find(
      (c) => c.name.toLowerCase() === name.toLowerCase(),
    );
    if (existing) {
      setSelected(existing.name);
      setFreeInput("");
      return;
    }
    registerTopic.mutate(name, {
      onSuccess: (result) => {
        setSelected(result.name);
        setFreeInput("");
      },
      onError: () => {
        setInputError("トピック名を入力してください");
      },
    });
  }, [freeInput, candidates, registerTopic]);

  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");

  return (
    <Dialog open={open} onOpenChange={(v) => {
      if (!v) {
        // 生成中に閉じた場合、一覧を再取得して完了したロードマップを反映する
        if (phase === "generating") {
          void qc.invalidateQueries({ queryKey: ["roadmaps"] });
        }
        onClose();
      }
    }}>
      <DialogContent className="max-w-[560px]">
        {phase === "input" && (
          <>
            <DialogHeader>
              <DialogTitle>新しいロードマップを作成</DialogTitle>
              <DialogDescription>
                学習したいトピックを選択してください。AIがObsidianのノートを参照しながら、大枠
                → 中枠 → 具体 の3層構造でロードマップを構築します。
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-0">
              <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted-foreground">
                トピックを選択
              </label>
              <TopicCandidateList
                candidates={candidates}
                selected={selected}
                onSelect={setSelected}
              />
            </div>

            {/* OR separator */}
            <div className="flex items-center gap-3 py-1">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs tracking-wider text-muted-foreground">
                または
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>

            {/* Free input */}
            <div className="flex gap-2">
              <Input
                value={freeInput}
                onChange={(e) => {
                  setFreeInput(e.target.value);
                  if (inputError) setInputError(null);
                }}
                placeholder="トピック名を入力"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTopic();
                  }
                }}
                className="flex-1"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={handleAddTopic}
                disabled={!freeInput.trim()}
              >
                <Plus className="h-3.5 w-3.5" />
                追加
              </Button>
            </div>
            {inputError && (
              <p className="text-xs text-destructive">{inputError}</p>
            )}

            {/* Selection status */}
            <div className="border-t border-border pt-3.5 text-[13px]">
              {selected ? (
                <span>
                  <span className="text-muted-foreground">選択中: </span>
                  <span className="font-semibold tracking-tight text-foreground">
                    {selected}
                  </span>
                </span>
              ) : (
                <span className="text-muted-foreground">
                  トピックを選択してください
                </span>
              )}
            </div>

            <DialogFooter>
              <Button variant="ghost" onClick={onClose}>
                キャンセル
              </Button>
              <Button
                onClick={() => void handleGenerate()}
                disabled={!selected}
              >
                <Sparkles className="h-4 w-4" />
                ロードマップを生成
              </Button>
            </DialogFooter>
          </>
        )}

        {phase === "generating" && (
          <div className="flex flex-col items-center px-1 pb-5 pt-3 text-center">
            <div className="relative mb-[18px] flex h-14 w-14 items-center justify-center">
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-primary/15 border-t-primary" />
              <Sparkles className="h-5 w-5 text-blue-400" />
            </div>
            <div className="mb-1.5 text-[15px] font-semibold tracking-tight">
              ロードマップを生成中…
            </div>
            <p className="mb-6 max-w-[380px] text-[13px] leading-relaxed text-muted-foreground">
              「{selected ?? "—"}
              」のノートを解析し、トピック構造を組み立てています。通常
              20〜40 秒かかります。
            </p>

            <div className="mb-5 flex w-full max-w-[280px] flex-col gap-2">
              {[
                { label: "ノートを読み込み", done: elapsed >= 4 },
                { label: "大枠トピックを抽出", done: elapsed >= 9 },
                { label: "中枠・具体項目を生成", done: false },
              ].map((step, i) => {
                const active =
                  (i === 0 && elapsed >= 0) ||
                  (i === 1 && elapsed >= 4) ||
                  (i === 2 && elapsed >= 9);
                return (
                  <div
                    key={step.label}
                    className={`flex items-center gap-2.5 rounded-md px-3 py-1.5 text-[13px] transition-colors ${
                      step.done
                        ? "text-score-sufficient-fg"
                        : active
                          ? "bg-primary/[0.08] text-foreground"
                          : "text-muted-foreground"
                    }`}
                  >
                    {step.done ? (
                      <Check className="h-3.5 w-3.5" />
                    ) : (
                      <CircleDashed className="h-3.5 w-3.5" />
                    )}
                    <span>{step.label}</span>
                  </div>
                );
              })}
            </div>

            <span className="font-mono text-[11px] tracking-wider text-muted-foreground">
              {minutes}:{seconds}
            </span>

            <div className="mt-4 flex w-full justify-end">
              <Button variant="ghost" onClick={onClose}>
                閉じる
              </Button>
            </div>
          </div>
        )}

        {phase === "failed" && (
          <div className="flex flex-col items-center px-1 pb-5 pt-3 text-center">
            <div className="mb-[18px] flex h-14 w-14 items-center justify-center rounded-full border border-rose-500/25 bg-rose-500/10">
              <AlertTriangle className="h-6 w-6 text-rose-400" />
            </div>
            <div className="mb-1.5 text-[15px] font-semibold tracking-tight">
              生成に失敗しました
            </div>
            <p className="mb-6 max-w-[380px] text-[13px] leading-relaxed text-muted-foreground">
              {failMessage ??
                "生成に失敗しました。もう一度お試しください"}
            </p>
            <DialogFooter>
              <Button variant="ghost" onClick={onClose}>
                閉じる
              </Button>
              <Button onClick={() => setPhase("input")}>
                <RotateCcw className="h-4 w-4" />
                やり直す
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

import { useRef } from "react";
import {
  PenLine,
  HelpCircle,
  SendHorizontal,
  ArrowUp,
  MessageCircle,
  Code2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MarkdownContent } from "@/components/common/markdown-content";
import {
  applyTextareaIndent,
  restoreTextareaSelection,
} from "@/lib/textarea-indent";
import { ChatBubble } from "./chat-bubble";
import type { SessionState, CodingDifficultyType } from "@/types/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface QuestionPhaseProps {
  sessionState: SessionState;
  isSubmitting: boolean;
  chatMessages: ChatMessage[];
  answerDraft: string;
  chatDraft: string;
  onAnswerDraftChange: (text: string) => void;
  onChatDraftChange: (text: string) => void;
  onSubmitAnswer: (text: string) => void;
  onSubmitChat: (text: string) => void;
  onExplain: () => void;
  /** Coding session: example code to display above editor */
  exampleCode?: string;
  /** Coding session: current format badge */
  currentFormat?: CodingDifficultyType;
  /** Hide explain button (coding sessions) */
  hideExplainButton?: boolean;
}

const FORMAT_LABELS: Record<CodingDifficultyType, string> = {
  rewrite: "書き換え",
  fill_blank: "穴埋め",
  bug_fix: "バグ修正",
  extend: "拡張",
  implement: "実装",
};

const FORMAT_COLORS: Record<
  CodingDifficultyType,
  { text: string; bg: string }
> = {
  rewrite: { text: "#34d399", bg: "rgb(52 211 153 / 0.12)" },
  fill_blank: { text: "#38bdf8", bg: "rgb(56 189 248 / 0.12)" },
  bug_fix: { text: "#fb923c", bg: "rgb(251 146 60 / 0.12)" },
  extend: { text: "#a78bfa", bg: "rgb(167 139 250 / 0.12)" },
  implement: { text: "#f472b6", bg: "rgb(244 114 182 / 0.12)" },
};

export function QuestionPhase({
  sessionState: s,
  isSubmitting,
  chatMessages,
  answerDraft,
  chatDraft,
  onAnswerDraftChange,
  onChatDraftChange,
  onSubmitAnswer,
  onSubmitChat,
  onExplain,
  exampleCode,
  currentFormat,
  hideExplainButton,
}: QuestionPhaseProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isCode = currentFormat != null || s.current_answer_type === "code";
  const hasDraft = answerDraft.trim().length > 0;
  const cpCount = s.confirmation_points?.length ?? 0;
  const cpIndex = (s.current_point_index ?? 0) + 1;
  const cpLabel = `確認ポイント ${cpIndex} / ${cpCount}`;
  const placeholder = isCode
    ? "コードを入力してください"
    : "回答を入力してください";

  const handleAnswerKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (
      (e.metaKey || e.ctrlKey) &&
      e.key === "Enter" &&
      hasDraft &&
      !isSubmitting
    ) {
      e.preventDefault();
      onSubmitAnswer(answerDraft);
    }
  };

  const handleCodeKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const nextState = applyTextareaIndent(
        answerDraft,
        e.currentTarget.selectionStart,
        e.currentTarget.selectionEnd,
        { outdent: e.shiftKey },
      );
      onAnswerDraftChange(nextState.value);
      restoreTextareaSelection(e.currentTarget, nextState);
      return;
    }
    handleAnswerKeyDown(e);
  };

  const handleChatKeyDown = (e: React.KeyboardEvent) => {
    if (e.nativeEvent.isComposing) return;
    if (e.key === "Enter" && chatDraft.trim() && !isSubmitting) {
      e.preventDefault();
      onSubmitChat(chatDraft);
    }
  };

  return (
    <>
      {/* Question number row */}
      <div className="mb-3 flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
        <span>問題</span>
        <span className="text-xs font-semibold text-foreground">
          {s.total_questions_asked ?? 1}
        </span>
        <span className="rounded-full bg-[rgb(51_65_85/0.5)] px-2 py-px font-sans text-[11px] normal-case tracking-normal text-muted-foreground">
          {cpLabel}
        </span>
        <span className="flex-1" />
        {currentFormat != null ? (
          <span
            className="rounded-full px-2 py-px font-sans text-[11px] normal-case tracking-normal"
            style={{
              color: FORMAT_COLORS[currentFormat].text,
              background: FORMAT_COLORS[currentFormat].bg,
            }}
          >
            {FORMAT_LABELS[currentFormat]}
          </span>
        ) : (
          <span className="normal-case tracking-normal text-muted-foreground">
            {isCode ? "コード回答" : "文章回答"}
          </span>
        )}
      </div>

      {/* Question card */}
      <div className="rounded-md border border-border border-l-[3px] border-l-primary bg-[rgb(15_23_42/0.6)] px-5 py-[18px] text-[15px] leading-relaxed tracking-tight text-foreground">
        <MarkdownContent content={s.current_question_text ?? ""} />
      </div>

      {/* Example code (coding sessions) */}
      {exampleCode && (
        <div className="mt-4">
          <div className="mb-1.5 flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            <Code2 className="h-3 w-3" />
            <span>サンプルコード</span>
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-md border border-[rgb(51_65_85/0.5)] bg-[#0b1220] px-3.5 py-3 font-mono text-[12.5px] leading-relaxed text-[#e2e8f0]">
            {exampleCode}
          </pre>
        </div>
      )}

      {/* Answer block */}
      <div className="mt-5">
        <div className="mb-2 flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <PenLine className="h-3 w-3" />
          <span>回答</span>
        </div>

        {isCode ? (
          <div className="overflow-hidden rounded-md border border-[rgb(51_65_85/0.7)] bg-[#0b1220]">
            <div className="flex items-center justify-between border-b border-[rgb(51_65_85/0.5)] bg-[rgb(2_6_23/0.6)] px-3 py-2 font-mono text-[11px] text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <span className="inline-flex gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#fb7185]" />
                  <span className="h-2 w-2 rounded-full bg-[#fbbf24]" />
                  <span className="h-2 w-2 rounded-full bg-[#34d399]" />
                </span>
              </span>
              <span>answer.ts &middot; TypeScript</span>
              <span className="text-[rgb(100_116_139/0.7)]">
                {answerDraft.length} chars
              </span>
            </div>
            <textarea
              ref={textareaRef}
              className="block w-full resize-y bg-transparent px-4 py-3.5 font-mono text-[13px] leading-relaxed text-[#e2e8f0] outline-none [min-height:320px] [tab-size:2] placeholder:text-[rgb(100_116_139/0.6)]"
              value={answerDraft}
              onChange={(e) => onAnswerDraftChange(e.target.value)}
              onKeyDown={handleCodeKeyDown}
              placeholder={placeholder}
              spellCheck={false}
              disabled={isSubmitting}
            />
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            className="w-full resize-y rounded-md border border-input bg-background px-4 py-3.5 font-sans text-sm leading-relaxed text-foreground outline-none transition-[border-color,box-shadow] duration-150 [min-height:152px] placeholder:text-[rgb(148_163_184/0.5)] focus:border-ring focus:shadow-[0_0_0_2px_rgb(59_130_246/0.25)]"
            value={answerDraft}
            onChange={(e) => onAnswerDraftChange(e.target.value)}
            onKeyDown={handleAnswerKeyDown}
            placeholder={placeholder}
            disabled={isSubmitting}
            rows={6}
          />
        )}

        {/* Action row */}
        <div className="mt-3.5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <kbd className="inline-flex items-center rounded border border-input bg-[rgb(15_23_42/0.6)] px-[5px] py-px font-mono text-[10px] text-muted-foreground">
                ⌘
              </kbd>
              <kbd className="inline-flex items-center rounded border border-input bg-[rgb(15_23_42/0.6)] px-[5px] py-px font-mono text-[10px] text-muted-foreground">
                ↵
              </kbd>
              <span>で送信</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            {!hideExplainButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onExplain}
                disabled={isSubmitting}
              >
                <HelpCircle className="h-3.5 w-3.5" />
                解説して
              </Button>
            )}
            <button
              type="button"
              className="inline-flex h-8 items-center gap-[5px] rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground transition-colors duration-150 hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => onSubmitAnswer(answerDraft)}
              disabled={!hasDraft || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="inline-block h-3.5 w-3.5 animate-[qs-spin_0.7s_linear_infinite] rounded-full border-2 border-[rgb(255_255_255/0.3)] border-t-white" />
                  評価中…
                </>
              ) : (
                <>
                  <SendHorizontal className="h-3.5 w-3.5" />
                  回答する
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Chat dock */}
      <div className="mt-5 border-t border-dashed border-border pt-[18px]">
        {chatMessages
          .filter((m) => m.role === "assistant")
          .map((m, i) => (
            <ChatBubble key={i} text={m.content} />
          ))}
        <div className="flex items-stretch gap-2">
          <input
            className="h-[38px] flex-1 rounded-md border border-input bg-background px-3.5 font-sans text-[13px] text-foreground outline-none transition-[border-color] duration-150 placeholder:text-[rgb(148_163_184/0.55)] focus:border-ring disabled:cursor-not-allowed disabled:opacity-50"
            value={chatDraft}
            onChange={(e) => onChatDraftChange(e.target.value)}
            onKeyDown={handleChatKeyDown}
            placeholder="質問や解説リクエストを入力..."
            disabled={isSubmitting}
          />
          <button
            type="button"
            className="inline-flex h-[38px] w-[38px] items-center justify-center rounded-md border border-input bg-transparent text-muted-foreground transition-[background,color,border-color] duration-150 hover:bg-[rgb(51_65_85/0.5)] hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
            disabled={!chatDraft.trim() || isSubmitting}
            aria-label="送信"
            onClick={() => {
              if (chatDraft.trim() && !isSubmitting) onSubmitChat(chatDraft);
            }}
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <MessageCircle className="h-[11px] w-[11px]" />
          <span>
            質問・追加情報のリクエストはここから。進行は中断されません。
          </span>
        </div>
      </div>
    </>
  );
}

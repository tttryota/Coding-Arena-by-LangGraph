import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";

interface LecturePhaseProps {
  lectureContent: string;
  chatMessages: Array<{ role: "user" | "assistant"; content: string }>;
  onSendChat: (message: string) => void;
  onStartPractice: () => void;
  isSubmitting: boolean;
}

export function LecturePhase({
  lectureContent,
  chatMessages,
  onSendChat,
  onStartPractice,
  isSubmitting,
}: LecturePhaseProps) {
  const [chatDraft, setChatDraft] = useState("");

  const handleSend = () => {
    if (!chatDraft.trim()) return;
    onSendChat(chatDraft);
    setChatDraft("");
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>座学</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
            {lectureContent}
          </div>
        </CardContent>
      </Card>

      {chatMessages.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">チャット</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`rounded-lg p-3 text-sm ${
                  msg.role === "user"
                    ? "ml-8 bg-primary/10"
                    : "mr-8 bg-muted"
                }`}
              >
                {msg.content}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2">
        <Textarea
          value={chatDraft}
          onChange={(e) => setChatDraft(e.target.value)}
          placeholder="質問があれば入力してください"
          className="min-h-[60px]"
        />
        <Button
          onClick={handleSend}
          disabled={!chatDraft.trim() || isSubmitting}
          variant="outline"
          className="shrink-0"
        >
          送信
        </Button>
      </div>

      <Button
        onClick={onStartPractice}
        disabled={isSubmitting}
        className="w-full"
        size="lg"
      >
        演習を始める
      </Button>
    </div>
  );
}

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import type { Components } from "react-markdown";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

const components: Components = {
  pre({ children }) {
    return (
      <pre className="my-3 overflow-x-auto whitespace-pre-wrap rounded-md border border-[rgb(51_65_85/0.5)] bg-[#0b1220] px-3.5 py-3 font-mono text-[12.5px] leading-relaxed text-[#e2e8f0]">
        {children}
      </pre>
    );
  },
  code({ className, children }) {
    // インラインコード用スタイル。pre > code の場合は CSS でリセットされる。
    // className を保持して言語情報 (language-*) を維持する。
    const classes = [
      "md-code rounded bg-[rgb(51_65_85/0.5)] px-1.5 py-0.5 font-mono text-[13px] text-[#e2e8f0]",
      className,
    ]
      .filter(Boolean)
      .join(" ");
    return <code className={classes}>{children}</code>;
  },
};

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div className={`markdown-content ${className ?? ""}`.trim()}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

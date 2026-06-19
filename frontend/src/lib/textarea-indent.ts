export interface TextareaIndentState {
  value: string;
  selectionStart: number;
  selectionEnd: number;
}

interface ApplyIndentOptions {
  indent?: string;
  outdent?: boolean;
}

function getLineStart(value: string, index: number) {
  return value.lastIndexOf("\n", Math.max(index - 1, 0)) + 1;
}

function getBlockEnd(value: string, start: number, end: number) {
  const endIndexForLine =
    end > start && value[end - 1] === "\n" ? end - 1 : end;
  const lineEnd = value.indexOf("\n", endIndexForLine);
  return lineEnd === -1 ? value.length : lineEnd;
}

function stripOneIndent(line: string, indent: string) {
  if (line.startsWith(indent)) {
    return { line: line.slice(indent.length), removed: indent.length };
  }
  if (line.startsWith("\t")) {
    return { line: line.slice(1), removed: 1 };
  }
  const leadingSpaces = line.match(/^ +/)?.[0].length ?? 0;
  const removed = Math.min(leadingSpaces, indent.length);
  return { line: line.slice(removed), removed };
}

export function applyTextareaIndent(
  value: string,
  selectionStart: number,
  selectionEnd: number,
  options?: ApplyIndentOptions,
): TextareaIndentState {
  const indent = options?.indent ?? "  ";
  const outdent = options?.outdent ?? false;

  if (!outdent && selectionStart === selectionEnd) {
    return {
      value:
        value.slice(0, selectionStart) + indent + value.slice(selectionEnd),
      selectionStart: selectionStart + indent.length,
      selectionEnd: selectionEnd + indent.length,
    };
  }

  const blockStart = getLineStart(value, selectionStart);
  const blockEnd = getBlockEnd(value, selectionStart, selectionEnd);
  const lines = value.slice(blockStart, blockEnd).split("\n");

  if (outdent) {
    const removedPerLine: number[] = [];
    const updatedLines = lines.map((line) => {
      const next = stripOneIndent(line, indent);
      removedPerLine.push(next.removed);
      return next.line;
    });
    const removedTotal = removedPerLine.reduce(
      (sum, current) => sum + current,
      0,
    );
    return {
      value:
        value.slice(0, blockStart) +
        updatedLines.join("\n") +
        value.slice(blockEnd),
      selectionStart: Math.max(blockStart, selectionStart - removedPerLine[0]),
      selectionEnd: Math.max(blockStart, selectionEnd - removedTotal),
    };
  }

  return {
    value:
      value.slice(0, blockStart) +
      lines.map((line) => `${indent}${line}`).join("\n") +
      value.slice(blockEnd),
    selectionStart: selectionStart + indent.length,
    selectionEnd: selectionEnd + indent.length * lines.length,
  };
}

export function restoreTextareaSelection(
  textarea: HTMLTextAreaElement,
  nextState: TextareaIndentState,
) {
  window.setTimeout(() => {
    textarea.setSelectionRange(
      nextState.selectionStart,
      nextState.selectionEnd,
    );
  }, 0);
}

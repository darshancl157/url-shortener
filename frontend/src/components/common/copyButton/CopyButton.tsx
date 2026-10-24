import { useState } from "react";
import Button from "../button/Button";

const CopyButton: React.FC<{ text: string; compact?: boolean }> = ({
  text,
  compact = false,
}) => {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Button
      type="button"
      className={compact ? "button-compact" : undefined}
      onClick={copy}
    >
      {copied ? "Copied" : "Copy"}
    </Button>
  );
};

export default CopyButton;

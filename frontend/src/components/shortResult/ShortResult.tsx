import { useState } from "react";
import "./ShortResult.css";
import Button from "../common/button/Button";

const ShortResult: React.FC<{ shortUrl: string }> = ({ shortUrl }) => {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(shortUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="result" role="status">
      <a
        href={shortUrl}
        target="_blank"
        rel="noreferrer"
        className="result-link"
      >
        {shortUrl}
      </a>
      <Button type="button" onClick={copy}>
        {copied ? "Copied" : "Copy"}
      </Button>
    </div>
  );
};

export default ShortResult;

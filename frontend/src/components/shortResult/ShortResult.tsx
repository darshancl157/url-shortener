import CopyButton from "../common/copyButton/CopyButton";
import "./ShortResult.css";

const ShortResult: React.FC<{ shortUrl: string }> = ({ shortUrl }) => (
  <div className="result" role="status">
    <a href={shortUrl} target="_blank" rel="noreferrer" className="result-link">
      {shortUrl}
    </a>
    <CopyButton text={shortUrl} />
  </div>
);

export default ShortResult;

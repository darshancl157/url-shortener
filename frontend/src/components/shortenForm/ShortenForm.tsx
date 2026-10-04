import { useState } from "react";
import "./ShortenForm.css";
import Button from "../common/button/Button";

const ShortenForm: React.FC<{
  onSubmit: (url: string) => void;
  loading: boolean;
  error: string | null;
}> = ({ onSubmit, loading, error }) => {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit(value);
  }

  return (
    <form onSubmit={handleSubmit} className="form" noValidate>
      <div className="row">
        <input
          type="text"
          inputMode="url"
          className="input"
          placeholder="https://example.com/a/very/long/link"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          aria-label="Long URL"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "shorten-error" : undefined}
          autoFocus
        />
        <Button type="submit" disabled={loading}>
          {loading ? "Shortening…" : "Shorten"}
        </Button>
      </div>
      {error && (
        <p id="shorten-error" className="error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
};

export default ShortenForm;

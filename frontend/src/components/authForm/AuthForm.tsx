import { useState } from "react";
import Button from "../common/button/Button";
import { login, register, type User } from "../../services/auth";
import "./AuthForm.css";

type Mode = "login" | "register";

const AuthForm: React.FC<{ onAuthenticated: (user: User) => void }> = ({
  onAuthenticated,
}) => {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "register") await register(email, password);
      onAuthenticated(await login(email, password));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function switchMode() {
    setMode(mode === "login" ? "register" : "login");
    setError(null);
  }

  return (
    <form onSubmit={handleSubmit} className="auth" noValidate>
      <h2 className="auth-title">
        {mode === "login" ? "Log in" : "Create an account"}
      </h2>
      <label className="auth-field">
        Email
        <input
          type="email"
          className="auth-input"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label className="auth-field">
        Password
        <input
          type="password"
          className="auth-input"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      <Button type="submit" disabled={loading}>
        {loading ? "Please wait…" : mode === "login" ? "Log in" : "Sign up"}
      </Button>
      <button type="button" className="auth-switch" onClick={switchMode}>
        {mode === "login" ? "No account? Sign up" : "Have an account? Log in"}
      </button>
    </form>
  );
};

export default AuthForm;

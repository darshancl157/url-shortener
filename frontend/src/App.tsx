import React, { useEffect, useState } from "react";
import "./App.css";
import Container from "./components/common/container/Container";
import Header from "./components/layouts/header/Header";
import Footer from "./components/layouts/footer/Footer";
import AuthForm from "./components/authForm/AuthForm";
import ShortenForm from "./components/shortenForm/ShortenForm";
import ShortResult from "./components/shortResult/ShortResult";
import { logout, restoreSession, type User } from "./services/auth";
import { setSessionExpiredHandler } from "./services/http";
import { shortenUrl } from "./services/urls";

const App: React.FC = () => {
  // undefined = still checking for an existing session; null = logged out
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shortUrl, setShortUrl] = useState<string | null>(null);

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null));
    restoreSession()
      .then(setUser)
      .catch(() => setUser(null));
    return () => setSessionExpiredHandler(null);
  }, []);

  async function handleSubmit(url: string) {
    setLoading(true);
    setError(null);
    setShortUrl(null);
    try {
      const result = await shortenUrl(url);
      setShortUrl(result.short_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    await logout();
    setUser(null);
    setShortUrl(null);
    setError(null);
  }

  let content: React.ReactNode;
  if (user === undefined) {
    content = <p className="app-status">Loading…</p>;
  } else if (user === null) {
    content = <AuthForm onAuthenticated={setUser} />;
  } else {
    content = (
      <>
        <div className="app-session">
          <span>Signed in as {user.email}</span>
          <button type="button" className="app-logout" onClick={handleLogout}>
            Log out
          </button>
        </div>
        <ShortenForm onSubmit={handleSubmit} loading={loading} error={error} />
        {shortUrl && <ShortResult shortUrl={shortUrl} />}
      </>
    );
  }

  return (
    <main className="main">
      <Header />
      <Container>
        <div className="app">
          <div className="app-content">{content}</div>
        </div>
      </Container>
      <Footer />
    </main>
  );
};

export default App;

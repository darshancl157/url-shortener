import React, { useState } from "react";
import "./App.css";
import Container from "./components/common/container/Container";
import Header from "./components/layouts/header/Header";
import Footer from "./components/layouts/footer/Footer";
import ShortenForm from "./components/shortenForm/ShortenForm";
import ShortResult from "./components/shortResult/ShortResult";
import { shortenUrl } from "./services/urls";

const App: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shortUrl, setShortUrl] = useState<string | null>(null);

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

  return (
    <main className="main">
      <Header />
      <Container>
        <div className="app">
          <div className="app-content">
            <ShortenForm
              onSubmit={handleSubmit}
              loading={loading}
              error={error}
            />
            {shortUrl && <ShortResult shortUrl={shortUrl} />}
          </div>
        </div>
      </Container>
      <Footer />
    </main>
  );
};

export default App;

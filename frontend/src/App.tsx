import React from "react";
import "./App.css";
import Container from "./components/common/container/Container";
import Header from "./components/layouts/header/Header";
import Footer from "./components/layouts/footer/Footer";
import ShortenForm from "./components/shortenForm/ShortenForm";

const App: React.FC = () => {
  return (
    <main className="main">
      <Header />
      <Container>
        <div className="app">
          <ShortenForm
            onSubmit={(url) => console.log("Shorten URL:", url)}
            loading={false}
            error={null}
          />
        </div>
      </Container>
      <Footer />
    </main>
  );
};

export default App;

import React from "react";
import Container from "../../common/container/Container";
import "./Footer.css";

const Footer: React.FC = () => {
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <Container>
        <div className="footer__bottom">
          <p>© {year} URL Shortener. All rights reserved.</p>
        </div>
      </Container>
    </footer>
  );
};

export default Footer;

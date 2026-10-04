import React, { useEffect, useState } from "react";
import Container from "../../common/container/Container";
import "./Header.css";

const MOBILE_BREAKPOINT = 768;

const Header: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = () => setIsOpen(false);

  // Close on Escape, and auto-close when resizing up to desktop
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMenu();
    };
    const onResize = () => {
      if (window.innerWidth >= MOBILE_BREAKPOINT) closeMenu();
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  // Lock page scroll while the mobile menu is open
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  return (
    <header className="header">
      <Container>
        <div className="header__inner">
          <a href="/" className="header__logo" onClick={closeMenu}>
            Project 1 : URL Shortener
          </a>
        </div>
      </Container>

      {/* Backdrop: click outside to close */}
      <div
        className={`header__backdrop ${isOpen ? "is-visible" : ""}`}
        onClick={closeMenu}
        aria-hidden="true"
      />
    </header>
  );
};

export default Header;

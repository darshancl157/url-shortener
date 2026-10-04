import React from "react";
import "./Container.css";

const Container: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div className="container">{children}</div>;
};

export default Container;

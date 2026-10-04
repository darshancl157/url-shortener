import "./Button.css";

const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({
  className,
  ...props
}) => (
  <button className={className ? `button ${className}` : "button"} {...props} />
);

export default Button;

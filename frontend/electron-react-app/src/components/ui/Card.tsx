import { ReactNode } from "react";

import styles from "./Card.module.css";

type CardProps = {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  variant?: "default" | "muted" | "highlight";
  className?: string;
};

export const Card = ({
  title,
  subtitle,
  actions,
  children,
  variant = "default",
  className = "",
}: CardProps) => {
  return (
    <section className={`${styles.card} ${styles[variant]} ${className}`}>
      {(title || actions) && (
        <header className={styles.header}>
          <div>
            {title && <h3 className={styles.title}>{title}</h3>}
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
          {actions && <div className={styles.actions}>{actions}</div>}
        </header>
      )}
      <div className={styles.content}>{children}</div>
    </section>
  );
};

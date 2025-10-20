import { ReactNode } from "react";

import { ShellHeader } from "./ShellHeader";
import { ShellNavigation } from "./ShellNavigation";
import { ShellStatusBar } from "./ShellStatusBar";

import styles from "./MainLayout.module.css";

type Props = {
  children: ReactNode;
};

export const MainLayout = ({ children }: Props) => {
  return (
    <div className={styles.layout}>
      <ShellHeader />
      <div className={styles.contentArea}>
        <ShellNavigation />
        <main className={styles.main}>{children}</main>
      </div>
      <ShellStatusBar />
    </div>
  );
};

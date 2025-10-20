import { NavLink } from "react-router-dom";
import {
  FileText,
  BarChart3,
  Gauge,
  TrendingUp,
  Users,
  Sparkles,
  Settings,
} from "lucide-react";

import styles from "./ShellNavigation.module.css";

const links = [
  { path: "/", label: "Analysis", icon: "A", IconComponent: FileText },
  {
    path: "/dashboard",
    label: "Dashboard",
    icon: "D",
    IconComponent: BarChart3,
  },
  {
    path: "/mission-control",
    label: "Mission Control",
    icon: "MC",
    IconComponent: Gauge,
  },
  {
    path: "/analytics/advanced",
    label: "Advanced Analytics",
    icon: "📊",
    IconComponent: TrendingUp,
  },
  {
    path: "/analytics/meta",
    label: "Team Analytics",
    icon: "👥",
    IconComponent: Users,
  },
  {
    path: "/habits/growth-journey",
    label: "Growth Journey",
    icon: "🌟",
    IconComponent: Sparkles,
  },
  { path: "/settings", label: "Settings", icon: "S", IconComponent: Settings },
];

export const ShellNavigation = () => {
  return (
    <nav className={styles.nav}>
      {links.map((link) => {
        const Icon = link.IconComponent;
        return (
          <NavLink
            key={link.path}
            to={link.path}
            end={link.path === "/"}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ""}`
            }
          >
            <span className={styles.icon}>
              {Icon ? <Icon size={20} /> : link.icon}
            </span>
            <span>{link.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
};

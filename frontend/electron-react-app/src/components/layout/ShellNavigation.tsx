import { NavLink } from 'react-router-dom';

import styles from './ShellNavigation.module.css';

const links = [
  { path: '/', label: 'Analysis', icon: 'A' },
  { path: '/dashboard', label: 'Dashboard', icon: 'D' },
  { path: '/mission-control', label: 'Mission Control', icon: 'MC' },
  { path: '/analytics/advanced', label: 'Advanced Analytics', icon: '📊' },
  { path: '/analytics/meta', label: 'Team Analytics', icon: '👥' },
  { path: '/habits/growth-journey', label: 'Growth Journey', icon: '🌟' },
  { path: '/settings', label: 'Settings', icon: 'S' },
];

export const ShellNavigation = () => {
  return (
    <nav className={styles.nav}>
      {links.map((link) => (
        <NavLink
          key={link.path}
          to={link.path}
          end={link.path === '/'}
          className={({ isActive }) =>
            `${styles.link} ${isActive ? styles.active : ''}`
          }
        >
          <span className={styles.icon}>{link.icon}</span>
          <span>{link.label}</span>
        </NavLink>
      ))}
    </nav>
  );
};

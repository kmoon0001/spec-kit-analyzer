import { NavLink } from 'react-router-dom';

import styles from './ShellNavigation.module.css';

const links = [
  { path: '/', label: 'Analysis', icon: 'A' },
  { path: '/dashboard', label: 'Dashboard', icon: 'D' },
  { path: '/mission-control', label: 'Mission Control', icon: 'MC' },
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

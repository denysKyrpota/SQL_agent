/**
 * App Header - Minimal header with user menu
 */

import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import './AppHeader.module.css';

const AppHeader: React.FC = () => {
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const handleLogout = async () => {
    await logout();
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  return (
    <header className="app-header">
      <div className="app-header-container">
        {/* Logo */}
        <Link to="/" className="app-header-logo">
          SQL AI
        </Link>

        {/* User Menu */}
        <div className="app-header-actions" ref={menuRef}>
          <button
            className="user-menu-trigger"
            onClick={() => setShowUserMenu(!showUserMenu)}
            aria-label="User menu"
            aria-expanded={showUserMenu}
          >
            {user?.username}
          </button>

          {showUserMenu && (
            <div className="user-menu-dropdown">
              <Link to="/history" className="user-menu-item" onClick={() => setShowUserMenu(false)}>
                Query History
              </Link>
              <div className="user-menu-divider" />
              <button className="user-menu-item" onClick={handleLogout}>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default AppHeader;

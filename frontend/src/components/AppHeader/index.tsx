/**
 * App Header - Navigation header with user menu
 */

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/Button';
import './AppHeader.module.css';

const AppHeader: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <header className="app-header">
      <div className="app-header-container">
        {/* Logo / Brand */}
        <div className="app-header-brand">
          <Link to="/" className="brand-link">
            <span className="brand-icon">🤖</span>
            <span className="brand-name">SQL AI Agent</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="app-header-nav">
          <Link
            to="/"
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
          >
            New Query
          </Link>
          <Link
            to="/history"
            className={`nav-link ${isActive('/history') ? 'active' : ''}`}
          >
            History
          </Link>
        </nav>

        {/* User Menu */}
        <div className="app-header-user">
          <button
            className="user-button"
            onClick={() => setShowUserMenu(!showUserMenu)}
            aria-label="User menu"
            aria-expanded={showUserMenu}
          >
            <span className="user-icon">👤</span>
            <span className="user-name">{user?.username}</span>
            <span className="user-arrow">▼</span>
          </button>

          {showUserMenu && (
            <div className="user-menu">
              <div className="user-menu-header">
                <div className="user-menu-name">{user?.username}</div>
                <div className="user-menu-role">
                  {user?.role === 'admin' ? '👑 Admin' : '👤 User'}
                </div>
              </div>
              <div className="user-menu-divider" />
              <button
                className="user-menu-item"
                onClick={handleLogout}
              >
                🚪 Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default AppHeader;

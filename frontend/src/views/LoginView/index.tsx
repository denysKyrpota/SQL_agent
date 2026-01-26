/**
 * Login View - User authentication page
 */

import React, { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/Button';
import styles from './LoginView.module.css';

const LoginView: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticating } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!username.trim()) {
      setError('Username is required');
      return;
    }

    if (!password.trim()) {
      setError('Password is required');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      await login(username.trim(), password);
      // Redirect to main app after successful login
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className={styles.loginView}>
      <div className={styles.loginContainer}>
        <div className={styles.logoSection}>
          <div className={styles.logo}>
            <div className={styles.logoPlaceholder}>
              <span className={styles.logoText}>SQL</span>
              <span className={styles.logoSubtext}>AI Agent</span>
            </div>
          </div>
        </div>

        <h2 className={styles.signInTitle}>Please Sign In</h2>

        <form className={styles.loginForm} onSubmit={handleSubmit}>
          {error && (
            <div className={styles.loginError} role="alert">
              {error}
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.formLabel}>Email</label>
            <input
              id="username"
              type="text"
              className={styles.formInput}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isAuthenticating}
              autoComplete="username"
              autoFocus
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.formLabel}>Password</label>
            <div className={styles.passwordInputWrapper}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className={styles.formInput}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isAuthenticating}
                autoComplete="current-password"
              />
              <button
                type="button"
                className={styles.passwordToggle}
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className={styles.forgotPasswordWrapper}>
            <a href="#" className={styles.forgotPassword}>Forgot password?</a>
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={isAuthenticating}
            fullWidth
          >
            {isAuthenticating ? 'Signing in...' : 'Log in'}
          </Button>
        </form>

        <div className={styles.loginFooter}>
          <p className={styles.demoCredentials}>
            <strong>Note:</strong> Use credentials created during setup (<code>make db-init</code>)
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginView;

/**
 * Login View - User authentication page
 */

import React, { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/Button';
import TextArea from '@/components/TextArea';
import './LoginView.module.css';

const LoginView: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticating } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

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
    <div className="login-view">
      <div className="login-container">
        <div className="login-header">
          <h1>SQL AI Agent</h1>
          <p>Sign in to query your database</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isAuthenticating}
              autoComplete="username"
              autoFocus
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isAuthenticating}
              autoComplete="current-password"
              minLength={8}
              required
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={isAuthenticating}
            fullWidth
          >
            {isAuthenticating ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <div className="login-footer">
          <p className="demo-credentials">
            <strong>Demo credentials:</strong><br />
            Username: <code>admin</code> / Password: <code>admin123</code><br />
            Username: <code>testuser</code> / Password: <code>testpass123</code>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginView;

/**
 * ProtectedRoute - Wrapper component for authenticated routes
 */

import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface ProtectedRouteProps {
  /** Child components to render if authenticated */
  children: ReactNode;
  /** Whether admin role is required (default: false) */
  requireAdmin?: boolean;
}

/**
 * ProtectedRoute Component
 *
 * Renders children only if user is authenticated. Redirects to /login otherwise.
 * Optionally requires admin role.
 *
 * @example
 * ```tsx
 * <Route path="/dashboard" element={
 *   <ProtectedRoute>
 *     <Dashboard />
 *   </ProtectedRoute>
 * } />
 * ```
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAdmin = false,
}) => {
  const { user, isLoading } = useAuth();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          fontSize: '1.125rem',
          color: '#718096',
        }}
      >
        Loading...
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Admin required but user is not admin
  if (requireAdmin && user.role !== 'admin') {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          flexDirection: 'column',
          gap: '1rem',
        }}
      >
        <h1 style={{ fontSize: '1.5rem', color: '#2d3748' }}>Access Denied</h1>
        <p style={{ color: '#718096' }}>
          You don't have permission to access this page.
        </p>
      </div>
    );
  }

  // Authenticated and authorized
  return <>{children}</>;
};

export default ProtectedRoute;

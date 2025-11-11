/**
 * useAuth Hook - Access authentication context
 */

import { useContext } from 'react';
import { AuthContext, AuthContextValue } from '@/context/AuthContext';

/**
 * Hook to access authentication state and methods
 *
 * @returns Authentication context value
 * @throws Error if used outside AuthProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { user, login, logout, isLoading } = useAuth();
 *
 *   if (isLoading) return <div>Loading...</div>;
 *
 *   if (!user) {
 *     return <button onClick={() => login('user', 'pass')}>Login</button>;
 *   }
 *
 *   return <button onClick={logout}>Logout</button>;
 * }
 * ```
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

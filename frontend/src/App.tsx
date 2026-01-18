/**
 * App - Main application component with routing
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import ErrorBoundary from '@/components/ErrorBoundary';
import LoginView from '@/views/LoginView';
import QueryInterfaceView from '@/views/QueryInterfaceView';
import QueryHistoryView from '@/views/QueryHistoryView';
import QueryDetailView from '@/views/QueryDetailView';

/**
 * Main App Component
 *
 * Sets up routing, authentication, and error boundaries
 */
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginView />} />

            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <QueryInterfaceView />
                </ProtectedRoute>
              }
            />

            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <QueryHistoryView />
                </ProtectedRoute>
              }
            />

            <Route
              path="/query/:id"
              element={
                <ProtectedRoute>
                  <QueryDetailView />
                </ProtectedRoute>
              }
            />

            {/* Redirect unknown routes to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;

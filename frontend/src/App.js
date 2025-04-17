import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useAuth } from './contexts/AuthContext';

// Components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ResumePage from './pages/ResumePage';
import JobsPage from './pages/JobsPage';
import MatchPage from './pages/MatchPage';
import EmailPage from './pages/EmailPage';
import SchedulePage from './pages/SchedulePage';
import QueryPage from './pages/QueryPage';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" />} />
          <Route path="register" element={!isAuthenticated ? <RegisterPage /> : <Navigate to="/dashboard" />} />
          
          <Route path="dashboard" element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          } />
          
          <Route path="resume" element={
            <ProtectedRoute>
              <ResumePage />
            </ProtectedRoute>
          } />
          
          <Route path="jobs" element={
            <ProtectedRoute>
              <JobsPage />
            </ProtectedRoute>
          } />
          
          <Route path="match" element={
            <ProtectedRoute>
              <MatchPage />
            </ProtectedRoute>
          } />
          
          <Route path="email" element={
            <ProtectedRoute>
              <EmailPage />
            </ProtectedRoute>
          } />
          
          <Route path="schedule" element={
            <ProtectedRoute>
              <SchedulePage />
            </ProtectedRoute>
          } />
          
          <Route path="query" element={
            <ProtectedRoute>
              <QueryPage />
            </ProtectedRoute>
          } />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App;

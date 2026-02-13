import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import PostQueue from './components/PostQueue';
import PostEditor from './components/PostEditor';
import AIGenerator from './components/AIGenerator';
import ScheduleSettings from './components/ScheduleSettings';
import PostHistory from './components/PostHistory';
import ConnectLinkedIn from './components/ConnectLinkedIn';
import { Spinner } from 'react-bootstrap';

function ProtectedRoute({ children }) {
    const { authenticated, loading } = useAuth();
    if (loading) return <div className="d-flex justify-content-center mt-5"><Spinner animation="border" /></div>;
    if (!authenticated) return <Navigate to="/login" />;
    return children;
}

function AppRoutes() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route index element={<Dashboard />} />
                <Route path="queue" element={<PostQueue />} />
                <Route path="create" element={<PostEditor />} />
                <Route path="edit/:id" element={<PostEditor />} />
                <Route path="generate" element={<AIGenerator />} />
                <Route path="schedule" element={<ScheduleSettings />} />
                <Route path="history" element={<PostHistory />} />
                <Route path="connect" element={<ConnectLinkedIn />} />
            </Route>
        </Routes>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <AppRoutes />
            </BrowserRouter>
        </AuthProvider>
    );
}

import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../config/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [authenticated, setAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);
    const [linkedIn, setLinkedIn] = useState({ connected: false });

    const checkAuth = useCallback(async () => {
        try {
            await api.get('/auth/me');
            setAuthenticated(true);
        } catch {
            setAuthenticated(false);
        } finally {
            setLoading(false);
        }
    }, []);

    const checkLinkedIn = useCallback(async () => {
        try {
            const { data } = await api.get('/auth/linkedin/status');
            setLinkedIn(data);
        } catch {
            setLinkedIn({ connected: false });
        }
    }, []);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    useEffect(() => {
        if (authenticated) checkLinkedIn();
    }, [authenticated, checkLinkedIn]);

    const login = async (password) => {
        const { data } = await api.post('/auth/login', { password });
        if (data.ok) {
            setAuthenticated(true);
            return true;
        }
        return false;
    };

    const logout = async () => {
        await api.post('/auth/logout');
        setAuthenticated(false);
        setLinkedIn({ connected: false });
    };

    return (
        <AuthContext.Provider value={{
            authenticated, loading, linkedIn,
            login, logout, checkLinkedIn,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be inside AuthProvider');
    return ctx;
}

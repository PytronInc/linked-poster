import React, { useState } from 'react';
import { Card, Button, Alert, Badge } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';
import api from '../config/api';
import { FiLinkedin, FiCheck, FiX } from 'react-icons/fi';

export default function ConnectLinkedIn() {
    const { linkedIn, checkLinkedIn } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleConnect = async () => {
        setLoading(true);
        setError('');
        try {
            const { data } = await api.get('/auth/linkedin/initiate');
            window.location.href = data.url;
        } catch (err) {
            setError('Failed to initiate LinkedIn connection');
            setLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (!window.confirm('Disconnect LinkedIn? You will need to re-authorize to post.')) return;
        setLoading(true);
        try {
            await api.post('/auth/linkedin/disconnect');
            await checkLinkedIn();
        } catch (err) {
            setError('Failed to disconnect');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <h4 className="mb-4">LinkedIn Connection</h4>
            {error && <Alert variant="danger">{error}</Alert>}

            <Card style={{ maxWidth: '500px' }}>
                <Card.Body>
                    <div className="text-center mb-4">
                        <FiLinkedin size={48} className="text-primary" />
                        <h5 className="mt-3">
                            {linkedIn.connected ? (
                                <Badge bg="success"><FiCheck className="me-1" />Connected</Badge>
                            ) : (
                                <Badge bg="warning"><FiX className="me-1" />Not Connected</Badge>
                            )}
                        </h5>
                    </div>

                    {linkedIn.connected && linkedIn.profile && (
                        <div className="mb-4 text-center">
                            {linkedIn.profile.picture && (
                                <img
                                    src={linkedIn.profile.picture}
                                    alt="Profile"
                                    className="rounded-circle mb-2"
                                    style={{ width: 64, height: 64 }}
                                />
                            )}
                            <p className="mb-1"><strong>{linkedIn.profile.name}</strong></p>
                            <p className="text-muted mb-1">{linkedIn.profile.email}</p>
                            {linkedIn.expires_at && (
                                <small className="text-muted">
                                    Token expires: {new Date(linkedIn.expires_at).toLocaleDateString()}
                                </small>
                            )}
                        </div>
                    )}

                    <div className="d-grid gap-2">
                        {linkedIn.connected ? (
                            <Button variant="outline-danger" onClick={handleDisconnect} disabled={loading}>
                                {loading ? 'Disconnecting...' : 'Disconnect LinkedIn'}
                            </Button>
                        ) : (
                            <Button variant="primary" size="lg" onClick={handleConnect} disabled={loading}>
                                <FiLinkedin className="me-2" />
                                {loading ? 'Connecting...' : 'Connect LinkedIn Account'}
                            </Button>
                        )}
                    </div>
                </Card.Body>
            </Card>
        </>
    );
}

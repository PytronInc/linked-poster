import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Row, Col, Card, Badge, Alert } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';
import api from '../config/api';
import { FiEdit, FiClock, FiCheck, FiAlertCircle, FiZap } from 'react-icons/fi';

export default function Dashboard() {
    const { linkedIn } = useAuth();
    const [queue, setQueue] = useState([]);
    const [history, setHistory] = useState({ posts: [], total: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const [qRes, hRes] = await Promise.all([
                    api.get('/posts/queue'),
                    api.get('/history?limit=5'),
                ]);
                setQueue(qRes.data.posts || []);
                setHistory(hRes.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const drafts = queue.filter(p => p.status === 'draft');
    const scheduled = queue.filter(p => p.status === 'scheduled');
    const nextPost = scheduled.length > 0 ? scheduled[0] : null;

    if (loading) return <div className="text-center mt-5">Loading...</div>;

    return (
        <>
            <h4 className="mb-4">Dashboard</h4>

            {!linkedIn.connected && (
                <Alert variant="warning">
                    LinkedIn is not connected. <Link to="/connect">Connect now</Link> to start posting.
                </Alert>
            )}

            <Row className="mb-4">
                <Col md={3}>
                    <Card className="text-center">
                        <Card.Body>
                            <FiEdit size={24} className="text-secondary mb-2" />
                            <h2>{drafts.length}</h2>
                            <small className="text-muted">Drafts</small>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="text-center">
                        <Card.Body>
                            <FiClock size={24} className="text-primary mb-2" />
                            <h2>{scheduled.length}</h2>
                            <small className="text-muted">Scheduled</small>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="text-center">
                        <Card.Body>
                            <FiCheck size={24} className="text-success mb-2" />
                            <h2>{history.total}</h2>
                            <small className="text-muted">Published</small>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="text-center">
                        <Card.Body>
                            <FiAlertCircle size={24} className={linkedIn.connected ? 'text-success' : 'text-warning'} />
                            <h2 className="mb-0 mt-2">
                                <Badge bg={linkedIn.connected ? 'success' : 'warning'}>
                                    {linkedIn.connected ? 'Active' : 'Inactive'}
                                </Badge>
                            </h2>
                            <small className="text-muted">LinkedIn</small>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Row>
                <Col md={6}>
                    <Card>
                        <Card.Header className="d-flex justify-content-between align-items-center">
                            <span>Next Scheduled Post</span>
                            <Link to="/queue" className="btn btn-sm btn-outline-primary">View Queue</Link>
                        </Card.Header>
                        <Card.Body>
                            {nextPost ? (
                                <>
                                    <p className="mb-2" style={{ whiteSpace: 'pre-wrap' }}>
                                        {nextPost.content.substring(0, 200)}{nextPost.content.length > 200 ? '...' : ''}
                                    </p>
                                    <small className="text-muted">
                                        <FiClock className="me-1" />
                                        {new Date(nextPost.scheduled_time).toLocaleString()}
                                    </small>
                                </>
                            ) : (
                                <p className="text-muted mb-0">No posts scheduled. <Link to="/create">Create one</Link></p>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={6}>
                    <Card>
                        <Card.Header className="d-flex justify-content-between align-items-center">
                            <span>Quick Actions</span>
                        </Card.Header>
                        <Card.Body className="d-flex flex-column gap-2">
                            <Link to="/create" className="btn btn-primary">
                                <FiEdit className="me-2" />Create New Post
                            </Link>
                            <Link to="/generate" className="btn btn-outline-primary">
                                <FiZap className="me-2" />Generate with AI
                            </Link>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {history.posts.length > 0 && (
                <Card className="mt-4">
                    <Card.Header className="d-flex justify-content-between align-items-center">
                        <span>Recent Posts</span>
                        <Link to="/history" className="btn btn-sm btn-outline-primary">View All</Link>
                    </Card.Header>
                    <Card.Body className="p-0">
                        <div className="list-group list-group-flush">
                            {history.posts.map(post => (
                                <div key={post._id} className="list-group-item">
                                    <div className="d-flex justify-content-between align-items-start">
                                        <p className="mb-1" style={{ whiteSpace: 'pre-wrap' }}>
                                            {post.content.substring(0, 150)}{post.content.length > 150 ? '...' : ''}
                                        </p>
                                        <Badge bg={post.status === 'published' ? 'success' : 'danger'}>
                                            {post.status}
                                        </Badge>
                                    </div>
                                    {post.published_at && (
                                        <small className="text-muted">
                                            {new Date(post.published_at).toLocaleString()}
                                        </small>
                                    )}
                                </div>
                            ))}
                        </div>
                    </Card.Body>
                </Card>
            )}
        </>
    );
}

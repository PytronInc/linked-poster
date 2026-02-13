import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Badge, Alert, Spinner } from 'react-bootstrap';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import api from '../config/api';
import { FiEdit2, FiTrash2, FiSend, FiClock, FiMenu } from 'react-icons/fi';

export default function PostQueue() {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [publishing, setPublishing] = useState(null);
    const navigate = useNavigate();

    const loadQueue = useCallback(async () => {
        try {
            const { data } = await api.get('/posts/queue');
            setPosts(data.posts || []);
        } catch (err) {
            setError('Failed to load queue');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadQueue(); }, [loadQueue]);

    const handleDragEnd = async (result) => {
        if (!result.destination) return;
        const items = Array.from(posts);
        const [moved] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, moved);
        setPosts(items);

        try {
            await api.put('/posts/reorder', { post_ids: items.map(p => p._id) });
        } catch (err) {
            setError('Failed to reorder');
            loadQueue();
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this post?')) return;
        try {
            await api.delete(`/posts/${id}`);
            setPosts(prev => prev.filter(p => p._id !== id));
        } catch (err) {
            setError('Failed to delete');
        }
    };

    const handlePublishNow = async (id) => {
        if (!window.confirm('Publish this post to LinkedIn now?')) return;
        setPublishing(id);
        try {
            await api.post(`/posts/${id}/publish-now`);
            loadQueue();
        } catch (err) {
            setError(err.response?.data?.detail || 'Publish failed');
        } finally {
            setPublishing(null);
        }
    };

    const statusBadge = (status) => {
        const colors = { draft: 'secondary', scheduled: 'primary', publishing: 'warning', published: 'success', failed: 'danger' };
        return <Badge bg={colors[status] || 'secondary'}>{status}</Badge>;
    };

    if (loading) return <div className="text-center mt-5"><Spinner animation="border" /></div>;

    return (
        <>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h4 className="mb-0">Post Queue</h4>
                <Button onClick={() => navigate('/create')}>+ Create Post</Button>
            </div>

            {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}

            {posts.length === 0 ? (
                <Card><Card.Body className="text-center text-muted py-5">
                    No posts in queue. Create your first post!
                </Card.Body></Card>
            ) : (
                <DragDropContext onDragEnd={handleDragEnd}>
                    <Droppable droppableId="queue">
                        {(provided) => (
                            <div ref={provided.innerRef} {...provided.droppableProps}>
                                {posts.map((post, index) => (
                                    <Draggable key={post._id} draggableId={post._id} index={index}>
                                        {(provided, snapshot) => (
                                            <Card
                                                ref={provided.innerRef}
                                                {...provided.draggableProps}
                                                className={`mb-2 ${snapshot.isDragging ? 'shadow-lg' : ''}`}
                                            >
                                                <Card.Body className="d-flex align-items-start gap-3">
                                                    <div {...provided.dragHandleProps} className="pt-1" style={{ cursor: 'grab' }}>
                                                        <FiMenu size={20} className="text-muted" />
                                                    </div>
                                                    <div className="flex-grow-1">
                                                        <div className="d-flex justify-content-between mb-2">
                                                            <div className="d-flex gap-2 align-items-center">
                                                                {statusBadge(post.status)}
                                                                {post.has_image && <Badge bg="info">Image</Badge>}
                                                            </div>
                                                            <div className="d-flex gap-1">
                                                                <Button
                                                                    variant="outline-primary"
                                                                    size="sm"
                                                                    onClick={() => navigate(`/edit/${post._id}`)}
                                                                    title="Edit"
                                                                >
                                                                    <FiEdit2 />
                                                                </Button>
                                                                <Button
                                                                    variant="outline-success"
                                                                    size="sm"
                                                                    onClick={() => handlePublishNow(post._id)}
                                                                    disabled={publishing === post._id}
                                                                    title="Publish Now"
                                                                >
                                                                    {publishing === post._id ? <Spinner size="sm" /> : <FiSend />}
                                                                </Button>
                                                                <Button
                                                                    variant="outline-danger"
                                                                    size="sm"
                                                                    onClick={() => handleDelete(post._id)}
                                                                    title="Delete"
                                                                >
                                                                    <FiTrash2 />
                                                                </Button>
                                                            </div>
                                                        </div>
                                                        <p className="mb-1" style={{ whiteSpace: 'pre-wrap', fontSize: '0.9em' }}>
                                                            {post.content.substring(0, 300)}{post.content.length > 300 ? '...' : ''}
                                                        </p>
                                                        {post.scheduled_time && (
                                                            <small className="text-muted">
                                                                <FiClock className="me-1" />
                                                                {new Date(post.scheduled_time).toLocaleString()}
                                                            </small>
                                                        )}
                                                    </div>
                                                </Card.Body>
                                            </Card>
                                        )}
                                    </Draggable>
                                ))}
                                {provided.placeholder}
                            </div>
                        )}
                    </Droppable>
                </DragDropContext>
            )}
        </>
    );
}

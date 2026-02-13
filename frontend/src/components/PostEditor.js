import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Form, Button, Alert, Row, Col, Badge } from 'react-bootstrap';
import api from '../config/api';

export default function PostEditor() {
    const { id } = useParams();
    const isEdit = !!id;
    const navigate = useNavigate();

    const [content, setContent] = useState('');
    const [status, setStatus] = useState('draft');
    const [scheduledTime, setScheduledTime] = useState('');
    const [imageFile, setImageFile] = useState(null);
    const [hasImage, setHasImage] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [charCount, setCharCount] = useState(0);

    useEffect(() => {
        if (isEdit) {
            api.get('/posts/queue').then(({ data }) => {
                const post = (data.posts || []).find(p => p._id === id);
                if (post) {
                    setContent(post.content);
                    setStatus(post.status);
                    setHasImage(post.has_image);
                    if (post.scheduled_time) {
                        setScheduledTime(post.scheduled_time.slice(0, 16));
                    }
                }
            });
        }
    }, [id, isEdit]);

    useEffect(() => { setCharCount(content.length); }, [content]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');

        try {
            const payload = {
                content,
                status,
                scheduled_time: scheduledTime ? new Date(scheduledTime).toISOString() : null,
            };

            let postId = id;
            if (isEdit) {
                await api.put(`/posts/${id}`, payload);
            } else {
                const { data } = await api.post('/posts', payload);
                postId = data._id;
            }

            // Upload image if selected
            if (imageFile && postId) {
                const formData = new FormData();
                formData.append('file', imageFile);
                await api.post(`/posts/${postId}/image`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                });
            }

            navigate('/queue');
        } catch (err) {
            setError(err.response?.data?.detail || 'Save failed');
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteImage = async () => {
        if (!id) return;
        try {
            await api.delete(`/posts/${id}/image`);
            setHasImage(false);
        } catch (err) {
            setError('Failed to remove image');
        }
    };

    return (
        <>
            <h4 className="mb-4">{isEdit ? 'Edit Post' : 'Create Post'}</h4>
            {error && <Alert variant="danger">{error}</Alert>}

            <Card>
                <Card.Body>
                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Post Content</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={10}
                                value={content}
                                onChange={e => setContent(e.target.value)}
                                maxLength={3000}
                                placeholder="Write your LinkedIn post..."
                                required
                            />
                            <div className="d-flex justify-content-between mt-1">
                                <small className={charCount > 2800 ? 'text-danger' : 'text-muted'}>
                                    {charCount}/3000 characters
                                </small>
                            </div>
                        </Form.Group>

                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Status</Form.Label>
                                    <Form.Select value={status} onChange={e => setStatus(e.target.value)}>
                                        <option value="draft">Draft</option>
                                        <option value="scheduled">Scheduled</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Schedule Time {status !== 'scheduled' && <small className="text-muted">(optional)</small>}</Form.Label>
                                    <Form.Control
                                        type="datetime-local"
                                        value={scheduledTime}
                                        onChange={e => setScheduledTime(e.target.value)}
                                        required={status === 'scheduled'}
                                    />
                                </Form.Group>
                            </Col>
                        </Row>

                        <Form.Group className="mb-3">
                            <Form.Label>Image {hasImage && <Badge bg="info" className="ms-1">Uploaded</Badge>}</Form.Label>
                            <Form.Control
                                type="file"
                                accept="image/*"
                                onChange={e => setImageFile(e.target.files[0])}
                            />
                            {hasImage && (
                                <Button variant="link" size="sm" className="text-danger p-0 mt-1" onClick={handleDeleteImage}>
                                    Remove existing image
                                </Button>
                            )}
                        </Form.Group>

                        <div className="d-flex gap-2">
                            <Button type="submit" disabled={saving || !content.trim()}>
                                {saving ? 'Saving...' : isEdit ? 'Update Post' : 'Add to Queue'}
                            </Button>
                            <Button variant="outline-secondary" onClick={() => navigate('/queue')}>
                                Cancel
                            </Button>
                        </div>
                    </Form>
                </Card.Body>
            </Card>
        </>
    );
}

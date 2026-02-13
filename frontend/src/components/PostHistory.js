import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Spinner, Button } from 'react-bootstrap';
import api from '../config/api';
import { FiArchive } from 'react-icons/fi';

export default function PostHistory() {
    const [posts, setPosts] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(0);
    const limit = 20;

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const { data } = await api.get(`/history?skip=${page * limit}&limit=${limit}`);
                setPosts(data.posts || []);
                setTotal(data.total);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [page]);

    if (loading) return <div className="text-center mt-5"><Spinner animation="border" /></div>;

    const totalPages = Math.ceil(total / limit);

    return (
        <>
            <h4 className="mb-4"><FiArchive className="me-2" />Post History</h4>

            {posts.length === 0 ? (
                <Card><Card.Body className="text-center text-muted py-5">
                    No published posts yet.
                </Card.Body></Card>
            ) : (
                <>
                    <Card>
                        <Table responsive hover className="mb-0">
                            <thead>
                                <tr>
                                    <th>Content</th>
                                    <th>Status</th>
                                    <th>Published</th>
                                    <th>Type</th>
                                </tr>
                            </thead>
                            <tbody>
                                {posts.map(post => (
                                    <tr key={post._id}>
                                        <td style={{ maxWidth: 400 }}>
                                            <span style={{ whiteSpace: 'pre-wrap' }}>
                                                {post.content.substring(0, 200)}{post.content.length > 200 ? '...' : ''}
                                            </span>
                                            {post.error && (
                                                <div className="text-danger mt-1" style={{ fontSize: '0.8em' }}>
                                                    Error: {post.error}
                                                </div>
                                            )}
                                        </td>
                                        <td>
                                            <Badge bg={post.status === 'published' ? 'success' : 'danger'}>
                                                {post.status}
                                            </Badge>
                                        </td>
                                        <td>
                                            {post.published_at
                                                ? new Date(post.published_at).toLocaleString()
                                                : '-'}
                                        </td>
                                        <td>
                                            <Badge bg="secondary">{post.post_type || 'text'}</Badge>
                                            {post.has_image && <Badge bg="info" className="ms-1">Image</Badge>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    </Card>

                    {totalPages > 1 && (
                        <div className="d-flex justify-content-center gap-2 mt-3">
                            <Button
                                variant="outline-primary"
                                size="sm"
                                disabled={page === 0}
                                onClick={() => setPage(p => p - 1)}
                            >
                                Previous
                            </Button>
                            <span className="align-self-center text-muted">
                                Page {page + 1} of {totalPages}
                            </span>
                            <Button
                                variant="outline-primary"
                                size="sm"
                                disabled={page >= totalPages - 1}
                                onClick={() => setPage(p => p + 1)}
                            >
                                Next
                            </Button>
                        </div>
                    )}
                </>
            )}
        </>
    );
}

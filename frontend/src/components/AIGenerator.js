import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Button, Alert, Spinner, Row, Col } from 'react-bootstrap';
import api from '../config/api';
import { FiZap, FiPlus, FiRefreshCw } from 'react-icons/fi';

export default function AIGenerator() {
    const navigate = useNavigate();
    const [topic, setTopic] = useState('');
    const [tone, setTone] = useState('professional');
    const [postType, setPostType] = useState('text');
    const [context, setContext] = useState('');
    const [variants, setVariants] = useState([]);
    const [generating, setGenerating] = useState(false);
    const [improving, setImproving] = useState(null);
    const [error, setError] = useState('');
    const [addingToQueue, setAddingToQueue] = useState(null);

    const handleGenerate = async (e) => {
        e.preventDefault();
        setGenerating(true);
        setError('');
        setVariants([]);

        try {
            const { data } = await api.post('/generate', {
                topic,
                tone,
                post_type: postType,
                additional_context: context || null,
            });
            setVariants(data.variants || []);
        } catch (err) {
            setError(err.response?.data?.detail || 'Generation failed');
        } finally {
            setGenerating(false);
        }
    };

    const handleImprove = async (index) => {
        setImproving(index);
        try {
            const { data } = await api.post('/generate/improve', {
                content: variants[index],
            });
            const updated = [...variants];
            updated[index] = data.improved;
            setVariants(updated);
        } catch (err) {
            setError('Improve failed');
        } finally {
            setImproving(null);
        }
    };

    const handleAddToQueue = async (index) => {
        setAddingToQueue(index);
        try {
            await api.post('/posts', {
                content: variants[index],
                status: 'draft',
            });
            const updated = [...variants];
            updated.splice(index, 1);
            setVariants(updated);
            if (updated.length === 0) navigate('/queue');
        } catch (err) {
            setError('Failed to add to queue');
        } finally {
            setAddingToQueue(null);
        }
    };

    return (
        <>
            <h4 className="mb-4"><FiZap className="me-2" />AI Post Generator</h4>
            {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}

            <Card className="mb-4">
                <Card.Body>
                    <Form onSubmit={handleGenerate}>
                        <Form.Group className="mb-3">
                            <Form.Label>Topic / Idea</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={3}
                                value={topic}
                                onChange={e => setTopic(e.target.value)}
                                placeholder="e.g., The importance of building in public, Lessons from scaling a SaaS..."
                                required
                            />
                        </Form.Group>

                        <Row>
                            <Col md={4}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Tone</Form.Label>
                                    <Form.Select value={tone} onChange={e => setTone(e.target.value)}>
                                        <option value="professional">Professional</option>
                                        <option value="casual">Casual</option>
                                        <option value="thought-leadership">Thought Leadership</option>
                                        <option value="storytelling">Storytelling</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={4}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Post Type</Form.Label>
                                    <Form.Select value={postType} onChange={e => setPostType(e.target.value)}>
                                        <option value="text">Text Post</option>
                                        <option value="insight">Insight / Lesson</option>
                                        <option value="article_share">Article Share</option>
                                        <option value="poll_intro">Poll Intro</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={4}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Additional Context</Form.Label>
                                    <Form.Control
                                        value={context}
                                        onChange={e => setContext(e.target.value)}
                                        placeholder="Optional: your background, company, etc."
                                    />
                                </Form.Group>
                            </Col>
                        </Row>

                        <Button type="submit" disabled={generating || !topic.trim()}>
                            {generating ? (
                                <><Spinner size="sm" className="me-2" />Generating...</>
                            ) : (
                                <><FiZap className="me-2" />Generate 3 Variants</>
                            )}
                        </Button>
                    </Form>
                </Card.Body>
            </Card>

            {variants.map((variant, i) => (
                <Card key={i} className="mb-3">
                    <Card.Header className="d-flex justify-content-between align-items-center">
                        <span>Variant {i + 1}</span>
                        <div className="d-flex gap-1">
                            <Button
                                variant="outline-secondary"
                                size="sm"
                                onClick={() => handleImprove(i)}
                                disabled={improving === i}
                            >
                                {improving === i ? <Spinner size="sm" /> : <><FiRefreshCw className="me-1" />Improve</>}
                            </Button>
                            <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleAddToQueue(i)}
                                disabled={addingToQueue === i}
                            >
                                {addingToQueue === i ? <Spinner size="sm" /> : <><FiPlus className="me-1" />Add to Queue</>}
                            </Button>
                        </div>
                    </Card.Header>
                    <Card.Body>
                        <p style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{variant}</p>
                    </Card.Body>
                </Card>
            ))}
        </>
    );
}

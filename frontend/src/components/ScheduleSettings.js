import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Alert, Row, Col, Table } from 'react-bootstrap';
import api from '../config/api';
import { FiClock, FiPlus, FiTrash2 } from 'react-icons/fi';

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const DAY_LABELS = { monday: 'Monday', tuesday: 'Tuesday', wednesday: 'Wednesday', thursday: 'Thursday', friday: 'Friday', saturday: 'Saturday', sunday: 'Sunday' };

export default function ScheduleSettings() {
    const [settings, setSettings] = useState(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        api.get('/settings/schedule').then(({ data }) => setSettings(data)).catch(() => setError('Failed to load settings'));
    }, []);

    if (!settings) return <div className="text-center mt-5">Loading...</div>;

    const toggleDay = (day) => {
        setSettings(prev => ({
            ...prev,
            schedule: {
                ...prev.schedule,
                [day]: { ...prev.schedule[day], enabled: !prev.schedule[day].enabled },
            },
        }));
    };

    const addSlot = (day) => {
        setSettings(prev => ({
            ...prev,
            schedule: {
                ...prev.schedule,
                [day]: {
                    ...prev.schedule[day],
                    slots: [...prev.schedule[day].slots, { hour: 9, minute: 0 }],
                },
            },
        }));
    };

    const removeSlot = (day, index) => {
        setSettings(prev => ({
            ...prev,
            schedule: {
                ...prev.schedule,
                [day]: {
                    ...prev.schedule[day],
                    slots: prev.schedule[day].slots.filter((_, i) => i !== index),
                },
            },
        }));
    };

    const updateSlot = (day, index, field, value) => {
        setSettings(prev => ({
            ...prev,
            schedule: {
                ...prev.schedule,
                [day]: {
                    ...prev.schedule[day],
                    slots: prev.schedule[day].slots.map((s, i) =>
                        i === index ? { ...s, [field]: parseInt(value) } : s
                    ),
                },
            },
        }));
    };

    const handleSave = async () => {
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            await api.put('/settings/schedule', settings);
            setSuccess('Schedule saved!');
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError('Failed to save');
        } finally {
            setSaving(false);
        }
    };

    return (
        <>
            <h4 className="mb-4"><FiClock className="me-2" />Posting Schedule</h4>
            {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
            {success && <Alert variant="success">{success}</Alert>}

            <Row className="mb-4">
                <Col md={4}>
                    <Card>
                        <Card.Body>
                            <Form.Group className="mb-3">
                                <Form.Label>Timezone</Form.Label>
                                <Form.Control
                                    value={settings.timezone}
                                    onChange={e => setSettings(prev => ({ ...prev, timezone: e.target.value }))}
                                    placeholder="e.g., UTC, America/New_York"
                                />
                            </Form.Group>
                            <Form.Group>
                                <Form.Label>Daily Cap</Form.Label>
                                <Form.Control
                                    type="number"
                                    min={1}
                                    max={50}
                                    value={settings.daily_cap}
                                    onChange={e => setSettings(prev => ({ ...prev, daily_cap: parseInt(e.target.value) }))}
                                />
                                <Form.Text className="text-muted">Max posts per day (LinkedIn limit: 150/day)</Form.Text>
                            </Form.Group>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={8}>
                    <Card>
                        <Card.Body>
                            <Table borderless size="sm">
                                <thead>
                                    <tr>
                                        <th>Day</th>
                                        <th>Enabled</th>
                                        <th>Time Slots</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {DAYS.map(day => (
                                        <tr key={day}>
                                            <td className="align-middle">{DAY_LABELS[day]}</td>
                                            <td className="align-middle">
                                                <Form.Check
                                                    type="switch"
                                                    checked={settings.schedule[day]?.enabled ?? false}
                                                    onChange={() => toggleDay(day)}
                                                />
                                            </td>
                                            <td>
                                                {settings.schedule[day]?.enabled && (settings.schedule[day]?.slots || []).map((slot, i) => (
                                                    <div key={i} className="d-flex align-items-center gap-1 mb-1">
                                                        <Form.Control
                                                            type="number"
                                                            min={0} max={23}
                                                            value={slot.hour}
                                                            onChange={e => updateSlot(day, i, 'hour', e.target.value)}
                                                            style={{ width: 65 }}
                                                            size="sm"
                                                        />
                                                        <span>:</span>
                                                        <Form.Control
                                                            type="number"
                                                            min={0} max={59}
                                                            value={slot.minute}
                                                            onChange={e => updateSlot(day, i, 'minute', e.target.value)}
                                                            style={{ width: 65 }}
                                                            size="sm"
                                                        />
                                                        <Button
                                                            variant="link"
                                                            size="sm"
                                                            className="text-danger p-0"
                                                            onClick={() => removeSlot(day, i)}
                                                        >
                                                            <FiTrash2 />
                                                        </Button>
                                                    </div>
                                                ))}
                                            </td>
                                            <td className="align-middle">
                                                {settings.schedule[day]?.enabled && (
                                                    <Button variant="link" size="sm" onClick={() => addSlot(day)}>
                                                        <FiPlus />
                                                    </Button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </Table>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : 'Save Schedule'}
            </Button>
        </>
    );
}

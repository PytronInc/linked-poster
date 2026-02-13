import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Container, Nav, Navbar, Button } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';
import { FiHome, FiList, FiEdit, FiZap, FiClock, FiArchive, FiLinkedin, FiLogOut } from 'react-icons/fi';

export default function Layout() {
    const { logout, linkedIn } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const navItems = [
        { to: '/', icon: <FiHome />, label: 'Dashboard', end: true },
        { to: '/queue', icon: <FiList />, label: 'Queue' },
        { to: '/create', icon: <FiEdit />, label: 'Create' },
        { to: '/generate', icon: <FiZap />, label: 'AI Generate' },
        { to: '/schedule', icon: <FiClock />, label: 'Schedule' },
        { to: '/history', icon: <FiArchive />, label: 'History' },
    ];

    return (
        <>
            <Navbar bg="dark" variant="dark" expand="lg" className="mb-3">
                <Container fluid>
                    <Navbar.Brand as={NavLink} to="/">
                        <FiLinkedin className="me-2" />
                        LinkedIn AutoPoster
                    </Navbar.Brand>
                    <Navbar.Toggle />
                    <Navbar.Collapse>
                        <Nav className="me-auto">
                            {navItems.map(item => (
                                <Nav.Link
                                    key={item.to}
                                    as={NavLink}
                                    to={item.to}
                                    end={item.end}
                                    className="d-flex align-items-center gap-1"
                                >
                                    {item.icon} {item.label}
                                </Nav.Link>
                            ))}
                        </Nav>
                        <Nav className="d-flex align-items-center gap-2">
                            <Nav.Link as={NavLink} to="/connect" className="d-flex align-items-center gap-1">
                                <FiLinkedin />
                                <span className={linkedIn.connected ? 'text-success' : 'text-warning'}>
                                    {linkedIn.connected ? 'Connected' : 'Not Connected'}
                                </span>
                            </Nav.Link>
                            <Button variant="outline-light" size="sm" onClick={handleLogout}>
                                <FiLogOut className="me-1" /> Logout
                            </Button>
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
            <Container fluid className="px-4">
                <Outlet />
            </Container>
        </>
    );
}

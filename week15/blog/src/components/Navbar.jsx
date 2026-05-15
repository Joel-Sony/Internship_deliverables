import { Link, useLocation } from 'react-router-dom'
import './Navbar.css'

export default function Navbar() {
  const { pathname } = useLocation()
  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">📖 DevBlog</Link>
      <div className="nav-links">
        <Link to="/" className={pathname === '/' ? 'active' : ''}>Posts</Link>
      </div>
    </nav>
  )
}

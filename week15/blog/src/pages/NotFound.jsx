import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <main style={{ textAlign: 'center', padding: '5rem 1rem' }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>404</div>
      <h1 style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>Page not found</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '1.5rem' }}>
        The page you're looking for doesn't exist.
      </p>
      <Link
        to="/"
        style={{
          background: 'var(--accent)', color: '#fff', padding: '0.6rem 1.4rem',
          borderRadius: '8px', fontWeight: 600, fontSize: '0.9rem',
        }}
      >
        ← Back to Blog
      </Link>
    </main>
  )
}

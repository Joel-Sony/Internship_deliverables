import { useParams, Link, useNavigate } from 'react-router-dom'
import POSTS from '../data/posts'
import './PostView.css'

const BADGE_COLOUR = {
  Technology: '#dbeafe', Design: '#fce7f3', Career: '#dcfce7', Tutorial: '#fef3c7',
}
const BADGE_TEXT = {
  Technology: '#1d4ed8', Design: '#9d174d', Career: '#166534', Tutorial: '#92400e',
}

export default function PostView() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const post     = POSTS.find(p => p.id === Number(id))

  if (!post) {
    return (
      <main className="post-page">
        <p className="not-found-msg">Post not found. <Link to="/">← Back to posts</Link></p>
      </main>
    )
  }

  // Prev / next posts in same category
  const sameCat = POSTS.filter(p => p.category === post.category)
  const idx     = sameCat.findIndex(p => p.id === post.id)
  const prev    = sameCat[idx - 1]
  const next    = sameCat[idx + 1]

  return (
    <main className="post-page">
      <button className="back-btn" onClick={() => navigate(-1)}>← Back</button>

      <article className="post-article">
        {/* Meta */}
        <div className="post-meta">
          <span
            className="badge"
            style={{ background: BADGE_COLOUR[post.category], color: BADGE_TEXT[post.category] }}
          >
            {post.category}
          </span>
          <span className="meta-date">{formatDate(post.date)}</span>
          <span className="meta-read">{post.readTime} read</span>
        </div>

        <h1 className="post-title">{post.title}</h1>
        <p className="post-excerpt">{post.excerpt}</p>

        <hr className="divider" />

        <div className="post-body">
          {post.body.split('\n\n').map((para, i) => (
            para.startsWith('```')
              ? <pre key={i} className="code-block"><code>{para.replace(/```\w*\n?/g, '').replace(/```/g, '')}</code></pre>
              : <p key={i}>{para}</p>
          ))}
        </div>
      </article>

      {/* Prev / Next navigation */}
      {(prev || next) && (
        <nav className="post-nav">
          {prev ? (
            <Link to={`/post/${prev.id}`} className="post-nav-link prev">
              <span className="nav-label">← Previous</span>
              <span className="nav-title">{prev.title}</span>
            </Link>
          ) : <div />}
          {next ? (
            <Link to={`/post/${next.id}`} className="post-nav-link next">
              <span className="nav-label">Next →</span>
              <span className="nav-title">{next.title}</span>
            </Link>
          ) : <div />}
        </nav>
      )}
    </main>
  )
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}

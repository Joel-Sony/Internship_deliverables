import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import POSTS, { CATEGORIES, POSTS_PER_PAGE } from '../data/posts'
import './BlogList.css'

/* ── Category badge colour map ────────────────────────── */
const BADGE_COLOUR = {
  Technology: '#dbeafe',   // blue-100
  Design:     '#fce7f3',   // pink-100
  Career:     '#dcfce7',   // green-100
  Tutorial:   '#fef3c7',   // amber-100
}
const BADGE_TEXT = {
  Technology: '#1d4ed8',
  Design:     '#9d174d',
  Career:     '#166534',
  Tutorial:   '#92400e',
}

export default function BlogList() {
  // Keep category + page in URL so the browser Back button works
  const [searchParams, setSearchParams] = useSearchParams()
  const category = searchParams.get('category') || 'All'
  const page     = parseInt(searchParams.get('page') || '1', 10)

  function setCategory(cat) {
    setSearchParams({ category: cat, page: '1' })
  }
  function setPage(p) {
    setSearchParams({ category, page: String(p) })
  }

  // Filter
  const filtered = category === 'All'
    ? POSTS
    : POSTS.filter(p => p.category === category)

  // Paginate
  const totalPages = Math.ceil(filtered.length / POSTS_PER_PAGE)
  const safePage   = Math.min(Math.max(page, 1), totalPages)
  const paged      = filtered.slice((safePage - 1) * POSTS_PER_PAGE, safePage * POSTS_PER_PAGE)

  return (
    <main className="list-page">
      {/* Header */}
      <div className="list-header">
        <h1>Blog</h1>
        <p className="list-sub">{filtered.length} article{filtered.length !== 1 ? 's' : ''}</p>
      </div>

      {/* Category filters */}
      <div className="filters" role="tablist" aria-label="Filter by category">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            role="tab"
            aria-selected={cat === category}
            className={`filter-btn ${cat === category ? 'active' : ''}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Post grid */}
      {paged.length === 0 ? (
        <p className="empty">No posts in this category yet.</p>
      ) : (
        <div className="post-grid">
          {paged.map(post => (
            <Link to={`/post/${post.id}`} key={post.id} className="post-card">
              <div className="card-top">
                <span
                  className="badge"
                  style={{ background: BADGE_COLOUR[post.category], color: BADGE_TEXT[post.category] }}
                >
                  {post.category}
                </span>
                <span className="read-time">{post.readTime} read</span>
              </div>
              <h2 className="card-title">{post.title}</h2>
              <p className="card-excerpt">{post.excerpt}</p>
              <div className="card-footer">
                <span className="post-date">{formatDate(post.date)}</span>
                <span className="read-link">Read →</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination" aria-label="Pagination">
          <button
            className="page-btn"
            disabled={safePage === 1}
            onClick={() => setPage(safePage - 1)}
          >
            ← Prev
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map(n => (
            <button
              key={n}
              className={`page-btn ${n === safePage ? 'active' : ''}`}
              onClick={() => setPage(n)}
              aria-current={n === safePage ? 'page' : undefined}
            >
              {n}
            </button>
          ))}

          <button
            className="page-btn"
            disabled={safePage === totalPages}
            onClick={() => setPage(safePage + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </main>
  )
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

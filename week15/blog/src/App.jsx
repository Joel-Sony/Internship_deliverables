import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import BlogList from './pages/BlogList'
import PostView from './pages/PostView'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/"           element={<BlogList />} />
        <Route path="/post/:id"   element={<PostView />} />
        <Route path="*"           element={<NotFound />} />
      </Routes>
    </>
  )
}

import './index.css'
import StatCard from './StatCard'
import RecentItems from './RecentItems'
import Announcements from './Announcements'

const statsData = [
  { label: 'Total Users', value: '12,480', change: '▲ 8.2%', trend: 'up' },
  { label: 'Revenue', value: '$4,290', change: '▲ 3.1%', trend: 'up' },
  { label: 'Active Tasks', value: '34', change: '▼ 2 from yesterday', trend: 'down' },
];

const activityData = [
  { id: 1, name: 'Q2 Report.pdf', status: 'Done', time: '2 min ago', type: 'file' },
  { id: 2, name: 'API bug fix #204', status: 'Review', time: '18 min ago', type: 'code' },
  { id: 3, name: 'UX Research Notes', status: 'Done', time: '1 hour ago', type: 'doc' },
];

const announcementData = [
  { id: 1, title: 'New design system launched', text: 'Updated components are now live. Check the docs for migration steps.', time: 'Today', team: 'Product team', color: '#38bdf8' },
  { id: 2, title: 'Scheduled maintenance Friday', text: 'Services will be unavailable from 2–4 AM UTC on May 2.', time: 'Yesterday', team: 'Infrastructure', color: '#f59e0b' },
  { id: 3, title: 'Q2 planning kickoff', text: 'All-hands meeting on Thursday at 10 AM. Agenda shared on Notion.', time: '2 days ago', team: 'Leadership', color: '#a855f7' },
];

function App() {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Welcome back, here's what's happening today.</p>
      </header>

      <div className="stats-grid">
        {statsData.map(s => <StatCard key={s.label} {...s} />)}
      </div>

      <div className="content-grid">
        <RecentItems items={activityData} />
        <Announcements items={announcementData} />
      </div>
    </div>
  )
}

export default App

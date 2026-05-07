function AnnouncementItem({ title, text, time, team, color }) {
    return (
        <div className="list-item">
            <div className="item-icon" style={{ background: `${color}20`, color: color }}>
                🔔
            </div>
            <div className="item-content">
                <p className="item-title">{title}</p>
                <p className="item-desc">{text}</p>
                <div className="item-meta">
                    <span>{time}</span>
                    <span>•</span>
                    <span>{team}</span>
                </div>
            </div>
        </div>
    );
}

function Announcements({ items }) {
    return (
        <div className="card">
            <div className="card-title">
                <h3>Announcements</h3>
                <span className="card-action">See all</span>
            </div>
            <div className="list-container">
                {items.map(ann => (
                    <AnnouncementItem key={ann.id} {...ann} />
                ))}
            </div>
        </div>
    );
}

export default Announcements;
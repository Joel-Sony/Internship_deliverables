function getIcon(type) {
    switch(type) {
        case 'file': return '📄';
        case 'code': return '💻';
        case 'doc':  return '📝';
        default:     return '📌';
    }
}

function RecentItems({ items }) {
    return (
        <div className="card">
            <div className="card-title">
                <h3>Recent Activity</h3>
                <span className="card-action">View all</span>
            </div>
            <div className="list-container">
                {items.map(item => (
                    <div key={item.id} className="list-item">
                        <div className="item-icon">
                            {getIcon(item.type)}
                        </div>
                        <div className="item-content">
                            <p className="item-title">{item.name}</p>
                            <div className="item-meta">
                                <span>{item.time}</span>
                                <span className={`status-badge status-${item.status.toLowerCase()}`}>
                                    {item.status}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default RecentItems
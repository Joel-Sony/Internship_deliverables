function StatCard({ label, value, change, trend }) {
    return (
        <div className="card">
            <p className="stat-label">{label}</p>
            <h2 className="stat-value">{value}</h2>
            <span className={`stat-change ${trend}`}>
                {change}
            </span>
        </div>
    );
}

export default StatCard
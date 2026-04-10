export default function StatCard({ icon, value, label, color = 'var(--color-primary)' }) {
  return (
    <div className="stat-card" style={{ '--stat-color': color }}>
      <span className="stat-card-icon">{icon}</span>
      <div className="stat-card-value">{value ?? '—'}</div>
      <div className="stat-card-label">{label}</div>
    </div>
  );
}

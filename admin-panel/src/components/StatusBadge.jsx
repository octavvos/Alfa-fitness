const MAP = {
  faol: { text: "Faol", cls: "badge-success" },
  muzlatilgan: { text: "Muzlatilgan", cls: "badge-warning" },
  tugagan: { text: "Tugagan", cls: "badge-muted" },
  bekor: { text: "Bekor qilingan", cls: "badge-danger" },
};

export default function StatusBadge({ status }) {
  const info = MAP[status] ?? { text: status, cls: "badge-muted" };
  return <span className={`badge ${info.cls}`}>{info.text}</span>;
}

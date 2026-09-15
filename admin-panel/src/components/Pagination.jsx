export default function Pagination({ page, setPage, count, pageSize = 20 }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages <= 1) return null;

  return (
    <div className="pagination">
      <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>
        ← Oldingi
      </button>
      <span>
        {page} / {totalPages} ({count} ta)
      </span>
      <button className="btn" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
        Keyingi →
      </button>
    </div>
  );
}

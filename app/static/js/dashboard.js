(async () => {
    const res = await fetch('/api/inventory?fields=nibar,judul_buku&per_page=500&page=1');
    const first = await res.json();
    let items = first.items;
    const total = first.total;
    let page = 2;
    while (items.length < total) {
        const r = await fetch(`/api/inventory?fields=nibar,judul_buku&per_page=500&page=${page}`);
        const d = await r.json();
        if (!d.items.length) break;
        items = items.concat(d.items);
        page += 1;
    }

    const table = new Tabulator('#grid', {
        data: items,
        layout: 'fitColumns',
        height: 'calc(100vh - 160px)',
        pagination: true,
        paginationSize: 50,
        paginationSizeSelector: [25, 50, 100, 200],
        columns: [
            {title: 'NIBAR', field: 'nibar', width: 160, headerFilter: 'input'},
            {title: 'Judul Buku', field: 'judul_buku', headerFilter: 'input'},
        ],
    });

    document.getElementById('filter').addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        if (!q) { table.clearFilter(true); return; }
        table.setFilter((row) => {
            return String(row.nibar || '').toLowerCase().includes(q)
                || String(row.judul_buku || '').toLowerCase().includes(q);
        });
    });
})();

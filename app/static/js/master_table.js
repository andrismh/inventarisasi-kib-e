(async () => {
    const status = document.getElementById('status');

    const [barang, satuan, ruang, kondisi] = await Promise.all([
        fetch('/api/masters/barang').then(r => r.json()),
        fetch('/api/masters/satuan').then(r => r.json()),
        fetch('/api/masters/ruang').then(r => r.json()),
        fetch('/api/masters/kondisi').then(r => r.json()),
    ]);
    const toMap = (rows) => Object.fromEntries(rows.map(r => [r.id, r.nama]));
    const masterMaps = {
        barang: toMap(barang), satuan: toMap(satuan),
        ruang: toMap(ruang), kondisi: toMap(kondisi),
    };
    const listEditor = (rows, allowEmpty = false) => ({
        editor: 'list',
        editorParams: {
            values: [
                ...(allowEmpty ? [{label: '—', value: null}] : []),
                ...rows.map(r => ({label: r.nama, value: r.id})),
            ],
            autocomplete: true,
            listOnEmpty: true,
        },
        formatter: (cell) => {
            const v = cell.getValue();
            const mapKey = cell.getColumn().getDefinition().masterKey;
            return v == null ? '' : (masterMaps[mapKey][v] || v);
        },
    });

    // Load all rows (paged)
    status.textContent = 'Loading...';
    let items = [];
    let page = 1;
    while (true) {
        const r = await fetch(`/api/inventory?per_page=500&page=${page}`);
        const d = await r.json();
        items = items.concat(d.items);
        if (items.length >= d.total || !d.items.length) break;
        page += 1;
    }
    status.textContent = `${items.length} rows`;

    const enumEditor = (vals) => ({
        editor: 'list',
        editorParams: {values: [{label: '—', value: null}, ...vals.map(v => ({label: v, value: v}))]},
    });

    const columns = [
        {title: 'NIBAR', field: 'nibar', frozen: true, width: 120, editor: false},
        {title: 'Kode Reg.', field: 'kode_register', editor: 'input', width: 110},
        {title: 'Kode Barang', field: 'kode_barang_id', masterKey: 'barang', width: 240, ...listEditor(barang)},
        {title: 'Tahun', field: 'tahun_perolehan', editor: 'number', width: 90},
        {title: 'Nilai (Rp)', field: 'nilai_perolehan', editor: 'number', width: 120},
        {title: 'Spesifikasi', field: 'spesifikasi', editor: 'input', width: 200},
        {title: 'Jenis Aset', field: 'jenis_aset', width: 200, ...enumEditor(['BUKU', 'BARANG BERCORAK KESENIAN', 'HEWAN & TUMBUHAN'])},
        {title: 'Judul Buku', field: 'judul_buku', editor: 'input', width: 280},
        {title: 'Pencipta', field: 'pencipta_buku', editor: 'input', width: 180},
        {title: 'Spesifikasi Buku', field: 'spesifikasi_buku', editor: 'input', width: 180},
        {title: 'Jumlah', field: 'jumlah_barang', editor: 'number', width: 90},
        {title: 'Satuan', field: 'satuan_barang_id', masterKey: 'satuan', width: 140, ...listEditor(satuan)},
        {title: 'Status Keberadaan', field: 'status_keberadaan', width: 160, ...enumEditor(['hilang', 'tidak ditemukan'])},
        {title: 'Jml Hilang', field: 'jml_keberadaan', editor: 'number', width: 110},
        {title: 'Atribusi?', field: 'merupakan_atribusi', width: 110, ...enumEditor(['ya', 'tidak'])},
        {title: 'NIBAR Atribusi', field: 'nibar_atribusi', editor: 'number', width: 140},
        {title: 'Alamat', field: 'alamat', editor: 'input', width: 200},
        {title: 'Koordinat', field: 'koordinat', editor: 'input', width: 160},
        {title: 'Ruangan', field: 'ruangan_id', masterKey: 'ruang', width: 280, ...listEditor(ruang, true)},
        {title: 'Kondisi', field: 'kondisi_barang_id', masterKey: 'kondisi', width: 160, ...listEditor(kondisi)},
        {title: 'Merk/Type', field: 'merk_type', editor: 'input', width: 160},
        {title: 'Penggunaan', field: 'penggunaan', width: 200, ...enumEditor(['pemerintah daerah', 'pemerintah pusat', 'pemerintah daerah lainnya', 'pihak lain'])},
        {title: 'Nama Kuasa', field: 'nama_kuasa', editor: 'input', width: 160},
        {title: 'Nama Pemakai', field: 'nama_pemakai', editor: 'input', width: 160},
        {title: 'Status Pemakai', field: 'status_pemakai', editor: 'input', width: 140},
        {title: 'BAST', field: 'bast', width: 90, ...enumEditor(['ada', 'tidak'])},
        {title: 'Dasar Penggunaan', field: 'nama_dasar_penggunaan', editor: 'input', width: 180},
        {title: 'Nama Dokumen', field: 'nama_dokumen', editor: 'input', width: 160},
        {title: 'Tercatat Ganda', field: 'nibar_tercatat_ganda', editor: 'input', width: 140},
        {title: 'Deskripsi', field: 'deskripsi_barang', editor: 'input', width: 200},
        {title: 'Keterangan', field: 'keterangan', editor: 'input', width: 200},
        {title: 'Petugas', field: 'petugas', editor: 'input', width: 180},
        {title: 'Foto', field: 'foto', editor: 'input', width: 160},
    ];

    const table = new Tabulator('#grid', {
        data: items,
        layout: 'fitData',
        height: 'calc(100vh - 160px)',
        index: 'nibar',
        pagination: true,
        paginationSize: 50,
        paginationSizeSelector: [25, 50, 100, 200],
        columns,
        rowContextMenu: [
            {
                label: 'Delete row',
                action: async (e, row) => {
                    if (!confirm(`Delete NIBAR ${row.getData().nibar}?`)) return;
                    const r = await fetch(`/api/inventory/${row.getData().nibar}`, {method: 'DELETE'});
                    if (r.status === 204) row.delete();
                    else alert('Delete failed');
                },
            },
        ],
        cellEdited: async (cell) => {
            const data = cell.getRow().getData();
            const field = cell.getField();
            const value = cell.getValue();
            const r = await fetch(`/api/inventory/${data.nibar}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({[field]: value}),
            });
            if (!r.ok) {
                cell.restoreOldValue();
                const d = await r.json().catch(() => ({}));
                alert(d.error || `Update failed (${r.status})`);
            }
        },
    });

    const filterInput = document.getElementById('filter');
    if (filterInput) {
        filterInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            if (!term) {
                table.clearFilter();
                return;
            }
            table.setFilter((data) => {
                return Object.values(data).some(v => String(v ?? '').toLowerCase().includes(term));
            });
        });
    }
})();

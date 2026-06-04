(async () => {
    const status = document.getElementById('status');
    const subtitle = document.getElementById('editor-subtitle');
    const queueFilter = document.getElementById('queue-filter');
    const filterInput = document.getElementById('filter');
    const reloadButton = document.getElementById('reload-grid');
    const params = new URLSearchParams(window.location.search);
    const fmt = new Intl.NumberFormat('id-ID');
    const savedState = params.get('saved');
    const escapeHtml = (value) => String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');

    const queueLabels = {
        all_optional: 'Any missing optional field',
        judul_buku: 'Missing Judul Buku',
        pencipta_buku: 'Missing Pencipta Buku',
        spesifikasi_buku: 'Missing Spesifikasi Buku',
        spesifikasi: 'Missing Asal Usul',
        merupakan_atribusi: 'Missing Merupakan Atribusi',
        alamat: 'Missing Alamat',
        koordinat: 'Missing Koordinat',
        ruangan_id: 'Missing Ruangan',
        merk_type: 'Missing Merk / Type',
        penggunaan: 'Missing Penggunaan',
        nama_kuasa: 'Missing Nama Kuasa',
        nama_pemakai: 'Missing Nama Pemakai',
        status_pemakai: 'Missing Status Pemakai',
        bast: 'Missing BAST',
        nibar_tercatat_ganda: 'Missing NIBAR Tercatat Ganda',
        deskripsi_barang: 'Missing Deskripsi Barang',
        keterangan: 'Missing Keterangan',
        petugas: 'Missing Petugas',
        foto: 'Missing Foto',
        'duplicates:judul_buku': 'Duplicate title risk',
    };

    const initialMissing = params.get('missing') || '';
    const initialDuplicates = params.get('duplicates') ? `duplicates:${params.get('duplicates')}` : '';
    const initialQuery = params.get('q') || '';
    const initialQueue = initialDuplicates || initialMissing;
    if (initialQueue && ![...queueFilter.options].some(o => o.value === initialQueue)) {
        const opt = document.createElement('option');
        opt.value = initialQueue;
        opt.textContent = queueLabels[initialQueue] || initialQueue;
        queueFilter.appendChild(opt);
    }
    queueFilter.value = initialQueue;
    filterInput.value = initialQuery;

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
                ...(allowEmpty ? [{label: '-', value: null}] : []),
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

    const enumEditor = (vals) => ({
        editor: 'list',
        editorParams: {values: [{label: '-', value: null}, ...vals.map(v => ({label: v, value: v}))]},
    });

    const columns = [
        {title: 'NIBAR', field: 'nibar', frozen: true, width: 120, editor: false},
        {title: 'Kode Reg.', field: 'kode_register', editor: 'input', width: 110},
        {title: 'Kode Barang', field: 'kode_barang_id', masterKey: 'barang', width: 240, ...listEditor(barang)},
        {title: 'Tahun', field: 'tahun_perolehan', editor: 'number', width: 90},
        {title: 'Nilai (Rp)', field: 'nilai_perolehan', editor: 'number', width: 120},
        {title: 'Asal Usul', field: 'spesifikasi', editor: 'input', width: 140},
        {title: 'Jenis Aset', field: 'jenis_aset', width: 200, ...enumEditor(['BUKU', 'BARANG BERCORAK KESENIAN', 'HEWAN & TUMBUHAN'])},
        {title: 'Judul Buku', field: 'judul_buku', editor: 'input', width: 280},
        {title: 'Pencipta', field: 'pencipta_buku', editor: 'input', width: 180},
        {title: 'Spesifikasi Buku', field: 'spesifikasi_buku', editor: 'input', width: 180},
        {title: 'Jumlah', field: 'jumlah_barang', editor: 'number', width: 90},
        {title: 'Satuan', field: 'satuan_barang_id', masterKey: 'satuan', width: 140, ...listEditor(satuan)},
        {title: 'Atribusi?', field: 'merupakan_atribusi', width: 110, ...enumEditor(['ya', 'tidak'])},
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
        {title: 'Tercatat Ganda', field: 'nibar_tercatat_ganda', editor: 'input', width: 140},
        {title: 'Deskripsi', field: 'deskripsi_barang', editor: 'input', width: 200},
        {title: 'Keterangan', field: 'keterangan', editor: 'input', width: 200},
        {title: 'Petugas', field: 'petugas', editor: 'input', width: 180},
        {
            title: 'Foto',
            field: 'foto',
            editor: false,
            width: 160,
            formatter: (cell) => {
                const value = cell.getValue();
                if (!value) return '';
                const safeValue = escapeHtml(value);
                return `<a href="${safeValue}" target="_blank" rel="noopener" class="text-emerald-700 underline decoration-emerald-300 hover:text-emerald-900">View photo</a>`;
            },
        },
    ];

    const table = new Tabulator('#grid', {
        data: [],
        layout: 'fitData',
        height: 'calc(100vh - 170px)',
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
                    status.textContent = 'Deleting...';
                    const r = await fetch(`/api/inventory/${row.getData().nibar}`, {method: 'DELETE'});
                    if (r.status === 204) {
                        row.delete();
                        status.textContent = 'Deleted';
                    } else {
                        status.textContent = 'Delete failed';
                        alert('Delete failed');
                    }
                },
            },
        ],
        cellEdited: async (cell) => {
            const data = cell.getRow().getData();
            const field = cell.getField();
            const value = cell.getValue();
            status.textContent = 'Saving...';
            status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-amber-50 text-amber-700 shadow-sm border border-amber-200';
            const r = await fetch(`/api/inventory/${data.nibar}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({[field]: value}),
            });
            if (!r.ok) {
                cell.restoreOldValue();
                const d = await r.json().catch(() => ({}));
                status.textContent = 'Save failed';
                status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-rose-50 text-rose-700 shadow-sm border border-rose-200';
                alert(d.error || `Update failed (${r.status})`);
                return;
            }
            status.textContent = 'Saved';
            status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-700 shadow-sm border border-emerald-200';
            setTimeout(() => {
                if (status.textContent === 'Saved') {
                    status.textContent = `${fmt.format(table.getDataCount())} rows`;
                    status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-white text-slate-600 shadow-sm border border-slate-200';
                }
            }, 1500);
        },
    });

    async function loadRows() {
        const queue = queueFilter.value;
        const q = filterInput.value.trim();
        const urlParams = new URLSearchParams();
        if (queue.startsWith('duplicates:')) {
            urlParams.set('duplicates', queue.replace('duplicates:', ''));
        } else if (queue) {
            urlParams.set('missing', queue);
        }
        if (q) urlParams.set('q', q);

        const newUrl = `${window.location.pathname}${urlParams.toString() ? `?${urlParams}` : ''}`;
        window.history.replaceState({}, '', newUrl);

        status.textContent = 'Loading...';
        status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-white text-slate-600 shadow-sm border border-slate-200';
        const items = [];
        let page = 1;
        let total = 0;
        while (true) {
            const pageParams = new URLSearchParams(urlParams);
            pageParams.set('per_page', '500');
            pageParams.set('page', String(page));
            const r = await fetch(`/api/inventory?${pageParams.toString()}`);
            const d = await r.json();
            items.push(...d.items);
            total = d.total;
            if (items.length >= d.total || !d.items.length) break;
            page += 1;
        }
        table.setData(items);
        if (savedState === 'created' || savedState === 'updated') {
            status.textContent = savedState === 'created' ? 'Entry created' : 'Entry updated';
            status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-700 shadow-sm border border-emerald-200';
        } else {
            status.textContent = `${fmt.format(total)} rows`;
            status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-white text-slate-600 shadow-sm border border-slate-200';
        }
        subtitle.textContent = queue
            ? `${queueLabels[queue] || queue} (${fmt.format(total)} rows)`
            : 'Full editable inventory grid';
    }

    let searchTimer;
    filterInput.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadRows, 250);
    });
    queueFilter.addEventListener('change', loadRows);
    reloadButton.addEventListener('click', loadRows);

    await loadRows();
})();

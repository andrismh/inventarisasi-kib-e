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
    const toast = (message, type = 'error') => {
        const el = document.createElement('div');
        el.className = 'fixed bottom-24 right-4 z-50 max-w-sm px-4 py-3 rounded-lg shadow-lg text-sm font-medium ' +
            (type === 'success' ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white');
        el.textContent = message;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 4000);
    };

    const isBlank = (value) =>
        value === null || value === undefined || String(value).trim() === '';

    const highlightBlanks = (row) => {
        const el = row.getElement();
        if (!el) return;
        const data = row.getData();
        el.querySelectorAll('.tabulator-cell').forEach((cellEl) => {
            const field = cellEl.getAttribute('tabulator-field');
            if (field && isBlank(data[field])) {
                cellEl.classList.add('kibe-blank-cell');
            } else {
                cellEl.classList.remove('kibe-blank-cell');
            }
        });
    };

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
    const labelSorter = (masterKey) => {
        const map = masterMaps[masterKey];
        return (a, b) => {
            const av = a == null ? '' : (map[a] != null ? map[a] : String(a));
            const bv = b == null ? '' : (map[b] != null ? map[b] : String(b));
            return av.localeCompare(bv, 'id', {numeric: true});
        };
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
        {title: 'NIBAR', field: 'nibar', frozen: true, width: 120, editor: false, sorter: 'number'},
        {title: 'Kode Reg.', field: 'kode_register', editor: 'input', width: 110, sorter: 'string'},
        {title: 'Kode Barang', field: 'kode_barang_id', masterKey: 'barang', width: 240, sorter: labelSorter('barang'), ...listEditor(barang)},
        {title: 'Tahun', field: 'tahun_perolehan', editor: 'number', width: 90, sorter: 'number'},
        {title: 'Nilai (Rp)', field: 'nilai_perolehan', editor: 'number', width: 120, sorter: 'number'},
        {title: 'Asal Usul', field: 'spesifikasi', editor: 'input', width: 140, sorter: 'string'},
        {title: 'Jenis Aset', field: 'jenis_aset', width: 200, sorter: 'string', ...enumEditor(['BUKU', 'BARANG BERCORAK KESENIAN', 'HEWAN & TUMBUHAN'])},
        {title: 'Judul Buku', field: 'judul_buku', editor: 'input', width: 280, sorter: 'string'},
        {title: 'Pencipta', field: 'pencipta_buku', editor: 'input', width: 180, sorter: 'string'},
        {title: 'Spesifikasi Buku', field: 'spesifikasi_buku', editor: 'input', width: 180, sorter: 'string'},
        {title: 'Jumlah', field: 'jumlah_barang', editor: 'number', width: 90, sorter: 'number'},
        {title: 'Satuan', field: 'satuan_barang_id', masterKey: 'satuan', width: 140, sorter: labelSorter('satuan'), ...listEditor(satuan)},
        {title: 'Atribusi?', field: 'merupakan_atribusi', width: 110, sorter: 'string', ...enumEditor(['ya', 'tidak'])},
        {title: 'Alamat', field: 'alamat', editor: 'input', width: 200, sorter: 'string'},
        {title: 'Koordinat', field: 'koordinat', editor: 'input', width: 160, sorter: 'string'},
        {title: 'Ruangan', field: 'ruangan_id', masterKey: 'ruang', width: 280, sorter: labelSorter('ruang'), ...listEditor(ruang, true)},
        {title: 'Kondisi', field: 'kondisi_barang_id', masterKey: 'kondisi', width: 160, sorter: labelSorter('kondisi'), ...listEditor(kondisi)},
        {title: 'Merk/Type', field: 'merk_type', editor: 'input', width: 160, sorter: 'string'},
        {title: 'Penggunaan', field: 'penggunaan', width: 200, sorter: 'string', ...enumEditor(['pemerintah daerah', 'pemerintah pusat', 'pemerintah daerah lainnya', 'pihak lain'])},
        {title: 'Nama Kuasa', field: 'nama_kuasa', editor: 'input', width: 160, sorter: 'string'},
        {title: 'Nama Pemakai', field: 'nama_pemakai', editor: 'input', width: 160, sorter: 'string'},
        {title: 'Status Pemakai', field: 'status_pemakai', editor: 'input', width: 140, sorter: 'string'},
        {title: 'BAST', field: 'bast', width: 90, sorter: 'string', ...enumEditor(['ada', 'tidak'])},
        {title: 'Tercatat Ganda', field: 'nibar_tercatat_ganda', editor: 'input', width: 140, sorter: 'string'},
        {title: 'Deskripsi', field: 'deskripsi_barang', editor: 'input', width: 200, sorter: 'string'},
        {title: 'Keterangan', field: 'keterangan', editor: 'input', width: 200, sorter: 'string'},
        {title: 'Petugas', field: 'petugas', editor: 'input', width: 180, sorter: 'string'},
        {
            title: 'Foto',
            field: 'foto',
            editor: false,
            width: 160,
            sorter: 'string',
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
        headerSort: true,
        pagination: true,
        paginationSize: 50,
        paginationSizeSelector: [25, 50, 100, 200],
        rowFormatter: highlightBlanks,
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
                        toast('Delete failed');
                    }
                },
            },
        ],
        cellEdited: async (cell) => {
            const row = cell.getRow();
            const data = row.getData();
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
                toast(d.error || `Update failed (${r.status})`);
                return;
            }
            status.textContent = 'Saved';
            status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-700 shadow-sm border border-emerald-200';

            // Live queue trimming: filling the exact queued field removes the row
            // from a single-field "missing" view immediately; otherwise refresh
            // the blank-cell highlight.
            const queue = queueFilter.value;
            if (queue && !queue.startsWith('duplicates:') && queue !== 'all_optional') {
                if (!isBlank(value) && field === queue) {
                    row.delete();
                    status.textContent = `Saved — left in queue (${fmt.format(table.getDataCount())} rows)`;
                    updateSubtitle();
                    return;
                }
            }
            highlightBlanks(row);

            setTimeout(() => {
                if (status.textContent === 'Saved') {
                    status.textContent = `${fmt.format(table.getDataCount())} rows`;
                    status.className = 'text-sm font-medium px-4 py-1.5 rounded-full bg-white text-slate-600 shadow-sm border border-slate-200';
                }
            }, 1500);
        },
    });

    async function loadRows() {
        lastActiveRow = null;
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

    function updateSubtitle() {
        const queue = queueFilter.value;
        subtitle.textContent = queue
            ? `${queueLabels[queue] || queue} (${fmt.format(table.getDataCount())} rows)`
            : 'Full editable inventory grid';
    }

    let lastActiveRow = null;
    table.on('rowClick', (e, row) => { lastActiveRow = row; });

    function firstBlankField(row) {
        const data = row.getData();
        for (const col of table.getColumnDefinitions()) {
            const f = col.field;
            if (!f || col.editor === false) continue;
            if (isBlank(data[f])) return f;
        }
        return null;
    }

    async function nextBlank() {
        const rows = table.getRows('active');
        if (!rows.length) return;
        const start = lastActiveRow ? Math.max(rows.indexOf(lastActiveRow), 0) + 1 : 0;
        for (let pass = 0; pass < 2; pass++) {
            const begin = pass === 0 ? start : 0;
            for (let i = begin; i < rows.length; i++) {
                const field = firstBlankField(rows[i]);
                if (!field) continue;
                const cell = rows[i].getCell(field);
                if (!cell) continue;
                lastActiveRow = rows[i];
                try {
                    await rows[i].scrollTo();
                } catch (e) {
                    console.warn('Tidak dapat menggulir ke sel kosong.', e);
                }
                cell.edit();
                return;
            }
        }
        toast('Tidak ada lagi sel kosong yang tersisa.', 'success');
    }

    document.getElementById('next-blank').addEventListener('click', () => { void nextBlank(); });
    document.addEventListener('keydown', (e) => {
        if ((e.altKey || e.ctrlKey) && (e.key === 'n' || e.key === 'N')) {
            e.preventDefault();
            void nextBlank();
        }
    });

    await loadRows();
})();

(async () => {
    const loading = document.getElementById('dashboard-loading');
    const content = document.getElementById('dashboard-content');
    const fmt = new Intl.NumberFormat('id-ID');

    const labels = {
        spesifikasi: 'Asal Usul',
        judul_buku: 'Judul Buku',
        pencipta_buku: 'Pencipta Buku',
        spesifikasi_buku: 'Spesifikasi Buku',
        merupakan_atribusi: 'Merupakan Atribusi',
        alamat: 'Alamat',
        koordinat: 'Koordinat',
        ruangan_id: 'Ruangan',
        merk_type: 'Merk / Type',
        penggunaan: 'Penggunaan',
        nama_kuasa: 'Nama Kuasa',
        nama_pemakai: 'Nama Pemakai',
        status_pemakai: 'Status Pemakai',
        bast: 'BAST',
        nibar_tercatat_ganda: 'NIBAR Tercatat Ganda',
        deskripsi_barang: 'Deskripsi Barang',
        keterangan: 'Keterangan',
        petugas: 'Petugas',
        foto: 'Foto',
    };

    const editorUrl = (params) => `/master?${new URLSearchParams(params).toString()}`;

    function queueRow(title, detail, count, href) {
        const disabled = count === 0;
        const a = document.createElement('a');
        a.href = disabled ? '#' : href;
        a.className = `flex items-center justify-between px-5 py-4 transition-colors ${disabled ? 'cursor-default text-slate-400' : 'hover:bg-emerald-50 text-slate-800'}`;
        a.innerHTML = `
            <span>
                <span class="block font-medium">${title}</span>
                <span class="block text-sm text-slate-500 mt-0.5">${detail}</span>
            </span>
            <span class="text-lg font-bold ${disabled ? 'text-slate-300' : 'text-emerald-700'}">${fmt.format(count)}</span>
        `;
        if (disabled) a.addEventListener('click', (e) => e.preventDefault());
        return a;
    }

    try {
        const res = await fetch('/api/inventory/stats');
        if (!res.ok) throw new Error(`Stats failed (${res.status})`);
        const stats = await res.json();
        const rate = stats.total ? Math.round((stats.complete / stats.total) * 100) : 0;

        document.getElementById('stat-total').textContent = fmt.format(stats.total);
        document.getElementById('stat-complete').textContent = fmt.format(stats.complete);
        document.getElementById('stat-incomplete').textContent = fmt.format(stats.incomplete);
        document.getElementById('stat-rate').textContent = `${rate}%`;

        const queueList = document.getElementById('queue-list');
        queueList.appendChild(queueRow(
            'Complete missing data',
            'Rows with at least one optional field still blank.',
            stats.queues.all_optional,
            editorUrl({missing: 'all_optional'})
        ));
        queueList.appendChild(queueRow(
            'Blank title',
            'Assets that still need Judul Buku.',
            stats.queues.blank_title,
            editorUrl({missing: 'judul_buku'})
        ));
        queueList.appendChild(queueRow(
            'Duplicate title risk',
            'Rows sharing a repeated title.',
            stats.queues.duplicate_risk,
            editorUrl({duplicates: 'judul_buku'})
        ));

        const fieldList = document.getElementById('missing-field-list');
        Object.entries(stats.missing_fields)
            .sort((a, b) => b[1] - a[1])
            .forEach(([field, count]) => {
                const item = document.createElement('a');
                item.href = editorUrl({missing: field});
                item.className = 'bg-white px-5 py-4 hover:bg-emerald-50 transition-colors';
                item.innerHTML = `
                    <div class="text-sm font-medium text-slate-800">${labels[field] || field}</div>
                    <div class="text-2xl font-bold text-slate-900 mt-1">${fmt.format(count)}</div>
                    <div class="text-xs text-slate-500 mt-1">missing rows</div>
                `;
                fieldList.appendChild(item);
            });

        loading.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (error) {
        loading.className = 'bg-rose-50 rounded-lg border border-rose-200 shadow-sm p-6 text-sm text-rose-800';
        loading.textContent = error.message || 'Unable to load dashboard stats.';
    }
})();

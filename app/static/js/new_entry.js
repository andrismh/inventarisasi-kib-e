(async () => {
    // Populate master-driven selects
    const selects = document.querySelectorAll('select[data-master]');
    const types = [...new Set([...selects].map(s => s.dataset.master))];
    const cache = {};
    await Promise.all(types.map(async (t) => {
        const r = await fetch(`/api/masters/${t}`);
        cache[t] = await r.json();
    }));
    selects.forEach((sel) => {
        const opts = cache[sel.dataset.master];
        if (sel.dataset.allowEmpty) {
            const opt = document.createElement('option');
            opt.value = ''; opt.textContent = '—';
            sel.appendChild(opt);
        } else {
            const opt = document.createElement('option');
            opt.value = ''; opt.textContent = '— pilih —'; opt.disabled = true; opt.selected = true;
            sel.appendChild(opt);
        }
        opts.forEach(o => {
            const opt = document.createElement('option');
            opt.value = o.id; opt.textContent = o.nama;
            sel.appendChild(opt);
        });
    });

    // Initialize TomSelect on all selects
    document.querySelectorAll('select').forEach(sel => {
        sel.tomselect = new TomSelect(sel, {
            create: false,
            maxOptions: 100,
            sortField: {field: "text", direction: "asc"}
        });
    });

    let currentEditNibar = null;
    const form = document.getElementById('entry-form');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const btnSubmit = document.getElementById('btn-submit');
    const btnReset = document.getElementById('btn-reset');
    const nibarInput = document.querySelector('input[name="nibar"]');
    const params = new URLSearchParams(window.location.search);
    const fotoInput = document.getElementById('foto-input');
    const fotoPathInput = document.getElementById('foto-path');
    const fotoPreview = document.getElementById('foto-preview');
    const fotoPlaceholder = document.getElementById('foto-placeholder');
    const fotoStatus = document.getElementById('foto-status');
    const fotoDisabledHint = document.getElementById('foto-disabled-hint');
    const btnPickFoto = document.getElementById('btn-pick-foto');
    const btnUploadFoto = document.getElementById('btn-upload-foto');
    let selectedFotoFile = null;

    function setFotoPreview(src) {
        if (src) {
            fotoPreview.src = src;
            fotoPreview.classList.remove('hidden');
            fotoPlaceholder.classList.add('hidden');
        } else {
            fotoPreview.removeAttribute('src');
            fotoPreview.classList.add('hidden');
            fotoPlaceholder.classList.remove('hidden');
        }
    }

    function setFotoControls(enabled, fotoUrl = '') {
        fotoPathInput.value = fotoUrl || '';
        btnPickFoto.disabled = !enabled;
        btnUploadFoto.disabled = !enabled || !selectedFotoFile;
        fotoDisabledHint.textContent = enabled
            ? 'Ambil foto dari kamera ponsel atau pilih dari galeri, lalu upload.'
            : 'Simpan atau load NIBAR terlebih dahulu sebelum mengambil foto.';
        if (fotoUrl) {
            setFotoPreview(fotoUrl);
            fotoStatus.textContent = `Foto tersimpan: ${fotoUrl}`;
        } else if (!selectedFotoFile) {
            setFotoPreview('');
            fotoStatus.textContent = enabled ? 'Belum ada foto tersimpan.' : '';
        }
    }

    async function loadEntry(nibar) {
        if (!nibar) return;
        try {
            const r = await fetch('/api/inventory/' + nibar);
            if (r.ok) {
                const data = await r.json();
                currentEditNibar = data.nibar;
                pageTitle.textContent = 'Edit Entry';
                pageSubtitle.textContent = `Editing NIBAR: ${data.nibar} - ${data.judul_buku || ''}`;
                btnSubmit.textContent = 'Update Entry';
                btnReset.classList.remove('hidden');
                nibarInput.readOnly = true;
                nibarInput.classList.add('bg-slate-100', 'cursor-not-allowed', 'text-slate-500');
                
                // Populate form
                for (const [key, value] of Object.entries(data)) {
                    const el = form.elements[key];
                    if (el) {
                        if (el.tomselect) {
                            el.tomselect.setValue(value !== null ? String(value) : '');
                        } else {
                            el.value = value !== null ? value : '';
                        }
                    }
                }
                selectedFotoFile = null;
                fotoInput.value = '';
                setFotoControls(true, data.foto || '');
                document.querySelectorAll('ul[data-similar-list]').forEach(ul => ul.innerHTML = '');
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        } catch (e) {
            console.error("Failed to load entry", e);
        }
    }

    btnReset.addEventListener('click', () => {
        currentEditNibar = null;
        pageTitle.textContent = 'Add / Edit Item';
        pageSubtitle.textContent = 'Add a new inventory item or load an existing NIBAR for focused editing';
        btnSubmit.textContent = 'Save Entry';
        btnReset.classList.add('hidden');
        nibarInput.readOnly = false;
        nibarInput.classList.remove('bg-slate-100', 'cursor-not-allowed', 'text-slate-500');
        form.reset();
        selectedFotoFile = null;
        fotoInput.value = '';
        setFotoControls(false);
        document.querySelectorAll('select').forEach(sel => {
            if (sel.tomselect) sel.tomselect.clear();
        });
        document.querySelectorAll('ul[data-similar-list]').forEach(ul => ul.innerHTML = '');
    });

    nibarInput.addEventListener('blur', () => {
        if (!currentEditNibar && nibarInput.value) {
            loadEntry(nibarInput.value);
        }
    });

    if (params.get('nibar')) {
        await loadEntry(params.get('nibar'));
        if (params.get('saved') === 'created') {
            fotoStatus.textContent = 'Entry created. You can upload a photo now.';
        } else if (params.get('saved') === 'updated') {
            fotoStatus.textContent = 'Entry updated. You can replace the photo if needed.';
        }
    } else {
        setFotoControls(false);
    }

    btnPickFoto.addEventListener('click', () => {
        if (!currentEditNibar) return;
        fotoInput.click();
    });

    fotoInput.addEventListener('change', () => {
        selectedFotoFile = fotoInput.files && fotoInput.files[0] ? fotoInput.files[0] : null;
        if (!selectedFotoFile) {
            setFotoControls(Boolean(currentEditNibar), fotoPathInput.value);
            return;
        }
        const previewUrl = URL.createObjectURL(selectedFotoFile);
        setFotoPreview(previewUrl);
        fotoStatus.textContent = `Ready to upload: ${selectedFotoFile.name}`;
        btnUploadFoto.disabled = !currentEditNibar;
    });

    btnUploadFoto.addEventListener('click', async () => {
        if (!currentEditNibar || !selectedFotoFile) return;
        fotoStatus.textContent = 'Uploading photo...';
        btnUploadFoto.disabled = true;
        const uploadData = new FormData();
        uploadData.append('foto', selectedFotoFile);
        const r = await fetch(`/api/inventory/${currentEditNibar}/foto`, {
            method: 'POST',
            body: uploadData,
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) {
            fotoStatus.textContent = data.error || `Photo upload failed (${r.status})`;
            btnUploadFoto.disabled = false;
            return;
        }
        selectedFotoFile = null;
        fotoInput.value = '';
        setFotoControls(true, data.foto || '');
    });

    // Similar-name lookup
    const debounce = (fn, ms) => {
        let t;
        return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
    };

    document.querySelectorAll('input[data-similar]').forEach((input) => {
        const field = input.dataset.similar;
        const list = document.querySelector(`ul[data-similar-list="${field}"]`);
        const lookup = debounce(async () => {
            if (currentEditNibar && field === 'nibar') return; // Skip lookup if editing and on nibar
            const q = input.value.trim();
            list.innerHTML = '';
            if (q.length < 2) return;
            const r = await fetch(`/api/inventory/search?q=${encodeURIComponent(q)}&field=${field}&limit=10`);
            const d = await r.json();
            if (!d.matches || !d.matches.length) return;
            const header = document.createElement('li');
            header.className = 'text-amber-700 font-medium';
            header.textContent = 'Item serupa sudah tercatat (Klik untuk edit):';
            list.appendChild(header);
            d.matches.forEach(m => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = '#';
                a.className = 'hover:text-emerald-600 underline decoration-slate-300 hover:decoration-emerald-500 transition-colors cursor-pointer';
                a.textContent = `${m.nibar} — ${m.judul_buku ?? ''}`;
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    loadEntry(m.nibar);
                });
                li.appendChild(a);
                list.appendChild(li);
            });
        }, 250);
        input.addEventListener('input', lookup);
    });

    // Submit
    const errBox = document.getElementById('form-error');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errBox.classList.add('hidden');
        const fd = new FormData(form);
        const payload = {};
        fd.forEach((v, k) => {
            if (v === '' || v === null) return;
            payload[k] = v;
        });
        
        const method = currentEditNibar ? 'PATCH' : 'POST';
        const url = currentEditNibar ? `/api/inventory/${currentEditNibar}` : '/api/inventory';
        
        const r = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
        });
        
        if (r.status === 201 || (r.status === 200 && currentEditNibar)) {
            const nibar = currentEditNibar || payload.nibar;
            const saved = currentEditNibar ? 'updated' : 'created';
            window.location.href = `/entry?nibar=${encodeURIComponent(nibar)}&saved=${saved}`;
            return;
        }
        const data = await r.json().catch(() => ({}));
        errBox.classList.remove('hidden');
        if (data.details) {
            errBox.innerHTML = '<strong>' + (data.error || 'Error') + '</strong><br>' +
                Object.entries(data.details).map(([k, v]) => `${k}: ${v.join(', ')}`).join('<br>');
        } else {
            errBox.textContent = data.error || `Error ${r.status}`;
        }
        window.scrollTo({top: errBox.offsetTop - 80, behavior: 'smooth'});
    });
})();

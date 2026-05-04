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
                document.querySelectorAll('ul[data-similar-list]').forEach(ul => ul.innerHTML = '');
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        } catch (e) {
            console.error("Failed to load entry", e);
        }
    }

    btnReset.addEventListener('click', () => {
        currentEditNibar = null;
        pageTitle.textContent = 'New Entry';
        pageSubtitle.textContent = 'Add a new inventory item';
        btnSubmit.textContent = 'Save Entry';
        btnReset.classList.add('hidden');
        nibarInput.readOnly = false;
        nibarInput.classList.remove('bg-slate-100', 'cursor-not-allowed', 'text-slate-500');
        form.reset();
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
            window.location.href = '/';
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

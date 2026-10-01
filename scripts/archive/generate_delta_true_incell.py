#!/usr/bin/env python
"""Generate delta true in-cell Excel with only new updated NIBARs (248)."""
import pathlib, sqlite3, tempfile, shutil, re, zipfile, io
from openpyxl import load_workbook
from PIL import Image as PILImage
import place_in_cell as pic

TEMPLATE = pathlib.Path("Format_Excel_KIBE.xlsx")
BASE_NOIMG = pathlib.Path("Format_Excel_KIBE_base_noimg.xlsx")  # already has 38 cols, no images
OUT = pathlib.Path("Format_Excel_KIBE_v2_delta_true_incell.xlsx")
DB_PATH = pathlib.Path("instance/inventory.db")
BAK_DB = pathlib.Path("instance/inventory.db.bak")
FOTO_DIR = pathlib.Path("app/static/foto")

# Determine delta NIBARs: those with foto in current but not in backup
cur_db = sqlite3.connect(str(DB_PATH))
bak_db = sqlite3.connect(str(BAK_DB))
cur_fotos = set(r[0] for r in cur_db.execute('SELECT nibar FROM inventory_item WHERE foto IS NOT NULL').fetchall())
bak_fotos = set(r[0] for r in bak_db.execute('SELECT nibar FROM inventory_item WHERE foto IS NOT NULL').fetchall())
delta_nibars = sorted(cur_fotos - bak_fotos)
print(f"Delta fotos: {len(delta_nibars)} (cur {len(cur_fotos)} - bak {len(bak_fotos)})")
# If user meant all changed rows, we could use a broader set, but foto delta is the clearest new updated set
# Use this delta

# Also include any NIBAR where other fields changed and now have complete required fields?
# For now, use delta_fotos as the new updated set

# Load base template (use the base_noimg which already has correct header/cols/validations but no data)
# Instead, load TEMPLATE and rebuild data from scratch for delta only
# Simpler: start from BASE_NOIMG (which has empty data rows? Actually base_noimg has 0 data rows after clearing, but we cleared earlier to have no data)
# Let's load TEMPLATE directly to preserve masters and validations correctly
wb = load_workbook(str(TEMPLATE))
ws = wb["Worksheet"]
print(f"Template: {ws.max_row} rows, header at 12, cols {ws.max_column}")

# Clear existing data rows 13:max_row (keep rows 1-12)
if ws.max_row >= 13:
    ws.delete_rows(13, ws.max_row - 12)
print(f"After clear: {ws.max_row} rows")

# Prepare DB lookups
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()
masters = {}
for tbl in ["master_barang","master_satuan","master_ruang","master_kondisi"]:
    cur.execute(f"SELECT id, nama FROM {tbl}")
    masters[tbl] = {r["id"]: r["nama"] for r in cur.fetchall()}

# For each delta NIBAR, append a row
# Need to map DB fields to 38 cols as before (skip 10-14 new cols)
# Use same logic as scripts_export_v2.py but only for delta
from openpyxl.utils import get_column_letter

row_idx = 13
for nibar in delta_nibars:
    cur.execute("SELECT * FROM inventory_item WHERE nibar=?", (nibar,))
    db = dict(cur.fetchone())
    # Fetch masters
    kode_barang = masters["master_barang"].get(db["kode_barang_id"])
    satuan = masters["master_satuan"].get(db["satuan_barang_id"])
    ruangan = masters["master_ruang"].get(db["ruangan_id"])
    kondisi = masters["master_kondisi"].get(db["kondisi_barang_id"])
    # Write row
    # Cols: 0 Nibar,1 Kode Register,2 Kode Barang,3 Tahun,4 Nilai,5 Asal Usul,6 Jenis,7 Judul,8 Pencipta,9 Spes Buku,10-14 new empty,15 Jumlah,16 Satuan,17 Status,18 Jml,19 Atribusi,20 NibarAtr,21 Alamat,22 Koordinat,23 Ruangan,24 Kondisi,25 Merk,26 Penggunaan,27 Kuasa,28 Pemakai,29 Status Pemakai,30 BAST,31 Nama Dasar,32 Dokumen,33 Ganda,34 Deskripsi,35 Keterangan,36 Petugas,37 Foto(empty)
    values = [
        str(db["nibar"]),  # 0
        db["kode_register"],  # 1
        kode_barang,  # 2
        db["tahun_perolehan"],  # 3
        db["nilai_perolehan"],  # 4
        db["spesifikasi"],  # 5
        db["jenis_aset"],  # 6
        db["judul_buku"],  # 7
        db["pencipta_buku"],  # 8
        db["spesifikasi_buku"],  # 9
        None,  # 10 Asal Daerah
        None,  # 11 Pencipta Barang
        None,  # 12 Bahan
        None,  # 13 Jenis Hewan (keep None, except 1422257 would be Taman but not in delta)
        None,  # 14 Ukuran
        db["jumlah_barang"],  # 15
        satuan,  # 16
        db["status_keberadaan"],  # 17
        db["jml_keberadaan"],  # 18
        db["merupakan_atribusi"],  # 19
        db["nibar_atribusi"],  # 20
        db["alamat"],  # 21
        db["koordinat"],  # 22
        ruangan,  # 23
        kondisi,  # 24
        db["merk_type"],  # 25
        db["penggunaan"],  # 26
        db["nama_kuasa"],  # 27
        db["nama_pemakai"],  # 28
        db["status_pemakai"],  # 29
        db["bast"],  # 30
        db["nama_dasar_penggunaan"],  # 31
        db["nama_dokumen"],  # 32
        db["nibar_tercatat_ganda"],  # 33 will be 'tidak' but external expects blank - keep as is for now, will be blank in true incell? Actually we will keep as is
        db["deskripsi_barang"],  # 34
        db["keterangan"],  # 35
        db["petugas"],  # 36
        None,  # 37 Foto text empty, image only
    ]
    for col_idx, val in enumerate(values):
        cell = ws.cell(row=row_idx, column=col_idx+1, value=val)
        if col_idx in (0,1):
            cell.number_format = '@'
        # Keep header style? Not needed
    # Set row height for image rows
    ws.row_dimensions[row_idx].height = 45
    row_idx += 1

print(f"Wrote {len(delta_nibars)} delta rows, new max_row {ws.max_row}")

# Adjust column AL width for images
ws.column_dimensions["AL"].width = 15

# Validations keep original 13:1644 range (covers delta 13:260, no need to shrink)

# Clear existing images (template has none, but just in case)
ws._images = []

# Save intermediate without images
tmp_base = pathlib.Path("Format_Excel_KIBE_delta_base.xlsx")
wb.save(str(tmp_base))
print(f"Saved delta base {tmp_base} with {ws.max_row} rows")
conn.close()
wb.close()

# Now inject true in-cell images for delta rows
# Reuse inject logic but for delta
import tempfile, shutil, zipfile, io
from pathlib import Path as P

# Build image list for delta
# Need nibar -> row mapping for delta
wb2 = load_workbook(str(tmp_base))
ws2 = wb2["Worksheet"]
nibar_to_row = {}
for r in range(13, ws2.max_row+1):
    val = ws2.cell(row=r, column=1).value
    if val is None:
        continue
    try:
        n = int(str(val).strip())
        nibar_to_row[n] = r
    except:
        pass
wb2.close()

# Prepare compressed temp images and all_entries
tmpdir = pathlib.Path(tempfile.mkdtemp())
all_entries = []
for nibar in delta_nibars:
    # Find foto path
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT foto FROM inventory_item WHERE nibar=?", (nibar,))
    foto = cur.fetchone()[0]
    conn.close()
    if not foto:
        continue
    fname = pathlib.Path(foto).name
    src = FOTO_DIR / fname
    if not src.exists():
        continue
    dst = tmpdir / fname
    with PILImage.open(src) as im:
        if im.mode in ("RGBA","LA","P"):
            im = im.convert("RGB")
        im.thumbnail((400,400), PILImage.LANCZOS)
        im.save(dst, format="JPEG", quality=80, optimize=True)
    r = nibar_to_row.get(nibar)
    if not r:
        continue
    cell = f"AL{r}"
    all_entries.append((cell, str(dst)))

print(f"Prepared {len(all_entries)} compressed images for true in-cell")

# Now inject using place_in_cell helpers
# Read base delta as zip
with zipfile.ZipFile(tmp_base, 'r') as zin:
    base_files = {name: zin.read(name) for name in zin.namelist()}

# Prepare pic images list for helper
pic_images = [{"cell": cell, "image": path} for cell, path in all_entries]
# Generate entries for helper
helper_entries = []
for item in pic_images:
    col, row = pic._parse_cell(item["cell"])
    helper_entries.append(("local", {"col": col, "row": row, "path": item["image"], "ext": pic._ext(item["image"])}))

# Update [Content_Types].xml
orig_ct = base_files["[Content_Types].xml"].decode()
new_ct_additions = []
if 'Extension="jpg"' not in orig_ct:
    new_ct_additions.append('  <Default Extension="jpg" ContentType="image/jpeg"/>')
if 'Extension="jpeg"' not in orig_ct:
    new_ct_additions.append('  <Default Extension="jpeg" ContentType="image/jpeg"/>')
overrides_needed = [
    ('/xl/metadata.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml'),
    ('/xl/richData/rdrichvalue.xml', 'application/vnd.ms-excel.rdrichvalue+xml'),
    ('/xl/richData/rdrichvaluestructure.xml', 'application/vnd.ms-excel.rdrichvaluestructure+xml'),
    ('/xl/richData/rdRichValueTypes.xml', 'application/vnd.ms-excel.rdrichvaluetypes+xml'),
    ('/xl/richData/richValueRel.xml', 'application/vnd.ms-excel.richvaluerel+xml'),
]
for part, ctype in overrides_needed:
    if part not in orig_ct:
        new_ct_additions.append(f'  <Override PartName="{part}" ContentType="{ctype}"/>')
if new_ct_additions:
    ct_new = orig_ct.replace("</Types>", "\n".join(new_ct_additions) + "\n</Types>")
    base_files["[Content_Types].xml"] = ct_new.encode()

# Update xl/_rels/workbook.xml.rels
orig_rels = base_files["xl/_rels/workbook.xml.rels"].decode()
existing_ids = re.findall(r'Id="rId(\d+)"', orig_rels)
max_rid = max(int(x) for x in existing_ids) if existing_ids else 0
next_id = max_rid + 1
rel_targets = [
    (f"rId{next_id}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata", "metadata.xml"),
    (f"rId{next_id+1}", "http://schemas.microsoft.com/office/2017/06/relationships/rdRichValue", "richData/rdrichvalue.xml"),
    (f"rId{next_id+2}", "http://schemas.microsoft.com/office/2017/06/relationships/rdRichValueStructure", "richData/rdrichvaluestructure.xml"),
    (f"rId{next_id+3}", "http://schemas.microsoft.com/office/2017/06/relationships/rdRichValueTypes", "richData/rdRichValueTypes.xml"),
    (f"rId{next_id+4}", "http://schemas.microsoft.com/office/2022/10/relationships/richValueRel", "richData/richValueRel.xml"),
]
rel_lines = "\n".join(f'  <Relationship Id="{rid}" Type="{typ}" Target="{tgt}"/>' for rid, typ, tgt in rel_targets)
rels_new = orig_rels.replace("</Relationships>", rel_lines + "\n</Relationships>")
base_files["xl/_rels/workbook.xml.rels"] = rels_new.encode()

# Generate richData files
base_files["xl/metadata.xml"] = pic._metadata(len(helper_entries)).encode()
base_files["xl/richData/rdrichvaluestructure.xml"] = pic._rich_struct(True, False).encode()
base_files["xl/richData/rdRichValueTypes.xml"] = pic._RICH_TYPES.encode()
base_files["xl/richData/rdrichvalue.xml"] = pic._rich_values(helper_entries).encode()
base_files["xl/richData/richValueRel.xml"] = pic._rich_value_rel_xml(len([e for k,e in helper_entries if k=="local"])).encode()
base_files["xl/richData/_rels/richValueRel.xml.rels"] = pic._rich_value_rel_rels(helper_entries).encode()

# Add media
for idx, (kind, entry) in enumerate(helper_entries):
    if kind == "local":
        local_idx = sum(1 for k,_ in helper_entries[:idx] if k=="local")
        media_name = f"xl/media/image{local_idx+1}.{entry['ext']}"
        with open(entry["path"], "rb") as f:
            base_files[media_name] = f.read()

# Patch sheet1.xml to add image cells
sheet_xml = base_files["xl/worksheets/sheet1.xml"].decode()
cell_to_vm = {}
for vm_idx, (kind, entry) in enumerate(helper_entries):
    cell = f"{entry['col']}{entry['row']}"
    cell_to_vm[cell] = vm_idx

from collections import defaultdict
row_to_cells = defaultdict(list)
for cell, vm in cell_to_vm.items():
    m = re.match(r"([A-Z]+)(\d+)", cell)
    col, row = m.group(1), int(m.group(2))
    row_to_cells[row].append((col, vm))

def patch_sheet(sheet_xml, row_to_cells):
    for row_num, cells in sorted(row_to_cells.items()):
        pattern = re.compile(rf'(<row r="{row_num}"[^>]*>)(.*?)(</row>)', re.DOTALL)
        m = pattern.search(sheet_xml)
        if not m:
            continue
        start, inner, end = m.groups()
        for col, vm in sorted(cells, key=lambda x: pic._col_num(x[0])):
            new_cell = f'<c r="{col}{row_num}" t="e" vm="{vm}"><v>#VALUE!</v></c>'
            inner = inner + new_cell
        new_row = start + inner + end
        sheet_xml = sheet_xml.replace(m.group(0), new_row, 1)
    return sheet_xml

sheet_patched = patch_sheet(sheet_xml, row_to_cells)
base_files["xl/worksheets/sheet1.xml"] = sheet_patched.encode()

# Write final delta true incell
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in base_files.items():
        zout.writestr(name, data)

print(f"Saved delta true in-cell to {OUT} with {len(helper_entries)} images, rows {len(delta_nibars)}")
shutil.rmtree(tmpdir)
# Cleanup tmp base
# pathlib.Path(tmp_base).unlink()
print("Done")

#!/usr/bin/env python
"""Inject true Place-in-Cell images into existing base workbook."""
import io, os, re, zipfile, pathlib, sqlite3, tempfile, shutil
from PIL import Image as PILImage

# Import helpers from place_in_cell
import place_in_cell as pic

BASE = pathlib.Path("Format_Excel_KIBE_base_noimg.xlsx")
OUT = pathlib.Path("Format_Excel_KIBE_v2_true_incell.xlsx")
DB_PATH = pathlib.Path("instance/inventory.db")
FOTO_DIR = pathlib.Path("app/static/foto")

# 1. Build image list
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()
# Need mapping nibar -> excel row number
from openpyxl import load_workbook
wb_tmp = load_workbook(str(BASE), read_only=True, data_only=True)
ws_tmp = wb_tmp["Worksheet"]
nibar_to_row = {}
for row in ws_tmp.iter_rows(min_row=13, values_only=True):
    if row[0] is None:
        continue
    try:
        n = int(str(row[0]).strip())
        # Find row number by scanning again with openpyxl's worksheet dimensions? Use enumerate
        pass
    except:
        pass
wb_tmp.close()

# Better: use openpyxl read_only=False to get row numbers
wb2 = load_workbook(str(BASE))
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

# Build images list for place-in-cell
images = []
tmpdir = pathlib.Path(tempfile.mkdtemp())
print(f"Tmp dir {tmpdir}")
# Get DB foto mapping
cur.execute("SELECT nibar, foto FROM inventory_item WHERE foto IS NOT NULL ORDER BY nibar")
for nibar, foto in cur.fetchall():
    r = nibar_to_row.get(nibar)
    if not r:
        continue
    fname = pathlib.Path(foto).name
    src = FOTO_DIR / fname
    if not src.exists():
        continue
    # Compress
    dst = tmpdir / fname
    with PILImage.open(src) as im:
        if im.mode in ("RGBA","LA","P"):
            im = im.convert("RGB")
        im.thumbnail((400,400), PILImage.LANCZOS)
        im.save(dst, format="JPEG", quality=80, optimize=True)
    cell = f"AL{r}"
    images.append({"cell": cell, "image": str(dst), "nibar": nibar, "row": r})
    # print first few
    if len(images) <= 3:
        print(f"Image {nibar} -> {cell} {dst}")

print(f"Total images to embed {len(images)}")

# Sort by row for vm order
images_sorted = sorted(images, key=lambda x: x["row"])
# For place_in_cell helpers, need list of dicts with cell and image
pic_images = [{"cell": img["cell"], "image": img["image"]} for img in images_sorted]

# 2. Generate XML for new parts using place_in_cell helpers
# We will reuse internal helpers but need to handle existing workbook's other sheets
# Create the XML strings as place_in_cell does
# Use its internal functions via import
from place_in_cell import _metadata, _rich_struct, _rich_values, _rich_value_rel_xml, _rich_value_rel_rels, _content_types, _workbook_rels

# Generate needed XML
all_entries = []
for item in pic_images:
    col, row = pic._parse_cell(item["cell"])
    all_entries.append(("local", {"col": col, "row": row, "path": item["image"], "ext": pic._ext(item["image"])}))

# For content types and workbook rels we need has_local/has_web
has_local = True
has_web = False

# 3. Patch the base zip
# Read base zip contents
with zipfile.ZipFile(BASE, 'r') as zin:
    base_files = {name: zin.read(name) for name in zin.namelist()}

# Prepare new content
# Update [Content_Types].xml
orig_ct = base_files["[Content_Types].xml"].decode()
# Generate new CT via helper for all_entries, but we need to merge with existing
# The helper's _content_types generates a full file with only the new parts + image exts
# Instead, we will add the missing entries manually via string manipulation
# Add Default for jpeg (if not present) and Overrides for richData parts
new_ct_additions = []
# Check if jpeg default exists
if 'Extension="jpeg"' not in orig_ct and 'Extension="jpg"' not in orig_ct:
    new_ct_additions.append('  <Default Extension="jpg" ContentType="image/jpeg"/>')
    new_ct_additions.append('  <Default Extension="jpeg" ContentType="image/jpeg"/>')
# Add Overrides for new parts if not present
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

# Insert before </Types>
if new_ct_additions:
    ct_new = orig_ct.replace("</Types>", "\n".join(new_ct_additions) + "\n</Types>")
else:
    ct_new = orig_ct
base_files["[Content_Types].xml"] = ct_new.encode()

# Update xl/_rels/workbook.xml.rels
orig_rels = base_files["xl/_rels/workbook.xml.rels"].decode()
# Parse existing rIds to find max
import re
existing_ids = re.findall(r'Id="rId(\d+)"', orig_rels)
max_rid = max(int(x) for x in existing_ids) if existing_ids else 0
# Add new relationships for richData
new_rels = []
# The workbook rels in place_in_cell adds 4-6 new rels, but base already has some
# We need to add: metadata, rdrichvalue, rdrichvaluestructure, rdRichValueTypes, richValueRel
# Find next rIds
next_id = max_rid + 1
rel_targets = [
    (f"rId{next_id}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata", "metadata.xml"),
    (f"rId{next_id+1}", "http://schemas.microsoft.com/office/2017/06/relationships/rdRichValue", "richData/rdrichvalue.xml"),
    (f"rId{next_id+2}", "http://schemas.microsoft.com/office/2017/06/relationships/rdRichValueStructure", "richData/rdrichvaluestructure.xml"),
    (f"rId{next_id+3}", "http://schemas.microsoft.com/office/2017/06/relationships/rdRichValueTypes", "richData/rdRichValueTypes.xml"),
    (f"rId{next_id+4}", "http://schemas.microsoft.com/office/2022/10/relationships/richValueRel", "richData/richValueRel.xml"),
]
rel_lines = "\n".join(f'  <Relationship Id="{rid}" Type="{typ}" Target="{tgt}"/>' for rid, typ, tgt in rel_targets)
# Insert before </Relationships>
rels_new = orig_rels.replace("</Relationships>", rel_lines + "\n</Relationships>")
base_files["xl/_rels/workbook.xml.rels"] = rels_new.encode()

# Generate new files for richData
# Use helpers
base_files["xl/metadata.xml"] = pic._metadata(len(all_entries)).encode()
base_files["xl/richData/rdrichvaluestructure.xml"] = pic._rich_struct(True, False).encode()
base_files["xl/richData/rdRichValueTypes.xml"] = pic._RICH_TYPES.encode()
base_files["xl/richData/rdrichvalue.xml"] = pic._rich_values(all_entries).encode()
base_files["xl/richData/richValueRel.xml"] = pic._rich_value_rel_xml(len([e for k,e in all_entries if k=="local"])).encode()
base_files["xl/richData/_rels/richValueRel.xml.rels"] = pic._rich_value_rel_rels(all_entries).encode()

# Add media images
# Need to handle that base already has no media, but we will add new media files
# The place_in_cell's media naming is image1, image2 etc. in order of all_entries
for idx, (kind, entry) in enumerate(all_entries):
    if kind == "local":
        # Find the rel index for this entry (0-based among locals)
        # The helper uses local_indices order
        # For simplicity, use idx among locals
        # Count locals before this idx
        local_idx = sum(1 for k,_ in all_entries[:idx] if k=="local")
        media_name = f"xl/media/image{local_idx+1}.{entry['ext']}"
        with open(entry["path"], "rb") as f:
            base_files[media_name] = f.read()
        # Also need to ensure content type for this ext is added (already handled)

# Now patch xl/worksheets/sheet1.xml to add image cells
# Read original sheet
sheet_xml = base_files["xl/worksheets/sheet1.xml"].decode()
# For each image, we need to find the row and insert <c r="ALxxx" t="e" vm="N"><v>#VALUE!</v></c>
# The vm index is the order in all_entries (0-based)

# Build map cell -> vm
cell_to_vm = {}
for vm_idx, (kind, entry) in enumerate(all_entries):
    # entry has col and row
    col = entry["col"]
    row = entry["row"]
    cell = f"{col}{row}"
    cell_to_vm[cell] = vm_idx

# Group by row
from collections import defaultdict
row_to_cells = defaultdict(list)
for cell, vm in cell_to_vm.items():
    # cell like AL13 -> row 13, col AL
    m = re.match(r"([A-Z]+)(\d+)", cell)
    col, row = m.group(1), int(m.group(2))
    row_to_cells[row].append((col, vm))

# For each row, insert the AL cell
# The sheet XML has <row r="13" ...><c ...>...</c>...</row>
# We need to insert after existing cells, sorted by col
# Use regex to find row blocks
def patch_sheet(sheet_xml, row_to_cells):
    # For each row, find its <row>...</row> and inject
    for row_num, cells in sorted(row_to_cells.items()):
        # cells is list of (col, vm) for that row (should be 1 per row for our case AL)
        # Find the row element: <row r="13" ...>.*?</row>
        # Use regex with DOTALL
        pattern = re.compile(rf'(<row r="{row_num}"[^>]*>)(.*?)(</row>)', re.DOTALL)
        m = pattern.search(sheet_xml)
        if not m:
            print(f"Row {row_num} not found in sheet XML - creating new row?")
            # If row doesn't exist (unlikely, since we have data rows for all), skip
            continue
        start, inner, end = m.groups()
        # inner contains existing <c> elements
        # Append new cells sorted by col
        for col, vm in sorted(cells, key=lambda x: pic._col_num(x[0])):
            new_cell = f'<c r="{col}{row_num}" t="e" vm="{vm}"><v>#VALUE!</v></c>'
            inner = inner + new_cell
        # Reconstruct
        new_row = start + inner + end
        sheet_xml = sheet_xml.replace(m.group(0), new_row, 1)
    return sheet_xml

sheet_patched = patch_sheet(sheet_xml, row_to_cells)
# Update dimension if needed? The dimension is A1:AL1644, which already includes AL, so fine
base_files["xl/worksheets/sheet1.xml"] = sheet_patched.encode()

# Also need to ensure the sheet has no drawing reference (base has none, since we cleared)
# So no need to remove drawing

# Write new zip
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in base_files.items():
        zout.writestr(name, data)

print(f"Saved true in-cell to {OUT} with {len(all_entries)} images")
# Cleanup tmp
shutil.rmtree(tmpdir)
print("Cleaned tmp")

# Verify
import zipfile as zf2
z = zf2.ZipFile(OUT)
print("Has metadata?", "xl/metadata.xml" in z.namelist())
print("Has richData?", any("richData" in n for n in z.namelist()))
print("Has media?", len([n for n in z.namelist() if "media" in n]))
# Check a sample row in sheet
data = z.read("xl/worksheets/sheet1.xml").decode()
import re
print("Sample AL13 cell exists?", 'r="AL13"' in data)
# Find AL13
m = re.search(r'<c r="AL13"[^>]*>.*?</c>', data)
print(m.group(0)[:200] if m else "not found")
z.close()

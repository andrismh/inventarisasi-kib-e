from datetime import datetime
from sqlalchemy import Index, func
from .extensions import db


class MasterMixin:
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(64), unique=True, nullable=False)
    nama = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {"id": self.id, "kode": self.kode, "nama": self.nama}


class MasterKondisi(MasterMixin, db.Model):
    __tablename__ = "master_kondisi"


class MasterSatuan(MasterMixin, db.Model):
    __tablename__ = "master_satuan"


class MasterRuang(MasterMixin, db.Model):
    __tablename__ = "master_ruang"


class MasterBarang(MasterMixin, db.Model):
    __tablename__ = "master_barang"


JENIS_ASET = {"BUKU", "BARANG BERCORAK KESENIAN", "HEWAN & TUMBUHAN"}
STATUS_KEBERADAAN = {"hilang", "tidak ditemukan"}
YA_TIDAK = {"ya", "tidak"}
ADA_TIDAK = {"ada", "tidak"}
PENGGUNAAN = {
    "pemerintah daerah",
    "pemerintah pusat",
    "pemerintah daerah lainnya",
    "pihak lain",
}


class InventoryItem(db.Model):
    __tablename__ = "inventory_item"

    nibar = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    kode_register = db.Column(db.String(32), nullable=False)
    kode_barang_id = db.Column(db.Integer, db.ForeignKey("master_barang.id"), nullable=False)
    tahun_perolehan = db.Column(db.Integer, nullable=False)
    nilai_perolehan = db.Column(db.BigInteger, nullable=False)
    spesifikasi = db.Column(db.Text)
    jenis_aset = db.Column(db.String(64), nullable=False)
    judul_buku = db.Column(db.String(512))
    pencipta_buku = db.Column(db.String(255))
    spesifikasi_buku = db.Column(db.Text)
    jumlah_barang = db.Column(db.Integer, nullable=False, default=1)
    satuan_barang_id = db.Column(db.Integer, db.ForeignKey("master_satuan.id"), nullable=False)
    status_keberadaan = db.Column(db.String(32))
    jml_keberadaan = db.Column(db.Integer)
    merupakan_atribusi = db.Column(db.String(8))
    nibar_atribusi = db.Column(db.BigInteger)
    alamat = db.Column(db.String(512))
    koordinat = db.Column(db.String(128))
    ruangan_id = db.Column(db.Integer, db.ForeignKey("master_ruang.id"))
    kondisi_barang_id = db.Column(db.Integer, db.ForeignKey("master_kondisi.id"), nullable=False)
    merk_type = db.Column(db.String(255))
    penggunaan = db.Column(db.String(64))
    nama_kuasa = db.Column(db.String(255))
    nama_pemakai = db.Column(db.String(255))
    status_pemakai = db.Column(db.String(128))
    bast = db.Column(db.String(8))
    nama_dasar_penggunaan = db.Column(db.String(255))
    nama_dokumen = db.Column(db.String(255))
    nibar_tercatat_ganda = db.Column(db.String(255))
    deskripsi_barang = db.Column(db.Text)
    keterangan = db.Column(db.Text)
    petugas = db.Column(db.Text)
    foto = db.Column(db.String(512))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    kode_barang = db.relationship("MasterBarang")
    satuan_barang = db.relationship("MasterSatuan")
    ruangan = db.relationship("MasterRuang")
    kondisi_barang = db.relationship("MasterKondisi")

    __table_args__ = (
        Index("ix_inventory_item_judul_lower", func.lower(judul_buku)),
    )

    def to_dict(self, fields=None):
        data = {
            "nibar": self.nibar,
            "kode_register": self.kode_register,
            "kode_barang_id": self.kode_barang_id,
            "kode_barang": self.kode_barang.nama if self.kode_barang else None,
            "tahun_perolehan": self.tahun_perolehan,
            "nilai_perolehan": self.nilai_perolehan,
            "asal_usul": self.spesifikasi,
            "spesifikasi": self.spesifikasi,
            "jenis_aset": self.jenis_aset,
            "judul_buku": self.judul_buku,
            "pencipta_buku": self.pencipta_buku,
            "spesifikasi_buku": self.spesifikasi_buku,
            "jumlah_barang": self.jumlah_barang,
            "satuan_barang_id": self.satuan_barang_id,
            "satuan_barang": self.satuan_barang.nama if self.satuan_barang else None,
            "status_keberadaan": self.status_keberadaan,
            "jml_keberadaan": self.jml_keberadaan,
            "merupakan_atribusi": self.merupakan_atribusi,
            "nibar_atribusi": self.nibar_atribusi,
            "alamat": self.alamat,
            "koordinat": self.koordinat,
            "ruangan_id": self.ruangan_id,
            "ruangan": self.ruangan.nama if self.ruangan else None,
            "kondisi_barang_id": self.kondisi_barang_id,
            "kondisi_barang": self.kondisi_barang.nama if self.kondisi_barang else None,
            "merk_type": self.merk_type,
            "penggunaan": self.penggunaan,
            "nama_kuasa": self.nama_kuasa,
            "nama_pemakai": self.nama_pemakai,
            "status_pemakai": self.status_pemakai,
            "bast": self.bast,
            "nama_dasar_penggunaan": self.nama_dasar_penggunaan,
            "nama_dokumen": self.nama_dokumen,
            "nibar_tercatat_ganda": self.nibar_tercatat_ganda,
            "deskripsi_barang": self.deskripsi_barang,
            "keterangan": self.keterangan,
            "petugas": self.petugas,
            "foto": self.foto,
        }
        if fields:
            return {k: data[k] for k in fields if k in data}
        return data

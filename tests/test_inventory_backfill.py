import unittest

from app import create_app
from app.extensions import db
from app.models import InventoryItem, MasterBarang, MasterKondisi, MasterRuang, MasterSatuan


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class InventoryBackfillTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.runner = self.app.test_cli_runner()
        with self.app.app_context():
            db.create_all()
            barang = MasterBarang(kode="01", nama="01 - Umum")
            satuan = MasterSatuan(kode="3", nama="3 - Buah")
            ruang = MasterRuang(
                kode="10531",
                nama="10531 - GEDUNG UNIT IV > GEDUNG UNIT IV LANTAI 3 > RUANG RAPAT F BIDANG PENGELOLA BMD",
            )
            kondisi = MasterKondisi(kode="1", nama="1 - Baik")
            db.session.add_all([barang, satuan, ruang, kondisi])
            db.session.flush()
            db.session.add_all(
                [
                    InventoryItem(
                        nibar=3001,
                        kode_register="000001",
                        kode_barang_id=barang.id,
                        tahun_perolehan=2026,
                        nilai_perolehan=1000,
                        jenis_aset="",
                        judul_buku="Judul Backfill",
                        jumlah_barang=1,
                        satuan_barang_id=satuan.id,
                        kondisi_barang_id=kondisi.id,
                    ),
                    InventoryItem(
                        nibar=3002,
                        kode_register="000002",
                        kode_barang_id=barang.id,
                        tahun_perolehan=2026,
                        nilai_perolehan=1000,
                        spesifikasi="Existing",
                        jenis_aset="BUKU",
                        judul_buku="Judul Existing",
                        jumlah_barang=2,
                        satuan_barang_id=satuan.id,
                        kondisi_barang_id=kondisi.id,
                        deskripsi_barang="Manual",
                    ),
                ]
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_backfill_defaults_fills_blanks_and_preserves_existing_values(self):
        result = self.runner.invoke(args=["backfill-inventory-defaults"])

        self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            filled = InventoryItem.query.get(3001)
            preserved = InventoryItem.query.get(3002)

            self.assertEqual(filled.spesifikasi, "6-APBD")
            self.assertEqual(filled.jenis_aset, "BUKU")
            self.assertEqual(filled.merupakan_atribusi, "tidak")
            self.assertEqual(filled.koordinat, "-7.794439738764821, 110.36759391147048")
            self.assertEqual(filled.status_pemakai, "Badan Pengelola Keuangan dan Aset DIY")
            self.assertEqual(filled.deskripsi_barang, "Buku Umum")
            self.assertEqual(filled.keterangan, "Judul Backfill")
            self.assertEqual(filled.bast, "tidak")
            self.assertEqual(filled.ruangan.kode, "10531")

            self.assertEqual(preserved.spesifikasi, "Existing")
            self.assertEqual(preserved.jumlah_barang, 2)
            self.assertEqual(preserved.deskripsi_barang, "Manual")


if __name__ == "__main__":
    unittest.main()

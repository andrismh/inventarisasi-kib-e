import io
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import InventoryItem, MasterBarang, MasterKondisi, MasterRuang, MasterSatuan


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_FOTO_UPLOAD_BYTES = 5 * 1024 * 1024


class InventoryApiTest(unittest.TestCase):
    def setUp(self):
        self.upload_dir = tempfile.TemporaryDirectory()
        TestConfig.FOTO_UPLOAD_DIR = self.upload_dir.name
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
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
                        nibar=1001,
                        kode_register="000001",
                        kode_barang_id=barang.id,
                        tahun_perolehan=2024,
                        nilai_perolehan=10000,
                        jenis_aset="BUKU",
                        judul_buku="Atlas Sekolah",
                        jumlah_barang=1,
                        satuan_barang_id=satuan.id,
                        kondisi_barang_id=kondisi.id,
                    ),
                    InventoryItem(
                        nibar=1002,
                        kode_register="000002",
                        kode_barang_id=barang.id,
                        tahun_perolehan=2024,
                        nilai_perolehan=15000,
                        jenis_aset="BUKU",
                        judul_buku="Kamus Bahasa",
                        pencipta_buku="Tim",
                        jumlah_barang=1,
                        satuan_barang_id=satuan.id,
                        kondisi_barang_id=kondisi.id,
                        alamat="Rak A",
                        koordinat="0,0",
                        merk_type="Cetak",
                        status_keberadaan="hilang",
                        jml_keberadaan=1,
                        merupakan_atribusi="tidak",
                        nibar_atribusi=1001,
                        penggunaan="pemerintah daerah",
                        nama_kuasa="Kuasa",
                        nama_pemakai="Pemakai",
                        status_pemakai="Aktif",
                        bast="ada",
                        nama_dasar_penggunaan="SK",
                        nama_dokumen="Dokumen",
                        nibar_tercatat_ganda="Tidak",
                        deskripsi_barang="Lengkap",
                        keterangan="OK",
                        petugas="Andri",
                        foto="foto.jpg",
                    ),
                    InventoryItem(
                        nibar=1003,
                        kode_register="000003",
                        kode_barang_id=barang.id,
                        tahun_perolehan=2024,
                        nilai_perolehan=20000,
                        jenis_aset="BUKU",
                        jumlah_barang=1,
                        satuan_barang_id=satuan.id,
                        kondisi_barang_id=kondisi.id,
                    ),
                    InventoryItem(
                        nibar=1004,
                        kode_register="000004",
                        kode_barang_id=barang.id,
                        tahun_perolehan=2024,
                        nilai_perolehan=20000,
                        jenis_aset="BUKU",
                        judul_buku="Atlas Sekolah",
                        jumlah_barang=1,
                        satuan_barang_id=satuan.id,
                        kondisi_barang_id=kondisi.id,
                    ),
                ]
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.upload_dir.cleanup()

    def test_stats_counts_completion_and_blank_titles(self):
        response = self.client.get("/api/inventory/stats")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total"], 4)
        self.assertEqual(data["complete"], 0)
        self.assertEqual(data["incomplete"], 4)
        self.assertEqual(data["blank_title"], 1)
        self.assertEqual(data["missing_fields"]["alamat"], 3)
        self.assertNotIn("status_keberadaan", data["missing_fields"])
        self.assertNotIn("jml_keberadaan", data["missing_fields"])
        self.assertNotIn("nibar_atribusi", data["missing_fields"])
        self.assertNotIn("nama_dasar_penggunaan", data["missing_fields"])
        self.assertNotIn("nama_dokumen", data["missing_fields"])
        self.assertEqual(data["duplicate_risk"], 2)
        self.assertIn("all_optional", data["queues"])

    def test_inventory_filters_by_missing_optional_field(self):
        response = self.client.get("/api/inventory?missing=alamat")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total"], 3)
        self.assertEqual([item["nibar"] for item in data["items"]], [1001, 1003, 1004])

    def test_inventory_filters_by_any_missing_optional_field(self):
        response = self.client.get("/api/inventory?missing=all_optional")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total"], 4)

    def test_inventory_filters_by_query_text(self):
        response = self.client.get("/api/inventory?q=kamus")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["nibar"], 1002)

    def test_inventory_filters_by_duplicate_titles(self):
        response = self.client.get("/api/inventory?duplicates=judul_buku")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total"], 2)
        self.assertEqual([item["nibar"] for item in data["items"]], [1001, 1004])

    def test_create_applies_required_inventory_defaults(self):
        response = self.client.post(
            "/api/inventory",
            json={
                "nibar": 2001,
                "kode_register": "000200",
                "kode_barang_id": 1,
                "tahun_perolehan": 2026,
                "nilai_perolehan": 50000,
                "judul_buku": "Buku Default",
                "kondisi_barang_id": 1,
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["asal_usul"], "6-APBD")
        self.assertEqual(data["spesifikasi"], "6-APBD")
        self.assertEqual(data["jenis_aset"], "BUKU")
        self.assertEqual(data["jumlah_barang"], 1)
        self.assertEqual(data["satuan_barang"], "3 - Buah")
        self.assertEqual(data["merupakan_atribusi"], "tidak")
        self.assertEqual(data["koordinat"], "-7.794439738764821, 110.36759391147048")
        self.assertIn("RUANG RAPAT F BIDANG PENGELOLA BMD", data["ruangan"])
        self.assertEqual(data["nama_kuasa"], "Badan Pengelola Keuangan dan Aset DIY")
        self.assertEqual(data["nama_pemakai"], "Badan Pengelola Keuangan dan Aset DIY")
        self.assertEqual(data["status_pemakai"], "Badan Pengelola Keuangan dan Aset DIY")
        self.assertEqual(data["bast"], "tidak")
        self.assertEqual(data["nibar_tercatat_ganda"], "tidak")
        self.assertEqual(data["deskripsi_barang"], "Buku Umum")
        self.assertEqual(data["keterangan"], "Buku Default")

    def test_create_special_nibar_uses_non_book_asset_default(self):
        response = self.client.post(
            "/api/inventory",
            json={
                "nibar": 1422257,
                "kode_register": "000001",
                "kode_barang_id": 1,
                "tahun_perolehan": 2009,
                "nilai_perolehan": 14850000,
                "jenis_aset": "BUKU",
                "kondisi_barang_id": 1,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["jenis_aset"], "HEWAN & TUMBUHAN")

    def test_asal_usul_alias_maps_to_spesifikasi(self):
        response = self.client.patch("/api/inventory/1001", json={"asal_usul": "7-Hibah"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["asal_usul"], "7-Hibah")
        self.assertEqual(data["spesifikasi"], "7-Hibah")

    def test_foto_upload_rejects_missing_inventory_row(self):
        response = self.client.post(
            "/api/inventory/9999/foto",
            data={"foto": (io.BytesIO(b"\xff\xd8\xff\xe0jpeg"), "capture.jpg")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 404)

    def test_foto_upload_rejects_non_image_file(self):
        response = self.client.post(
            "/api/inventory/1001/foto",
            data={"foto": (io.BytesIO(b"not an image"), "notes.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Unsupported image type")

    def test_foto_upload_rejects_too_large_file(self):
        response = self.client.post(
            "/api/inventory/1001/foto",
            data={
                "foto": (
                    io.BytesIO(b"x" * (TestConfig.MAX_FOTO_UPLOAD_BYTES + 1)),
                    "capture.jpg",
                )
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Photo file is too large")

    def test_foto_upload_saves_file_and_updates_inventory_path(self):
        response = self.client.post(
            "/api/inventory/1001/foto",
            data={"foto": (io.BytesIO(b"\xff\xd8\xff\xe0jpeg"), "capture.jpg")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, {"nibar": 1001, "foto": "/static/foto/1001.jpg"})
        with self.app.app_context():
            item = InventoryItem.query.get(1001)
            self.assertEqual(item.foto, "/static/foto/1001.jpg")
        self.assertTrue((Path(self.upload_dir.name) / "1001.jpg").exists())

    def test_foto_upload_replaces_previous_file_for_same_nibar(self):
        self.client.post(
            "/api/inventory/1001/foto",
            data={"foto": (io.BytesIO(b"\xff\xd8\xff\xe0jpeg"), "capture.jpg")},
            content_type="multipart/form-data",
        )

        response = self.client.post(
            "/api/inventory/1001/foto",
            data={"foto": (io.BytesIO(b"RIFFwebp"), "capture.webp")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["foto"], "/static/foto/1001.webp")
        self.assertFalse((Path(self.upload_dir.name) / "1001.jpg").exists())
        self.assertTrue((Path(self.upload_dir.name) / "1001.webp").exists())


if __name__ == "__main__":
    unittest.main()

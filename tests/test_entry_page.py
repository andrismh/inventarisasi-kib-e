import unittest

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_FOTO_UPLOAD_BYTES = 123456


class EntryPageTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_asset_details_is_book_focused(self):
        response = self.client.get("/entry")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Book Details", html)
        self.assertIn('name="jenis_aset" type="hidden" value="BUKU"', html)
        self.assertIn("Asal Usul", html)
        self.assertIn('name="asal_usul"', html)
        self.assertIn('value="6-APBD"', html)
        self.assertNotIn("Jenis Aset", html)
        self.assertNotIn("Merk / Type", html)
        self.assertNotIn("Status Keberadaan", html)
        self.assertNotIn("Jml Keberadaan", html)
        self.assertNotIn("NIBAR Atribusi", html)
        self.assertNotIn("Nama Dasar Penggunaan", html)
        self.assertNotIn("Nama Dokumen", html)

    def test_dashboard_and_editor_hide_deprecated_completion_fields(self):
        dashboard = self.client.get("/").get_data(as_text=True)
        editor = self.client.get("/master").get_data(as_text=True)

        for label in [
            "Status Keberadaan",
            "Jml Keberadaan",
            "NIBAR Atribusi",
            "Nama Dasar Penggunaan",
            "Nama Dokumen",
        ]:
            self.assertNotIn(label, dashboard)
            self.assertNotIn(label, editor)

        self.assertIn("Asal Usul", editor)

    def test_entry_page_uses_camera_capture_panel_for_foto(self):
        response = self.client.get("/entry")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="foto-panel"', html)
        self.assertIn('name="foto" type="hidden"', html)
        self.assertIn('type="file"', html)
        self.assertIn('accept="image/*"', html)
        self.assertIn('capture="environment"', html)
        self.assertIn('id="btn-upload-foto"', html)
        self.assertIn("fotoMaxUploadBytes: 123456", html)
        self.assertIn("disabled", html)
        self.assertNotIn("Foto (path)", html)


if __name__ == "__main__":
    unittest.main()

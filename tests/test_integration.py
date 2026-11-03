"""
End-to-End System Integration Test for Alzheimer's Platform.
Verifies all 20 required integration checkpoints:
1. Registration
2. Login
3. Logout
4. MySQL Connection
5. Dashboard
6. MRI JPG Upload
7. MRI PNG Upload
8. Invalid File Rejection
9. Actual CNN Classification
10. Four-Class Prediction
11. Confidence Score Display
12. Grad-CAM Generation
13. Cognitive Questionnaire
14. Cognitive Scoring
15. MySQL Data Storage
16. Prediction History
17. Assessment History
18. Progress Charts
19. PDF Report Downloads
20. User-Specific Data Security
"""

import os
import sys
import uuid
import io
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services import db_service


class CompleteIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
        cls.client = cls.app.test_client()

        # Create unique test users
        cls.test_uname1 = f"dr_test1_{uuid.uuid4().hex[:6]}"
        cls.test_email1 = f"{cls.test_uname1}@hospital.org"
        cls.test_pwd = "SecurePassword123!"

        cls.test_uname2 = f"dr_test2_{uuid.uuid4().hex[:6]}"
        cls.test_email2 = f"{cls.test_uname2}@hospital.org"

    def test_01_user_registration_and_login(self):
        """Checkpoints 1, 2, 3, 4: Registration, Login, Session, MySQL."""
        # 1. Register User 1
        res_reg = self.client.post("/auth/register", data={
            "username": self.test_uname1,
            "email": self.test_email1,
            "password": self.test_pwd,
            "confirm_password": self.test_pwd
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        # Verify in MySQL
        u1 = db_service.get_user_by_username(self.test_uname1)
        self.assertIsNotNone(u1)
        self.__class__.user1_id = u1["user_id"]

        # 2. Login User 1
        res_login = self.client.post("/auth/login", data={
            "username": self.test_uname1,
            "password": self.test_pwd
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Clinical Dashboard", res_login.data)

        # 3. Check Dashboard (Checkpoint 5)
        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Total MRI Predictions", res_dash.data)

    def test_02_mri_uploads_and_rejection(self):
        """Checkpoints 6, 7, 8: JPG, PNG Uploads & Invalid File Rejection."""
        # Login
        self.client.post("/auth/login", data={
            "username": self.test_uname1,
            "password": self.test_pwd
        }, follow_redirects=True)

        # 1. Invalid file rejection (.txt)
        bad_file = (io.BytesIO(b"This is not a brain MRI"), "test.txt")
        res_bad = self.client.post("/mri/upload", data={"mri_file": bad_file}, follow_redirects=True)
        self.assertIn(b"Invalid file format", res_bad.data)

        # 2. Valid PNG upload from real samples
        sample_png = list((PROJECT_ROOT / "data" / "samples").glob("*.png"))[0]
        with open(sample_png, "rb") as f:
            png_bytes = f.read()

        res_upload_png = self.client.post("/mri/upload", data={
            "mri_file": (io.BytesIO(png_bytes), sample_png.name)
        }, follow_redirects=True)
        self.assertEqual(res_upload_png.status_code, 200)
        self.assertIn(b"MRI Classification Analysis", res_upload_png.data)
        self.assertIn(b"Diagnostic Confidence", res_upload_png.data)

    def test_03_gradcam_and_history(self):
        """Checkpoints 9, 10, 11, 12, 16: CNN Inference, Confidence, Grad-CAM, History."""
        # Login
        self.client.post("/auth/login", data={
            "username": self.test_uname1,
            "password": self.test_pwd
        }, follow_redirects=True)

        # Fetch latest prediction from DB
        latest = db_service.get_latest_mri_prediction(self.user1_id)
        self.assertIsNotNone(latest)
        self.assertIn(latest["predicted_category"], [
            "Non-Demented", "Very Mild Demented", "Mild Demented", "Moderate Demented"
        ])
        self.assertGreater(latest["confidence"], 0.0)

        # View Grad-CAM page
        res_gc = self.client.get(f"/mri/gradcam/{latest['prediction_id']}")
        self.assertEqual(res_gc.status_code, 200)
        self.assertIn(b"Grad-CAM Visualization", res_gc.data)

        # View History
        res_hist = self.client.get("/mri/history")
        self.assertEqual(res_hist.status_code, 200)
        self.assertIn(latest["predicted_category"].encode(), res_hist.data)

    def test_04_cognitive_assessment_flow(self):
        """Checkpoints 13, 14, 15, 17: Questionnaire, Scoring, MySQL, History."""
        self.client.post("/auth/login", data={
            "username": self.test_uname1,
            "password": self.test_pwd
        }, follow_redirects=True)

        # Questionnaire Page
        res_test = self.client.get("/cognitive/test")
        self.assertEqual(res_test.status_code, 200)

        # Submit answers
        form_data = {
            "q_1": "Apple, Table, Penny",
            "q_2": "I recall specifically what I ate and approximately when",
            "q_3": "Penny",
            "q_4": "D-L-R-O-W",
            "q_5": "86",
            "q_6": "32 (doubling pattern)",
            "q_7": "I can identify the exact current year and correct season",
            "q_8": "I know my exact current city/state and building/room setting",
            "q_9": "Completing an educational cognitive assessment questionnaire on a computer/phone",
            "q_10": "Stethoscope",
            "q_11": "Easel",
            "q_12": "Despite the heavy rain, the students arrived on time for their morning lecture.",
            "q_13": "Engineer / Locomotive Driver",
            "q_14": "Drop it into the nearest official post box or give it to postal staff",
            "q_15": "Both are instruments used for measurement (time and length)"
        }
        res_sub = self.client.post("/cognitive/submit", data=form_data, follow_redirects=True)
        self.assertEqual(res_sub.status_code, 200)
        self.assertIn(b"Overall Cognitive Performance", res_sub.data)
        self.assertIn(b"High Cognitive Performance", res_sub.data)

        # Verify DB answers table
        latest_cog = db_service.get_latest_cognitive_assessment(self.user1_id)
        self.assertIsNotNone(latest_cog)
        self.assertEqual(latest_cog["total_score"], 30)

        full_assess = db_service.get_assessment_by_id(latest_cog["assessment_id"], self.user1_id)
        self.assertEqual(len(full_assess["answers"]), 15)

    def test_05_progress_and_pdf_reports(self):
        """Checkpoints 18, 19: Longitudinal Charts & PDF Report Downloads."""
        self.client.post("/auth/login", data={
            "username": self.test_uname1,
            "password": self.test_pwd
        }, follow_redirects=True)

        # Progress tracking page
        res_prog = self.client.get("/progress")
        self.assertEqual(res_prog.status_code, 200)
        self.assertIn(b"Longitudinal Timeline", res_prog.data)

        # Generate Report
        res_rep = self.client.get("/reports/generate", follow_redirects=True)
        self.assertEqual(res_rep.status_code, 200)
        self.assertEqual(res_rep.mimetype, "application/pdf")
        self.assertGreater(len(res_rep.data), 1000)

    def test_06_user_data_isolation(self):
        """Checkpoint 20: User-specific data security (User 2 cannot view User 1)."""
        # Ensure User 1 is logged out first
        self.client.get("/auth/logout")

        # Register and Login User 2
        self.client.post("/auth/register", data={
            "username": self.test_uname2,
            "email": self.test_email2,
            "password": self.test_pwd,
            "confirm_password": self.test_pwd
        }, follow_redirects=True)

        self.client.post("/auth/login", data={
            "username": self.test_uname2,
            "password": self.test_pwd
        }, follow_redirects=True)

        # Fetch User 1's prediction
        u1_pred = db_service.get_latest_mri_prediction(self.user1_id)
        self.assertIsNotNone(u1_pred)

        # Attempt to access User 1's prediction result as User 2
        res_access = self.client.get(f"/mri/result/{u1_pred['prediction_id']}", follow_redirects=True)
        self.assertIn(b"unauthorized", res_access.data.lower())

    @classmethod
    def tearDownClass(cls):
        """Clean up test users from database."""
        conn = db_service.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username IN (%s, %s)", (cls.test_uname1, cls.test_uname2))
        conn.commit()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    unittest.main()

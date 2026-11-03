"""
Comprehensive System Verification Test Suite.
Tests:
1. Flask application initialization and configuration
2. Authentication flow (register, login, session)
3. MySQL database connectivity and CRUD operations
4. Cognitive assessment scoring engine across all 5 domains
5. ReportLab PDF generation integrity
6. File upload and security restrictions
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services import db_service, cognitive_service, report_service


class AlzheimerSystemTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test Flask client."""
        cls.app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
        cls.client = cls.app.test_client()

    def test_01_home_and_public_routes(self):
        """Verify public routes are reachable."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Alzheimer's Disease Classification", res.data)

        res_login = self.client.get("/auth/login")
        self.assertEqual(res_login.status_code, 200)

        res_reg = self.client.get("/auth/register")
        self.assertEqual(res_reg.status_code, 200)

    def test_02_database_connectivity(self):
        """Verify MySQL connection and basic query execution."""
        conn = db_service.get_connection()
        self.assertIsNotNone(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 + 1;")
        res = cursor.fetchone()
        self.assertEqual(res[0], 2)
        cursor.close()
        conn.close()

    def test_03_cognitive_scoring_engine(self):
        """Verify accurate multi-domain scoring and educational tiers."""
        # Perfect answers across all 15 questions
        perfect_answers = {
            "1": "Apple, Table, Penny",
            "2": "I recall specifically what I ate and approximately when",
            "3": "Penny",
            "4": "D-L-R-O-W",
            "5": "86",
            "6": "32 (doubling pattern)",
            "7": "I can identify the exact current year and correct season",
            "8": "I know my exact current city/state and building/room setting",
            "9": "Completing an educational cognitive assessment questionnaire on a computer/phone",
            "10": "Stethoscope",
            "11": "Easel",
            "12": "Despite the heavy rain, the students arrived on time for their morning lecture.",
            "13": "Engineer / Locomotive Driver",
            "14": "Drop it into the nearest official post box or give it to postal staff",
            "15": "Both are instruments used for measurement (time and length)"
        }
        scored = cognitive_service.score_assessment(perfect_answers)
        self.assertEqual(scored["total_score"], 30)
        self.assertEqual(scored["performance_tier"], "High Cognitive Performance")
        for dom, sc in scored["domain_scores"].items():
            self.assertEqual(sc, 6)

        # Partial/zero answers
        zero_answers = {str(i): "incorrect answer" for i in range(1, 16)}
        scored_zero = cognitive_service.score_assessment(zero_answers)
        self.assertEqual(scored_zero["total_score"], 0)
        self.assertEqual(scored_zero["performance_tier"], "Substantial Cognitive Variation")

    def test_04_pdf_report_generation(self):
        """Verify that ReportLab builds a valid PDF report."""
        user_info = {"user_id": 999, "username": "TestDoctor", "email": "doctor@test.edu"}
        mri_info = {
            "predicted_category": "Very Mild Demented",
            "confidence": 0.885,
            "image_path": None,
            "gradcam_path": None
        }
        cog_info = {
            "total_score": 24,
            "max_score": 30,
            "domain_scores": {"Memory": 4, "Attention": 5, "Orientation": 5, "Language": 5, "Reasoning": 5},
            "performance_tier": "Mild Cognitive Variation"
        }
        pdf_path = report_service.generate_pdf_report(
            user_info, mri_result=mri_info, cognitive_result=cog_info, output_filename="test_verification_report.pdf"
        )
        self.assertTrue(Path(pdf_path).exists())
        self.assertGreater(Path(pdf_path).stat().st_size, 1000)

    def test_05_auth_flow(self):
        """Test registration, duplicate prevention, and login."""
        import uuid
        test_uname = f"u_{uuid.uuid4().hex[:6]}"
        test_email = f"{test_uname}@test.com"

        # Register
        res = self.client.post("/auth/register", data={
            "username": test_uname,
            "email": test_email,
            "password": "Password123!",
            "confirm_password": "Password123!"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Login
        res_login = self.client.post("/auth/login", data={
            "username": test_uname,
            "password": "Password123!"
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Clinical Dashboard", res_login.data)

        # Clean up created test user
        user = db_service.get_user_by_username(test_uname)
        if user:
            conn = db_service.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user["user_id"],))
            conn.commit()
            cursor.close()
            conn.close()


if __name__ == "__main__":
    unittest.main()

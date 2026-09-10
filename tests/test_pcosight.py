import importlib
import os
import sys
import unittest
import warnings
from unittest.mock import patch

from sklearn.exceptions import InconsistentVersionWarning


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

pcos_app = importlib.import_module("app")


BASIC_INPUT = {
    "Age (yrs)": 24.0,
    "BMI": 25.3,
    "Cycle(R/I)": 2,
    "Pimples(Y/N)": 1,
    "hair growth(Y/N)": 0,
    "Hair loss(Y/N)": 1,
    "Weight gain(Y/N)": 0,
    "Skin darkening (Y/N)": 0,
    "Fast food (Y/N)": 1,
    "Reg.Exercise(Y/N)": 1,
}

ADVANCED_INPUT = {
    "Age (yrs)": 24.0,
    "BMI": 25.3,
    "Cycle(R/I)": 2,
    "Pimples(Y/N)": 1,
    "hair growth(Y/N)": 0,
    "Hair loss(Y/N)": 1,
    "Weight gain(Y/N)": 0,
    "Skin darkening (Y/N)": 0,
    "AMH(ng/mL)": 4.2,
    "LH(mIU/mL)": 8.4,
    "FSH(mIU/mL)": 5.1,
    "LH_FSH_Ratio": 1.65,
    "TSH (mIU/L)": 2.3,
    "PRL(ng/mL)": 14.0,
    "RBS(mg/dl)": 92.0,
}


class ModelLoadingTests(unittest.TestCase):
    def test_basic_model_assets_load_with_expected_features(self):
        pcos_app.basic_model = None
        pcos_app.basic_scaler = None
        pcos_app.basic_features = None

        pcos_app.load_basic_assets()

        self.assertIsNotNone(pcos_app.basic_model)
        self.assertIsNotNone(pcos_app.basic_scaler)
        self.assertEqual(list(BASIC_INPUT.keys()), list(pcos_app.basic_features))
        self.assertTrue(hasattr(pcos_app.basic_model, "predict_proba"))
        self.assertTrue(hasattr(pcos_app.basic_scaler, "transform"))

    def test_advanced_model_assets_load_with_expected_features(self):
        pcos_app.adv_model = None
        pcos_app.adv_features = None

        pcos_app.load_advanced_assets()

        self.assertIsNotNone(pcos_app.adv_model)
        self.assertEqual(list(ADVANCED_INPUT.keys()), list(pcos_app.adv_features))
        self.assertTrue(hasattr(pcos_app.adv_model, "predict_proba"))


class PredictionTests(unittest.TestCase):
    def test_basic_prediction_returns_probability_between_zero_and_one(self):
        probability = pcos_app.predict_basic(BASIC_INPUT)

        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

    def test_advanced_prediction_returns_probability_between_zero_and_one(self):
        probability = pcos_app.predict_advanced(ADVANCED_INPUT)

        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

    def test_basic_prediction_requires_all_expected_features(self):
        incomplete_input = BASIC_INPUT.copy()
        incomplete_input.pop("BMI")

        with self.assertRaises(KeyError):
            pcos_app.predict_basic(incomplete_input)

    def test_advanced_prediction_requires_all_expected_features(self):
        incomplete_input = ADVANCED_INPUT.copy()
        incomplete_input.pop("AMH(ng/mL)")

        with self.assertRaises(KeyError):
            pcos_app.predict_advanced(incomplete_input)


class FlaskRouteValidationTests(unittest.TestCase):
    def setUp(self):
        pcos_app.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = pcos_app.app.test_client()

    def test_protected_prediction_pages_redirect_to_login(self):
        response = self.client.get("/basic")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_register_rejects_missing_required_fields(self):
        response = self.client.post(
            "/register",
            data={"email": "", "username": "newuser", "password": "secret"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/register", response.headers["Location"])

    def test_login_rejects_unknown_user(self):
        response = self.client.post(
            "/login",
            data={"username": "missing-user", "password": "bad-password"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    @patch.object(pcos_app, "save_prediction")
    @patch.object(pcos_app, "generate_recommendations")
    @patch.object(pcos_app, "predict_basic")
    def test_basic_form_submits_valid_input_to_prediction_pipeline(
        self,
        mock_predict_basic,
        mock_generate_recommendations,
        mock_save_prediction,
    ):
        mock_predict_basic.return_value = 0.42
        mock_generate_recommendations.return_value = {
            "good": ["Screening completed."],
            "bad": ["Monitor symptoms."],
            "improve": ["Follow up if symptoms persist."],
        }

        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["username"] = "tester"

        response = self.client.post(
            "/basic",
            data={
                "age": "24",
                "bmi": "25.3",
                "cycle": "2",
                "pimples": "1",
                "hair_growth": "0",
                "hair_loss": "1",
                "weight_gain": "0",
                "skin_darkening": "0",
                "fast_food": "1",
                "regular_exercise": "1",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/basic", response.headers["Location"])
        mock_predict_basic.assert_called_once_with(BASIC_INPUT)
        mock_generate_recommendations.assert_called_once()
        mock_save_prediction.assert_called_once()

    @patch.object(pcos_app, "save_prediction")
    @patch.object(pcos_app, "generate_recommendations")
    @patch.object(pcos_app, "predict_advanced")
    def test_advanced_form_submits_valid_input_to_prediction_pipeline(
        self,
        mock_predict_advanced,
        mock_generate_recommendations,
        mock_save_prediction,
    ):
        mock_predict_advanced.return_value = 0.58
        mock_generate_recommendations.return_value = {
            "good": ["Screening completed."],
            "bad": ["Review hormonal markers."],
            "improve": ["Discuss results with a clinician."],
        }

        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["username"] = "tester"

        response = self.client.post(
            "/advanced",
            data={
                "age": "24",
                "bmi": "25.3",
                "cycle": "2",
                "pimples": "1",
                "hair_growth": "0",
                "hair_loss": "1",
                "weight_gain": "0",
                "skin_darkening": "0",
                "amh": "4.2",
                "lh": "8.4",
                "fsh": "5.1",
                "lh_fsh_ratio": "1.65",
                "tsh": "2.3",
                "prl": "14.0",
                "rbs": "92.0",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/advanced", response.headers["Location"])
        mock_predict_advanced.assert_called_once_with(ADVANCED_INPUT)
        mock_generate_recommendations.assert_called_once()
        mock_save_prediction.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)

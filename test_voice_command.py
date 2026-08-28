import unittest
from app.routes import clean_whisper_output

class TestVoiceCommandProcessing(unittest.TestCase):
    def test_clean_whisper_output(self):
        test_input = "I spent 500 on dinner on March 2nd."
        expected_output = {
            "date": "2025-03-02",
            "category": "Food",
            "amount": "500",
            "description": "I spent on dinner"
        }
        result = clean_whisper_output(test_input)
        self.assertEqual(result, expected_output)  # ✅ Automatically checks

if __name__ == '__main__':
    unittest.main()

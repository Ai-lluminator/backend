import unittest
import requests
from flask import jsonify
import time

class TestServer(unittest.TestCase):
    def setUp(self):
        self.base_url = 'http://127.0.0.1:5000'

    def test_get_request(self):
        test_data = {'userId': 1, 'telegramUserId': 1, 'prompts': [{"id":1234, "prompt":"I am interested in LLMs working in science"},], 'status': 'PENDING'}
        response = requests.post(self.base_url + "/checkout", json=test_data)
        self.assertEqual(response.status_code, 201)
        time.sleep(1)
        
        result_response = requests.get(self.base_url + f"/results/{response.json()['jobId']}")
        self.assertEqual(result_response.status_code, 200)
        print(len(result_response.json()["data"]))
        print(point["data"]["title"] for point in result_response.json()["data"])

if __name__ == '__main__':
    unittest.main()
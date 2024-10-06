from flask import Flask, request, jsonify
import datetime
from database import RAG
from worker import Worker

app = Flask(__name__)

jobs = {}
results = {}
job_ids = []

worker = Worker(jobs, results, job_ids)

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.json
    # Assuming a jobId generation mechanism
    if len(job_ids) == 0:
        jobId = 1
    else:
        jobId = max(job_ids) + 1
    job_ids.append(jobId)
    jobs[jobId] = {'userId': data['userId'], 'telegramUserId': data['telegramUserId'], 'prompts': data['prompts'], 'status': 'PENDING'}
    return jsonify({'jobId': jobId}), 201

@app.route('/jobs/<int:job_id>', methods=['GET'])
def get_job_status(job_id):
    job = jobs.get(job_id)
    if job is None:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'jobId': job_id, 'status': job['status']}), 200

@app.route('/results/<int:job_id>', methods=['GET'])
def get_results(job_id):
    if job_id not in results:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(results[job_id]), 200

if __name__ == '__main__':
    worker.start()
    app.run(debug=True)
from database import RAG
import threading

class Worker:
    def __init__(self, jobs, results, job_ids):
        self.jobs = jobs
        self.job_ids = job_ids
        self.results = results

    def __run(self):
        rag = RAG()
        while True:
            for job_id in self.job_ids:
                job = self.jobs[job_id]
                if job['status'] == 'PENDING':
                    results = {"data":[]}
                    for prompt in job["prompts"]:
                        papers = rag.query(prompt['prompt'], limit=10)
                        current = {"promptId":prompt["id"], "data":[]}
                        for paper in zip(papers['documents'][0], papers['metadatas'][0]):
                            content = paper[0]
                            authors = paper[1]['authors'].split(',')
                            link = paper[1]['link']
                            title = paper[1]['title']
                            current['data'].append({'content': content, 'authors': authors, 'link': link, 'title':title})
                        results["data"].append(current)

                    job['status'] = 'COMPLETED'
                    self.jobs[job_id] = job
                    self.results[job_id] = results

    def start(self):
        thread = threading.Thread(target=self.__run, daemon=True)
        thread.start()
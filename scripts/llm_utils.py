from openai import OpenAI


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI()

    def get_response(self, prompt, model="gpt-4-0125-preview"):
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model, 
        )
        response = completion.choices[0].message.content
        return response

class ArxivAgent:
    def __init__(self, model=None):
        self.client = OpenAIClient()
        self.model = model or "gpt-4-0125-preview"

    def tldr(self, abstract):
        prompt = '\n'.join([
            "You are a cosmologist reading an abstract of an arXiv paper. " 
            "You will write a TL;DR for the paper. Here is the abstract:",
            "",
            "Abstract:",
            abstract,
            "",
            "TL;DR:"
        ])
        res = self.client.get_response(prompt, model=self.model)
        return res.replace("TL;DR: ", "")
from groq import Groq
import os


class OpenAIClient:
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("OPENAI_API_KEY")
        )

    def get_response(self, prompt, model="gpt-4-turbo"):
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model, 
        )
        response = completion.choices[0].message.content
        return response

class ArxivAgent:
    def __init__(self, model=None):
        self.client = OpenAIClient()
        self.model = model or "gpt-4-turbo"

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
import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_schedule(tasks):

    task_text = ""

    for task in tasks:
        task_text += f"""
        Task: {task['title']}
        Deadline: {task['deadline']}
        Description: {task['description']}
        """

    prompt = f"""
    You are an AI productivity planner.

    Create a daily schedule from these tasks.

    Tasks:
    {task_text}

    Return a clean timetable only.
    """

    response = model.generate_content(prompt)

    return response.text
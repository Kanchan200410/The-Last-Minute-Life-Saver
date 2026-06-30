import json
import google.generativeai as genai

from config import Config


# ==========================================
# CONFIGURE GEMINI
# ==========================================

genai.configure(api_key=Config.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


# ==========================================
# ESTIMATE TASK
# ==========================================

def estimate_task(title, description, deadline):
    """
    Analyze a task using Gemini and return:

    {
        estimated_minutes,
        priority,
        difficulty,
        reason
    }
    """

    prompt = f"""
You are an expert AI productivity assistant.

Analyze the following task.

Task Title:
{title}

Task Description:
{description}

Deadline:
{deadline}

Estimate:

1. Estimated time in minutes
2. Priority
3. Difficulty
4. Short reason

Return ONLY valid JSON.

Example:

{{
    "estimated_minutes": 180,
    "priority": "HIGH",
    "difficulty": "HARD",
    "reason": "Requires backend, frontend and database integration."
}}

Rules:

- estimated_minutes must be an integer.
- Priority must be HIGH, MEDIUM or LOW.
- Difficulty must be EASY, MEDIUM or HARD.
- Reason must be less than 20 words.
- Return JSON only.
- Do NOT use markdown.
- Do NOT wrap the JSON inside ```json.
"""

    try:

        response = model.generate_content(prompt)

        text = response.text.strip()

        # Remove markdown if Gemini accidentally returns it
        text = (
            text.replace("```json", "")
                .replace("```", "")
                .strip()
        )

        data = json.loads(text)

        return {

            "estimated_minutes": int(
                data.get("estimated_minutes", 60)
            ),

            "priority": (
                data.get("priority", "MEDIUM")
                .upper()
                .strip()
            ),

            "difficulty": (
                data.get("difficulty", "MEDIUM")
                .upper()
                .strip()
            ),

            "reason": data.get(
                "reason",
                "Estimated by AI."
            )

        }

    except Exception as e:

        print("\n========== GEMINI ERROR ==========")
        print(e)
        print("==================================\n")

        # Safe fallback values

        return {

            "estimated_minutes": 60,

            "priority": "MEDIUM",

            "difficulty": "MEDIUM",

            "reason": "AI estimation unavailable."

        }


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    result = estimate_task(

        "Build Flask Dashboard",

        "Create a responsive dashboard with Supabase, authentication, charts and analytics.",

        "2026-07-01"

    )

    print(json.dumps(result, indent=4))
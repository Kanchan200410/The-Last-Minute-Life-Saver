supabase.table("tasks").insert({
    "title": title,
    "description": description,
    "deadline": deadline,
    "status": "Pending"
}).execute()
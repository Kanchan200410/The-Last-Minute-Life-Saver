from database.supabase_client import supabase


def get_user(email):

    response = (
        supabase.table("users")
        .select("*")
        .eq("email", email)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def update_profile(email, name, username, bio, phone, profile_picture=None):

    data = {
        "name": name,
        "username": username,
        "bio": bio,
        "phone": phone
    }

    if profile_picture:
        data["profile_picture"] = profile_picture

    (
        supabase.table("users")
        .update(data)
        .eq("email", email)
        .execute()
    )
import requests, random, string, base64

# BASE_URL = "https://neobackend.fly.dev"
BASE_URL = "http://localhost:8080"
COMMON_PASS = "password123"

def fetch_image_as_base64(url: str) -> str:
    """Download an image from *url* and return it as a base64‑encoded string."""
    resp = requests.get(url)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")


def create_user(fullname: str, email: str, password: str,
                user_type: str, image_url: str, crefito: str = None) -> str | None:
    """Register a user; returns the user ID or ``None`` on failure."""
    profile_image_b64 = fetch_image_as_base64(image_url)

    payload = {
        "fullname": fullname,
        "email": email,
        "password": password,
        "user_type": user_type,
        "profile_image": profile_image_b64,
    }
    if crefito:
        payload["crefito"] = crefito

    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload)

        if resp.status_code == 201:
            user_id = resp.json()["id"]
            print(f"✅ Created {user_type}: {fullname} ({email}) → ID: {user_id}")
            return user_id
        if resp.status_code == 409:
            print(f"⚠️ User {email} already exists – logging in.")
            return login_and_get_id(email, password)
        print(f"❌ Failed to create {fullname}: {resp.text}")
    except Exception as exc:
        print(f"❌ Error while creating {fullname}: {exc}")
    return None


def login_and_get_id(email: str, password: str) -> str | None:
    """Log in and fetch the user’s ID via the ``/me`` endpoint."""
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        print(f"❌ Login failed for {email}")
        return None

    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = requests.get(f"{BASE_URL}/me", headers=headers)
    if me_resp.status_code == 200:
        return me_resp.json()["id"]
    return None


def get_token(email: str, password: str) -> str | None:
    """Return a JWT for the given credentials."""
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    return resp.json()["token"] if resp.status_code == 200 else None


def connect_users(scanner_token: str, target_id: str) -> None:
    """Create a relationship between the logged‑in user and *target_id*."""
    headers = {"Authorization": f"Bearer {scanner_token}"}
    payload = {"targetUserId": target_id}
    resp = requests.post(f"{BASE_URL}/api/relationships/connect", headers=headers, json=payload)

    if resp.status_code == 200:
        print(f"🔗 Connected to user ID {target_id}")
    else:
        print(f"❌ Connection failed for {target_id}: {resp.text}")


def main() -> None:
    # ----------------------------------------------------------------------
    # 1️⃣  Create the physiotherapist
    # ----------------------------------------------------------------------
    physio = {
        "fullname": "Caio Zampini",
        "email": f"caio@mail.com",
        "image": "https://raw.githubusercontent.com/zampini28/imagens/refs/heads/main/caio.jpeg",
        "crefito": f"314142-F",
    }

    physio_id = create_user(
        fullname=physio["fullname"],
        email=physio["email"],
        password=COMMON_PASS,
        user_type="PHYSIO",
        image_url=physio["image"],
        crefito=physio["crefito"],
    )
    if not physio_id:
        return

    physio_token = get_token(physio["email"], COMMON_PASS)

    # ----------------------------------------------------------------------
    # 2️⃣  Create the three patients
    # ----------------------------------------------------------------------
    patients = [
        {
            "fullname": "Augusto Junior",
            "email": f"augusto@mail.com",
            "image": "https://raw.githubusercontent.com/zampini28/imagens/refs/heads/main/augusto.jpeg",
        },
        {
            "fullname": "Ronald Ivan",
            "email": f"ronald@mail.com",
            "image": "https://raw.githubusercontent.com/zampini28/imagens/refs/heads/main/ronald.jpeg",
        },
        {
            "fullname": "Davi Ferreira",
            "email": f"davi@mail.com",
            "image": "https://raw.githubusercontent.com/zampini28/imagens/refs/heads/main/davi.jpeg",
        },
    ]

    patient_ids = []
    for p in patients:
        pid = create_user(
            fullname=p["fullname"],
            email=p["email"],
            password=COMMON_PASS,
            user_type="PATIENT",
            image_url=p["image"],
        )
        if pid:
            patient_ids.append(pid)

    # ----------------------------------------------------------------------
    # 3️⃣  Connect physiotherapist with each patient
    # ----------------------------------------------------------------------
    if physio_token:
        for pid in patient_ids:
            connect_users(physio_token, pid)

    # ----------------------------------------------------------------------
    # 4️⃣  Summary
    # ----------------------------------------------------------------------
    print("\n✅ Seeding complete.")
    print(f"Physiotherapist login: {physio['email']} / {COMMON_PASS}")
    for p in patients:
        print(f"Patient login: {p['email']} / {COMMON_PASS}")


if __name__ == "__main__":
    main()

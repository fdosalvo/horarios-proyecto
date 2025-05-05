import requests

# === Paso 1: Obtener el token de acceso desde la primera API ===
auth_url = "http://localhost/api/token/"
auth_payload = {
    "username": "fsalvo",
    "password": "xxxx"
}
auth_headers = {
    "Content-Type": "application/json"
}

print("🔍 Enviando solicitud para obtener token...")
print(f"URL: {auth_url}")
print(f"Payload: {auth_payload}")
print(f"Headers: {auth_headers}")

# Hacer solicitud para obtener token
auth_response = requests.post(auth_url, json=auth_payload, headers=auth_headers)

if auth_response.status_code == 200:
    # Extraer el token del JSON de respuesta
    auth_data = auth_response.json()
    access_token = auth_data.get("access")
    print(f"🔑 Token de acceso recibido: {access_token}")
    print(f"Respuesta completa: {auth_data}")

    # === Paso 2: Usar el token en otra API ===
    api_url = "http://localhost/api/apoderados/"
    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    print("\n🔍 Enviando solicitud GET a la API...")
    print(f"URL: {api_url}")
    print(f"Headers: {api_headers}")

    api_response = requests.get(api_url, headers=api_headers)

    if api_response.status_code == 200:
        print("✅ Respuesta de la segunda API:")
        print(api_response.json())
    else:
        print(f"❌ Error en la segunda API. Código: {api_response.status_code}")
        print(api_response.text)
else:
    print(f"❌ Error al obtener token. Código: {auth_response.status_code}")
    print(auth_response.text)


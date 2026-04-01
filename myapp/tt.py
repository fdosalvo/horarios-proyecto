import requests
import getpass
import json
import tkinter as tk
from tkinter import ttk, messagebox

def mostrar_json_en_grilla(json_data):
    # Si es un diccionario, lo convertimos en una lista de un solo elemento
    if isinstance(json_data, dict):
        json_data = [json_data]
    if not json_data:
        messagebox.showinfo("Sin datos", "No hay datos para mostrar.")
        return

    # Crear ventana principal
    root = tk.Tk()
    root.title("Datos de la API")

    # Crear Treeview
    columns = list(json_data[0].keys())
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    for item in json_data:
        values = [item.get(col, "") for col in columns]
        tree.insert("", tk.END, values=values)
    tree.pack(expand=True, fill="both")

    root.mainloop()

# === Paso 1: Solicitar password por pantalla ===
username = "fsalvo"
password = getpass.getpass(f"Ingrese la contraseña para el usuario '{username}': ")

auth_url = "http://localhost/api/token/"
auth_payload = {
    "username": username,
    "password": password
}
auth_headers = {
    "Content-Type": "application/json"
}

print("🔍 Enviando solicitud para obtener token...")
print(f"URL: {auth_url}")
print(f"Payload: {{'username': '{username}', 'password': '***'}}")
print(f"Headers: {auth_headers}")

# Hacer solicitud para obtener token
auth_response = requests.post(auth_url, json=auth_payload, headers=auth_headers)

if auth_response.status_code == 200:
    auth_data = auth_response.json()
    access_token = auth_data.get("access")
    print(f"🔑 Token de acceso recibido: {access_token}")
    print(f"Respuesta completa: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")

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
        data = api_response.json()
        # Mostrar en grilla Tkinter
        mostrar_json_en_grilla(data)
    else:
        print(f"❌ Error en la segunda API. Código: {api_response.status_code}")
        print(api_response.text)
else:
    print(f"❌ Error al obtener token. Código: {auth_response.status_code}")
    print(auth_response.text)
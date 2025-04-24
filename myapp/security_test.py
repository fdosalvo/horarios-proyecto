# security_test.py - Archivo de prueba con problemas de seguridad

import pyyaml  # Dependencia vulnerable (necesitaremos instalar una versión antigua)
import sqlite3
import eval  # Esto generará un error porque 'eval' no es un módulo, pero lo usaremos como ejemplo de uso inseguro

# Problema 1: Credenciales expuestas
API_KEY = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"  # Clave API falsa (similar a un formato de Stripe)

# Problema 2: Inyección SQL potencial
def get_user_data(user_input):
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    # Inyección SQL: user_input no está sanitizado
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    cursor.execute(query)  # Esto es vulnerable a inyección SQL
    return cursor.fetchall()

# Problema 3: Uso de eval() inseguro
def evaluate_user_input(user_input):
    # Esto es extremadamente inseguro: evalúa entrada del usuario sin validación
    result = eval(user_input)
    return result

# Problema 4: Uso de pyyaml vulnerable
def load_yaml_data(data):
    yaml = pyyaml.YAML()  # Usaremos una versión vulnerable de pyyaml
    return yaml.load(data)

if __name__ == "__main__":
    # Ejemplo de uso
    user_input = "test' OR '1'='1"  # Ejemplo de inyección SQL
    print(get_user_data(user_input))
    
    dangerous_input = "print('Hacked!')"  # Ejemplo de entrada peligrosa para eval()
    print(evaluate_user_input(dangerous_input))
    
    yaml_data = "!!python/object/apply:os.system ['echo Hacked by YAML']"
    print(load_yaml_data(yaml_data))
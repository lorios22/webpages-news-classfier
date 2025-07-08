# Configuración de API Key - Instrucciones

## ¿Qué falta?

El archivo `.env` ya está creado y configurado, pero necesitas agregar tu **API key real de OpenAI**.

## Pasos para configurar:

### 1. Obtén tu API key de OpenAI
- Ve a https://platform.openai.com/api-keys
- Crea una nueva API key si no tienes una
- Copia la API key completa (empieza con `sk-`)

### 2. Edita el archivo .env
Puedes usar cualquiera de estos métodos:

```bash
# Opción 1: Con VS Code (recomendado)
code .env

# Opción 2: Con nano
nano .env

# Opción 3: Con vim
vim .env

# Opción 4: Reemplazar directamente con sed
sed -i '' 's/your_openai_api_key_here/tu_api_key_real/' .env
```

### 3. Cambia esta línea:
```bash
# De:
OPENAI_API_KEY=your_openai_api_key_here

# A:
OPENAI_API_KEY=sk-tu_api_key_real_aqui
```

### 4. Guarda el archivo y prueba:
```bash
# Ejecutar pruebas
python3 test_mvp_fixes.py

# Si todo funciona, ejecutar pipeline completo
python3 scripts/run_full_pipeline.py
```

## Verificación

Para verificar que la configuración funciona:

```bash
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY', '')
if api_key and api_key != 'your_openai_api_key_here':
    print('✅ API Key configurada correctamente')
else:
    print('❌ API Key no configurada')
"
```

## Solución de Problemas

### Si las pruebas fallan:
1. Verifica que el archivo `.env` esté en el directorio raíz
2. Verifica que la API key sea válida
3. Verifica que tengas créditos en tu cuenta de OpenAI

### Si el archivo .env no se carga:
1. Verifica que `python-dotenv` esté instalado: `pip install python-dotenv`
2. Verifica que el archivo se llame exactamente `.env` (con el punto al inicio)

## Estado Actual del Sistema

✅ **FUNCIONANDO:**
- Archivo .env creado y configurado
- Sistema de carga de variables de entorno
- Sistema de duplicados (no necesita API key)
- FIN integration (no necesita API key)  
- Truncado de contenido (no necesita API key)
- Limpieza de contenido (no necesita API key)

❌ **PENDIENTE:**
- Solo falta configurar tu API key real de OpenAI

Una vez configurada la API key, el sistema debería funcionar completamente. 
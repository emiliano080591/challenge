# Troubleshooting

- `ValidationError: OPENAI_API_KEY missing`
Asegúrate de que .env está en la raíz y que arrancas desde la raíz, o que tu `config.py` carga `.env` por ruta absoluta. También puedes exportar la variable en shell.
- `500 Internal Server Error en /api/chat` 
Revisa logs (`make logs`). Si es OpenAI, valida tu API key. Si es DB, confirma `DATABASE_URL`.
En local, SQLite (`local.db`) se crea automáticamente. En Docker, usa Postgres del compose.
- **Prometheus no ve la API**
En el compose unificado no deberías tocar nada: el target es `api:8000`.
Verifica en **Prometheus → Status → Targets** que `kopi-api` esté UP.
- **No aparece “Import” en Grafana**
Estás como anónimo Viewer. Inicia sesión (`admin/admin` si configuraste) o eleva rol anónimo a Editor para desarrollo.
- **Actualicé métricas pero Grafana no cambia**
`make rebuild` para reconstruir la imagen de la API y reiniciar.
Verifica en http://localhost:8000/metrics
 que las nuevas métricas existan.
En Prometheus, usa la lupa para buscarlas por nombre.
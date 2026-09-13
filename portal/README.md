# Liverpool Seguimiento · Goldval

Portal privado para consultar pedidos, guías, incidencias y entregas de Liverpool Marketplace.

```bash
npm install
copy .env.example .env.local
npm run dev
```

Variables requeridas: `INSFORGE_URL`, `INSFORGE_API_KEY`, `PORTAL_TOKEN`, `PORTAL_USER` y `PORTAL_PASSWORD`.

El seguimiento se ejecuta en InsForge: ciclo diario a las 06:00 de Ciudad de México y reintentos cada 15 minutos.

# Apex 25 online

Servidor Node.js que sirve el juego y conecta a los jugadores por WebSocket. Cualquiera con el link puede jugar, sin cuenta.

## Probar en tu PC
```
npm install
npm start
```
Abrí http://localhost:3000. Para jugar con amigos en tu misma red wifi, que entren a `http://TU-IP-LOCAL:3000`.

## Publicarlo en internet
Subí esta carpeta a un hosting que soporte WebSockets y Node 18 o más (Render, Railway, Fly.io, un VPS):
- Comando de instalación: `npm install`
- Comando de inicio: `npm start`
- El puerto se toma de la variable `PORT`.

Con HTTPS el juego usa `wss://` automáticamente. Compartí el link, uno crea la sala y los demás entran con el código.

## Notas
- Hasta 21 jugadores por sala. El anfitrión es quien creó la sala (si se va, pasa a otro jugador).
- Cada jugador calcula su propio auto y el servidor solo retransmite posiciones. Es práctico para jugar con amigos, pero un jugador podría hacer trampa modificando su cliente.
- Endpoint `/health` para los chequeos del hosting.

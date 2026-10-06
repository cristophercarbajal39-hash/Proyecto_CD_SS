const ACAPULCO = [16.8531, -99.8237];
const RADIO_LOCAL_KM = 60;  // más allá de esto se considera "fuera de Acapulco"
const map = L.map('map').setView(ACAPULCO, 11);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; OpenStreetMap'}).addTo(map);
const msg = document.getElementById('msg'), lista = document.getElementById('cercanas');
let casa = null, pin = null, sedes = [];

const km = (a, b) => {  // haversine
  const r = Math.PI / 180, dla = (b[0]-a[0])*r, dlo = (b[1]-a[1])*r;
  const h = Math.sin(dla/2)**2 + Math.cos(a[0]*r)*Math.cos(b[0]*r)*Math.sin(dlo/2)**2;
  return 12742 * Math.asin(Math.sqrt(h));
};
const etiqueta = s => s.sede ? `${s.nombre} (${s.sede})` : s.nombre;
const cercanas = () => sedes.map(s => ({s, k: km(casa, [s.lat, s.lon])})).sort((a, b) => a.k - b.k);

function listar() {
  lista.innerHTML = '';
  if (!casa) return;
  cercanas().slice(0, 10).forEach(({s, k}) => {
    const li = document.createElement('li');
    li.textContent = `${etiqueta(s)}: ${k.toFixed(1)} km en línea recta`;
    lista.appendChild(li);
  });
}

function fijar(ll, texto) {
  casa = ll;
  if (pin) pin.setLatLng(ll);
  else pin = L.circleMarker(ll, {radius: 9, color: '#fff', weight: 3, fillColor: '#1b3b6b', fillOpacity: 1})
    .addTo(map).bindTooltip('Tu ubicación');
  const lejos = km(ll, ACAPULCO);
  if (lejos <= RADIO_LOCAL_KM) {
    map.fitBounds([ll, ...cercanas().slice(0, 3).map(({s}) => [s.lat, s.lon])], {padding: [50, 50], maxZoom: 15});
    msg.textContent = texto;
  } else {
    map.setView(ACAPULCO, 11);
    msg.textContent = `Tu ubicación está a ${Math.round(lejos)} km de Acapulco. Haz clic en el mapa para marcar tu casa en Acapulco.`;
  }
  listar();
}

function localizar() {
  if (!navigator.geolocation) { msg.textContent = 'Tu navegador no permite geolocalización. Haz clic en el mapa para marcar tu casa.'; return; }
  msg.textContent = 'Buscando tu ubicación…';
  navigator.geolocation.getCurrentPosition(
    p => fijar([p.coords.latitude, p.coords.longitude], 'Ubicación detectada. Solo se usa en tu navegador y no se guarda.'),
    e => { msg.textContent = e.code === 1 ? 'No diste permiso de ubicación. Haz clic en el mapa para marcar tu casa.'
                                          : 'No se pudo obtener tu ubicación. Haz clic en el mapa para marcar tu casa.'; },
    {timeout: 10000, maximumAge: 60000});
}

map.on('click', e => {
  const ll = [e.latlng.lat, e.latlng.lng];
  try { localStorage.setItem('casa', JSON.stringify(ll)); } catch (_) {}
  fijar(ll, 'Casa marcada. Se guarda solo en tu navegador.');
});
document.getElementById('gps').addEventListener('click', localizar);
document.getElementById('olvidar').addEventListener('click', () => {
  try { localStorage.removeItem('casa'); } catch (_) {}
  if (pin) { pin.remove(); pin = null; } casa = null; lista.innerHTML = '';
  map.setView(ACAPULCO, 11);
  msg.textContent = 'Ubicación borrada. Pulsa «Usar mi ubicación» o marca tu casa en el mapa.';
});

async function iniciar() {
  const deps = await fetch('/api/dependencias').then(r => r.json());
  sedes = deps.flatMap(d => (d.sedes || []).map(s => ({nombre: d.nombre, sede: s.nombre, lat: s.lat, lon: s.lon})));
  sedes.forEach(s => {
    const el = document.createElement('div'), b = document.createElement('strong');
    b.textContent = s.nombre; el.append(b);
    if (s.sede) el.append(document.createElement('br'), s.sede);
    L.marker([s.lat, s.lon]).addTo(map).bindPopup(el);
  });
  // 1) casa marcada antes por el alumno  2) ubicación del dispositivo (pide permiso)
  let guardada = null;
  try { guardada = JSON.parse(localStorage.getItem('casa')); } catch (_) {}
  if (Array.isArray(guardada)) return fijar(guardada, 'Usando tu casa guardada. Pulsa «Usar mi ubicación» para cambiar.');
  if (navigator.permissions) {
    try {
      const p = await navigator.permissions.query({name: 'geolocation'});
      if (p.state === 'denied') { msg.textContent = 'El permiso de ubicación está bloqueado. Haz clic en el mapa para marcar tu casa.'; return; }
    } catch (_) {}
  }
  localizar();
}
iniciar();

import L from 'leaflet';
import 'leaflet-rotate';

document.addEventListener('htmx:load', (ev) => {
    const mapElList = ev.detail.elt.querySelectorAll('.map');
    [...mapElList].map((mapEl) => {
        const draggable = mapEl.dataset.draggable;
        const initialZoom = parseInt(mapEl.dataset.initialZoom) || 13;        

        var lat, mapLatInputEl;
        if (mapEl.dataset.latitude && isNaN(mapEl.dataset.latitude)) {
            var mapLatInputEl = document.querySelector(mapEl.dataset.latitude);
            lat = parseFloat(mapLatInputEl.value) || 0;
        } else{
            lat = parseFloat(mapEl.dataset.latitude);
        }

        var lon, mapLonInputEl;
        if (mapEl.dataset.longitude && isNaN(mapEl.dataset.longitude)) {
            var mapLonInputEl = document.querySelector(mapEl.dataset.longitude);
            lon = parseFloat(mapLonInputEl.value) || 0;
        } else{
            lon = parseFloat(mapEl.dataset.longitude);
        }

        var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 20,
            maxNativeZoom: 19,
            opacity: 0.75,
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        });

        const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.jpg', {
            maxZoom: 20,
            maxNativeZoom: 18,
            attribution: '© Tile: Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
        });

        const map = L.map(mapEl, { center: [lat, lon], layers: [sat, osm], zoom: initialZoom });

        const marker = L.marker([lat, lon], { draggable, autoPan: true }).addTo(map);

        if (mapLatInputEl !== undefined) {
            mapLatInputEl.addEventListener('change', (ev) => {
                const lat = parseFloat(ev.target.value) || 0;

                map.panTo([lat, lon]);
                marker.setLatLng([lat, lon]);
            });

            if (draggable) {
                marker.addEventListener('dragend', (ev) => mapLatInputEl.value = marker.getLatLng().lat.toFixed(4));
            }
        }

        if (mapLonInputEl !== undefined) {
            mapLonInputEl.addEventListener('change', (ev) => {
                const lon = parseFloat(ev.target.value) || 0;

                map.panTo([lat, lon]);
                marker.setLatLng([lat, lon]);
            });

            if (draggable) {
                marker.addEventListener('dragend', (ev) => mapLonInputEl.value = marker.getLatLng().lng.toFixed(4));
            }
        }
    });
});

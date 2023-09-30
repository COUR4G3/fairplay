import L from 'leaflet';

document.addEventListener('htmx:load', (ev) => {
    const mapElList = ev.detail.elt.querySelectorAll('.map');
    [...mapElList].map((mapEl) => {
        const mapContainerEl = mapEl.querySelector('.map-container');

        const draggable = mapEl.dataset.draggable;
        const initialZoom = parseInt(mapEl.dataset.initialZoom) || 13;        

        var lat, mapLatInputEl;
        if (mapEl.dataset.latitude && isNaN(mapEl.dataset.latitude)) {
            var mapLatInputEl = mapEl.querySelector(mapEl.dataset.latitude);
            if (mapLatInputEl === undefined) {
                mapLatInputEl = document.querySelector(mapEl.dataset.latitude);
            }
            lat = parseFloat(mapLatInputEl.value) || 0;
        } else{
            lat = parseFloat(mapEl.dataset.latitude);
        }

        var lon, mapLonInputEl;
        if (mapEl.dataset.longitude && isNaN(mapEl.dataset.longitude)) {
            var mapLonInputEl = mapEl.querySelector(mapEl.dataset.longitude);
            if (mapLonInputEl === undefined) {
                mapLonInputEl = document.querySelector(mapEl.dataset.longitude);
            }
            lon = parseFloat(mapLonInputEl.value) || 0;
        } else{
            lon = parseFloat(mapEl.dataset.longitude);
        }

        const map = L.map(mapContainerEl, { center: [lat, lon], zoom: initialZoom });

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        const marker = L.marker([lat, lon], { draggable, autoPan: true }).addTo(map);

        if (mapLatInputEl !== undefined) {
            mapLatInputEl.addEventListener('change', (ev) => {
                const lat = parseFloat(ev.target.value) || 0;

                map.panTo([lat, lon]);
                marker.setLatLng([lat, lon]);
            });

            if (draggable) {
                marker.addEventListener('dragend', (ev) => mapLatInputEl.value = marker.getLatLng().lat.toFixed(3));
            }
        }

        if (mapLonInputEl !== undefined) {
            mapLonInputEl.addEventListener('change', (ev) => {
                const lon = parseFloat(ev.target.value) || 0;

                map.panTo([lat, lon]);
                marker.setLatLng([lat, lon]);
            });

            if (draggable) {
                marker.addEventListener('dragend', (ev) => mapLonInputEl.value = marker.getLatLng().lng.toFixed(3));
            }
        }
    });
});

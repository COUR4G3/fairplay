import maplibregl from 'maplibre-gl';


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

        const map = new maplibregl.Map({
            container: mapEl,
            style: 'https://api.maptiler.com/maps/bright-v2/style.json?key=2JkTIhBjBIY6hGQ9h2t6',
            center: [lon, lat],
            zoom: (lon || lat) ? initialZoom : 2
        });

        map.addControl(new maplibregl.FullscreenControl());
        map.addControl(new maplibregl.NavigationControl());

        const geolocate = new maplibregl.GeolocateControl();
        map.addControl(geolocate);

        if (!lat && !lon) {
            map.on('load', () => geolocate.trigger());
        }

        const marker = new maplibregl.Marker({ color: "var(--bs-primary)", draggable });
        marker.setLngLat([lon, lat]).addTo(map);

        map.doubleClickZoom.disable();
        map.on('dblclick', function(e) {
            const { lng: lon, lat } = e.lngLat;

            map.panTo([lon, lat]);
            marker.setLngLat([lon, lat]);

            if (mapLatInputEl !== undefined) {
                mapLatInputEl.value = lat.toFixed(4);
            }

            if (mapLonInputEl !== undefined) {
                mapLonInputEl.value = lon.toFixed(4);
            }
        });

        if (mapLatInputEl !== undefined) {
            mapLatInputEl.addEventListener('change', (ev) => {
                const lat = parseFloat(ev.target.value) || 0;

                map.panTo([lon, lat]);
                marker.setLngLat([lon, lat]);
            });

            if (draggable) {
                marker.on('dragend', (ev) => mapLatInputEl.value = marker.getLngLat().lat.toFixed(4));
            }
        }

        if (mapLonInputEl !== undefined) {
            mapLonInputEl.addEventListener('change', (ev) => {
                const lon = parseFloat(ev.target.value) || 0;

                map.panTo()

                map.panTo([lon, lat]);
                marker.setLngLat([lon, lat]);
            });

            if (draggable) {
                marker.on('dragend', (ev) => mapLonInputEl.value = marker.getLngLat().lng.toFixed(4));
            }
        }
    });
});

/* ==================== HERBARIO ESPOCH - MAPAS DE GEOLOCALIZACIÓN ==================== */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {

        // ==================== INICIALIZAR MAPA PRINCIPAL ====================
        const mapContainer = document.getElementById('herbario-map');
        
        if (mapContainer && typeof L !== 'undefined') {
            initializeMap();
        }

        function initializeMap() {
            // Obtener datos de ubicaciones desde el elemento data
            const mapData = document.getElementById('herbario-map-data');
            let locations = [];
            
            if (mapData) {
                try {
                    locations = JSON.parse(mapData.textContent);
                } catch (e) {
                    console.error('Error al parsear datos del mapa:', e);
                    return;
                }
            }

            if (locations.length === 0) {
                mapContainer.innerHTML = '<div class="herbario-map-empty">No hay ubicaciones con coordenadas GPS disponibles.</div>';
                return;
            }

            // Centro de Ecuador por defecto
            const defaultCenter = [-1.8312, -78.1834];
            const defaultZoom = 7;

            // Crear mapa
            const map = L.map('herbario-map').setView(defaultCenter, defaultZoom);

            // Agregar capa de tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(map);

            // Crear cluster de marcadores
            let markers = L.markerClusterGroup({
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true
            });

            // Agregar marcadores
            locations.forEach(function(location) {
                if (location.lat && location.lng) {
                    const marker = L.marker([location.lat, location.lng]);
                    
                    // Popup con información
                    const popupContent = `
                        <div class="herbario-map-popup">
                            <h4 class="herbario-map-popup-title">${location.name}</h4>
                            <p class="herbario-map-popup-location">
                                <strong>Localidad:</strong> ${location.locality}<br>
                                <strong>Provincia:</strong> ${location.provincia}
                            </p>
                            <p class="herbario-map-popup-coords">
                                <small>Lat: ${location.lat.toFixed(6)}, Lng: ${location.lng.toFixed(6)}</small>
                            </p>
                        </div>
                    `;
                    
                    marker.bindPopup(popupContent);
                    markers.addLayer(marker);
                }
            });

            map.addLayer(markers);

            // Ajustar vista para mostrar todos los marcadores
            if (locations.length > 0) {
                const bounds = markers.getBounds();
                if (bounds.isValid()) {
                    map.fitBounds(bounds, { padding: [50, 50] });
                }
            }

            // ==================== CONTROLES ADICIONALES ====================
            
            // Control de pantalla completa
            L.control.fullscreen({
                position: 'topleft',
                title: 'Ver en pantalla completa',
                titleCancel: 'Salir de pantalla completa'
            }).addTo(map);

            // Control de escala
            L.control.scale({
                metric: true,
                imperial: false,
                position: 'bottomleft'
            }).addTo(map);

            // ==================== FILTRAR MARCADORES ====================
            const provinceFilter = document.getElementById('herbario-map-province-filter');
            if (provinceFilter) {
                provinceFilter.addEventListener('change', function() {
                    const selectedProvince = this.value;
                    
                    markers.clearLayers();
                    
                    const filteredLocations = selectedProvince 
                        ? locations.filter(loc => loc.provincia === selectedProvince)
                        : locations;
                    
                    filteredLocations.forEach(function(location) {
                        if (location.lat && location.lng) {
                            const marker = L.marker([location.lat, location.lng]);
                            const popupContent = `
                                <div class="herbario-map-popup">
                                    <h4 class="herbario-map-popup-title">${location.name}</h4>
                                    <p class="herbario-map-popup-location">
                                        <strong>Localidad:</strong> ${location.locality}<br>
                                        <strong>Provincia:</strong> ${location.provincia}
                                    </p>
                                </div>
                            `;
                            marker.bindPopup(popupContent);
                            markers.addLayer(marker);
                        }
                    });
                    
                    map.addLayer(markers);
                    
                    if (filteredLocations.length > 0) {
                        const bounds = markers.getBounds();
                        if (bounds.isValid()) {
                            map.fitBounds(bounds, { padding: [50, 50] });
                        }
                    }
                });
            }

            // ==================== MAPA DE CALOR ====================
            const heatmapToggle = document.getElementById('herbario-map-heatmap-toggle');
            let heatLayer = null;
            
            if (heatmapToggle && typeof L.heatLayer !== 'undefined') {
                heatmapToggle.addEventListener('change', function() {
                    if (this.checked) {
                        // Crear capa de calor
                        const heatData = locations
                            .filter(loc => loc.lat && loc.lng)
                            .map(loc => [loc.lat, loc.lng, 1]);
                        
                        heatLayer = L.heatLayer(heatData, {
                            radius: 25,
                            blur: 15,
                            maxZoom: 17,
                            gradient: {
                                0.0: '#2d5f3f',
                                0.5: '#5a8c6f',
                                1.0: '#8fbc8f'
                            }
                        }).addTo(map);
                        
                        markers.remove();
                    } else {
                        // Remover capa de calor
                        if (heatLayer) {
                            map.removeLayer(heatLayer);
                            heatLayer = null;
                        }
                        map.addLayer(markers);
                    }
                });
            }

            // ==================== EXPORTAR MAPA ====================
            const exportMapBtn = document.getElementById('herbario-map-export');
            if (exportMapBtn) {
                exportMapBtn.addEventListener('click', function() {
                    // Usar leaflet-image o similar para exportar
                    alert('Función de exportación en desarrollo');
                });
            }
        }

        // ==================== MAPA EN DETALLE DE ESPÉCIMEN ====================
        const detailMapContainer = document.getElementById('herbario-detail-map');
        
        if (detailMapContainer && typeof L !== 'undefined') {
            initializeDetailMap();
        }

        function initializeDetailMap() {
            const mapData = detailMapContainer.dataset;
            const lat = parseFloat(mapData.lat);
            const lng = parseFloat(mapData.lng);
            const name = mapData.name || '';
            const locality = mapData.locality || '';

            if (!lat || !lng) {
                detailMapContainer.innerHTML = '<div class="herbario-map-empty">No hay coordenadas GPS disponibles.</div>';
                return;
            }

            const map = L.map('herbario-detail-map').setView([lat, lng], 13);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(map);

            const marker = L.marker([lat, lng]).addTo(map);
            
            const popupContent = `
                <div class="herbario-map-popup">
                    <h4 class="herbario-map-popup-title">${name}</h4>
                    <p class="herbario-map-popup-location">${locality}</p>
                    <p class="herbario-map-popup-coords">
                        <small>Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}</small>
                    </p>
                    <a href="https://www.google.com/maps?q=${lat},${lng}" target="_blank" class="herbario-map-popup-link">
                        Abrir en Google Maps
                    </a>
                </div>
            `;
            
            marker.bindPopup(popupContent).openPopup();

            // Control de escala
            L.control.scale({
                metric: true,
                imperial: false,
                position: 'bottomleft'
            }).addTo(map);
        }

        // ==================== CARGAR LEAFLET SI NO ESTÁ DISPONIBLE ====================
        if (!window.L && (mapContainer || detailMapContainer)) {
            loadLeaflet();
        }

        function loadLeaflet() {
            // Cargar CSS
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            document.head.appendChild(link);

            // Cargar JS
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            script.onload = function() {
                // Cargar plugins adicionales
                loadLeafletPlugins();
            };
            document.head.appendChild(script);
        }

        function loadLeafletPlugins() {
            // Leaflet MarkerCluster
            const clusterCSS = document.createElement('link');
            clusterCSS.rel = 'stylesheet';
            clusterCSS.href = 'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css';
            document.head.appendChild(clusterCSS);

            const clusterJS = document.createElement('script');
            clusterJS.src = 'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js';
            clusterJS.onload = function() {
                // Reinicializar mapas después de cargar plugins
                if (mapContainer) initializeMap();
                if (detailMapContainer) initializeDetailMap();
            };
            document.head.appendChild(clusterJS);
        }

    });

})();

/* ==================== ESTILOS CSS PARA MAPAS ==================== */
const style = document.createElement('style');
style.textContent = `
    .herbario-map-empty {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 400px;
        background: #f8f9fa;
        border: 2px dashed #ddd;
        border-radius: 8px;
        color: #666;
        font-size: 1.1rem;
    }
    
    .herbario-map-popup {
        min-width: 200px;
    }
    
    .herbario-map-popup-title {
        font-weight: bold;
        font-style: italic;
        color: #2d5f3f;
        margin-bottom: 10px;
        font-size: 1.1rem;
    }
    
    .herbario-map-popup-location {
        margin: 8px 0;
        font-size: 0.9rem;
    }
    
    .herbario-map-popup-coords {
        margin: 8px 0;
        color: #666;
    }
    
    .herbario-map-popup-link {
        display: inline-block;
        margin-top: 10px;
        padding: 5px 10px;
        background: #2d5f3f;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    
    .herbario-map-popup-link:hover {
        background: #1b3a2d;
        color: white;
    }
    
    .leaflet-container {
        font-family: 'Roboto', Arial, sans-serif;
    }
`;
document.head.appendChild(style);
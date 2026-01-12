/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { loadJS } from "@web/core/assets";

publicWidget.registry.HerbarioStatistics = publicWidget.Widget.extend({
    selector: '#herbario_statistics_section',
    events: {
        'click #stats_apply_filters': '_onApplyFilters',
        'click #stats_clear_filters': '_onClearFilters',
        'click .dropdown-item-chart-group': '_onChangeChartGroup',
        'click #dropdownGroupButton': '_onToggleDropdown',
        'click .map-detail-link': '_onMapDetailClick', // Delegar evento al widget
    },

    start: function () {
        console.log('✓ HerbarioStatistics Widget iniciado');
        this.chart = null;
        this.map = null;
        this.currentFilters = {};
        this.chartGroupBy = 'family';
        
        // Esperar a que las bibliotecas estén cargadas
        this._ensureLibraries().then(() => {
            console.log('✓ Todas las bibliotecas cargadas');
            return this._fetchInitialData();
        }).catch((error) => {
            console.error('✗ Error cargando bibliotecas:', error);
        });
        
        return this._super.apply(this, arguments);
    },

    _ensureLibraries: function() {
        console.log('Verificando bibliotecas necesarias...');
        
        // Verificar si jQuery está disponible (usando el $ de Odoo)
        if (typeof window.$ === 'undefined') {
            console.warn('jQuery ($) no está disponible, usando jQuery de Odoo');
            if (typeof odoo !== 'undefined' && odoo.$) {
                window.$ = window.jQuery = odoo.$;
            } else {
                console.error('jQuery no disponible en ningún namespace');
                return Promise.reject('jQuery no disponible');
            }
        }
        
        // Verificar y cargar Select2 si es necesario
        if (typeof $.fn.select2 === 'undefined') {
            console.log('Select2 no disponible, cargando...');
            return new Promise((resolve, reject) => {
                loadJS('/web/static/lib/select2/select2.js').then(() => {
                    console.log('✓ Select2 cargado');
                    // También cargar CSS
                    $('head').append('<link rel="stylesheet" href="/web/static/lib/select2/select2.css" />');
                    resolve();
                }).catch((error) => {
                    console.error('✗ Error cargando Select2:', error);
                    reject(error);
                });
            });
        }
        
        // Verificar Chart.js
        if (typeof Chart === 'undefined') {
            console.log('Chart.js no disponible');
            return loadJS('https://cdn.jsdelivr.net/npm/chart.js');
        }
        
        // Verificar Leaflet
        if (typeof L === 'undefined') {
            console.log('Leaflet no disponible');
            return loadJS('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
        }
        
        return Promise.resolve();
    },

    _onToggleDropdown: function(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        
        var $menu = this.$('#chart_group_selector');
        var isVisible = $menu.is(':visible');
        
        if (isVisible) {
            $menu.hide();
        } else {
            $menu.show();
        }
    },

    _fetchInitialData: function() {
        var self = this;
        console.log('Obteniendo opciones de filtros...');
        
        return jsonrpc('/herbario/api/filter_options', {}).then(function (options) {
            if (!self.el) return; // Seguridad
            console.log('✓ Opciones recibidas:', Object.keys(options));
            self._renderFilters(options);
            return self._fetchData();
        }).catch(function(error) {
            console.error('✗ Error al obtener opciones:', error);
        });
    },

    _renderFilters: function(options) {
        if (!this.el) return;
        console.log('Renderizando filtros...');
        
        // Función auxiliar para crear selects
        const createSelect = (id, label, opts) => {
            let optionsHtml = (opts || []).map(o => 
                `<option value="${o}">${o}</option>`
            ).join('');
            
            return `
                <div class="form-group mb-2">
                    <label for="${id}" class="form-label small fw-bold text-muted mb-1">${label}</label>
                    <select id="${id}" class="form-control stats-filter-select" multiple="multiple">
                        <option value=""></option>
                        ${optionsHtml}
                    </select>
                </div>`;
        };

        const filtersHtml = `
            ${createSelect('filter_family', 'Familia', options.families)}
            ${createSelect('filter_genus', 'Género', options.genera)}
            ${createSelect('filter_species', 'Especie', options.species)}
            ${createSelect('filter_author', 'Autor', options.authors)}
            ${createSelect('filter_determiner', 'Determinador', options.determiners)}
            ${createSelect('filter_collector', 'Colector', options.collectors)}
            ${createSelect('filter_country', 'País', options.countries)}
            ${createSelect('filter_province', 'Provincia', options.provinces)}
            ${createSelect('filter_herbarium', 'Herbario', options.herbaria)}
            ${createSelect('filter_index', 'Index', options.indices)}
            <div class="row mt-3 g-2">
                <div class="col-6">
                    <button type="button" id="stats_clear_filters" class="btn btn-secondary w-100"><i class="fa fa-eraser"></i> Limpiar</button>
                </div>
                <div class="col-6">
                    <button type="button" id="stats_apply_filters" class="btn btn-primary w-100" style="background-color: #0F5132; border-color: #0F5132;"><i class="fa fa-check"></i> Aplicar</button>
                </div>
            </div>
        `;

        this.$('#stats_filters_content').html(filtersHtml);

        // Inicializar Select2 con retry
        var self = this;
        this._initSelect2WithRetry();
    },

    _initSelect2WithRetry: function(attempt = 0) {
        if (attempt > 10) {
            console.warn('✗ No se pudo inicializar Select2 después de 10 intentos');
            return;
        }
        
        if (typeof $.fn.select2 !== 'undefined') {
            console.log('✓ Inicializando Select2 (intento ' + (attempt + 1) + ')');
            this.$('.stats-filter-select').select2({
                placeholder: 'Seleccione una o más opciones',
                allowClear: true,
                width: '100%'
            });
            console.log('✓ Select2 inicializado correctamente');
        } else {
            console.log('Esperando Select2... (intento ' + (attempt + 1) + ')');
            setTimeout(() => {
                this._initSelect2WithRetry(attempt + 1);
            }, 300);
        }
    },

    _fetchData: function () {
        var self = this;
        if (!this.el) return;
        console.log('Obteniendo datos - Filtros:', this.currentFilters, '| Agrupación:', this.chartGroupBy);
        
        // Mostrar loading
        this.$('#stats_main_content').addClass('position-relative');
        this.$('#stats_main_content').append(`
            <div class="loading-overlay" style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255,255,255,0.8);
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
            </div>
        `);

        return jsonrpc('/herbario/api/statistics_data', {
            filters: this.currentFilters,
            group_by: this.chartGroupBy,
        }).then(function (data) {
            if (!self.el) return;
            console.log('✓ Datos recibidos');
            self._updateChart(data.chart_data);
            self._updateMap(data.map_points);
            self.$('.loading-overlay').remove();
        }).catch(function(error) {
            console.error('✗ Error al obtener datos:', error);
            if (self.el) self.$('.loading-overlay').remove();
        });
    },

    _updateChart: function(chartData) {
        if (!this.el) return;
        console.log('Actualizando gráfico...');
        const ctx = this.el.querySelector('#familyChart');
        if (!ctx) {
            console.error('✗ Canvas #familyChart no encontrado');
            return;
        }
        
        const groupName = this.chartGroupBy.charAt(0).toUpperCase() + this.chartGroupBy.slice(1);
        this.$('#chart_title').text(`Especímenes por ${groupName}`);
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Verificar que Chart.js esté disponible
        if (typeof Chart === 'undefined') {
            console.error('✗ Chart.js no disponible');
            return;
        }
        
        this.chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: chartData.labels.slice(0, 20), // Limitar a 20 elementos
                datasets: [{ 
                    label: 'Nº de Especímenes', 
                    data: chartData.values.slice(0, 20),
                    backgroundColor: 'rgba(15, 81, 50, 0.7)',
                    borderColor: 'rgba(15, 81, 50, 1)',
                    borderWidth: 1
                }]
            },
            options: { 
                indexAxis: 'y', 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        console.log('✓ Gráfico actualizado');
    },

    _updateMap: function (mapPoints) {
        if (!this.el) return;
        console.log('Actualizando mapa con', mapPoints.length, 'puntos');
        
        // Verificar que Leaflet esté disponible
        if (typeof L === 'undefined') {
            console.error('✗ Leaflet no disponible');
            return;
        }
        
        if (!this.map) {
            // Inicializar mapa si no existe
            this.map = L.map('leaflet_map').setView([-1.8312, -78.1834], 7);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);
            this.markersLayer = L.layerGroup().addTo(this.map);
        } else {
            // Limpiar marcadores existentes
            this.markersLayer.clearLayers();
        }
        
        // Añadir nuevos marcadores
        mapPoints.forEach(point => {
            var marker = L.marker([point.lat, point.lng]).addTo(this.markersLayer);
            
            // Crear popup con evento para el detalle
            var popupContent = point.popup;
            marker.bindPopup(popupContent);
            
            // Añadir evento para mostrar detalle al hacer clic en el popup
            marker.on('popupopen', function(e) {
                var popup = e.popup;
                var popupElement = popup.getElement();
                $(popupElement).find('.map-detail-link').on('click', function(ev) {
                    ev.preventDefault();
                    var specimenId = $(this).data('specimen-id');
                    if (specimenId) {
                        // Redirigir directamente a la página del espécimen
                        window.location.href = '/herbario/specimen/' + specimenId;
                    }
                }.bind(this));
            }.bind(this));
        });
        
        // Ajustar vista del mapa si hay puntos
        if (mapPoints.length > 0) {
            var bounds = L.latLngBounds(mapPoints.map(p => [p.lat, p.lng]));
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
        
        console.log('✓ Mapa actualizado');
    },

    _onApplyFilters: function () {
        console.log('✓ Aplicando filtros...');
        this.currentFilters = {
            family: this.$('#filter_family').val(),
            genus: this.$('#filter_genus').val(),
            species: this.$('#filter_species').val(),
            author: this.$('#filter_author').val(),
            determiner: this.$('#filter_determiner').val(),
            collector: this.$('#filter_collector').val(),
            country: this.$('#filter_country').val(),
            province: this.$('#filter_province').val(),
            herbarium: this.$('#filter_herbarium').val(),
            index: this.$('#filter_index').val(),
        };
        this._fetchData();
    },

    _onClearFilters: function() {
        console.log('✓ Limpiando filtros...');
        this.currentFilters = {};
        
        // Limpiar controles de filtro
        this.$('.stats-filter-select').val(null).trigger('change');
        
        this._fetchData();
    },

    _onChangeChartGroup: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const $target = $(ev.currentTarget);
        const group = $target.data("group");
        
        console.log('✓ Cambiando agrupación a:', group);

        this.chartGroupBy = group;
        this.$('#chart_group_selector a').removeClass('active');
        $target.addClass('active');
        this.$('#chart_group_selector').hide();

        this._fetchData();
    },

    _onMapDetailClick: function(ev) {
        ev.preventDefault();
        const specimenId = $(ev.currentTarget).data('specimen-id');
        if (specimenId) {
            console.log('✓ Redirigiendo al detalle del espécimen:', specimenId);
            window.location.href = '/herbario/specimen/' + specimenId;
        }
    },
});

export default publicWidget.registry.HerbarioStatistics;
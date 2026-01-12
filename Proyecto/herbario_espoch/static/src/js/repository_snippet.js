/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.HerbarioRepository = publicWidget.Widget.extend({
    selector: '.s_herbario_repository',
    disabledInEditableMode: false, // Permite que el snippet se ejecute en modo edición
    events: {
        'click #herbario_apply_filters': '_onApplyFilters',
        'click #herbario_clear_filters': '_onClearFilters',
        'click .herbario-page-link': '_onPageClick',
        'click .btn_view_cards': '_onViewChange',
        'click .btn_view_table': '_onViewChange',
        'change .herbario_filters_sidebar select': '_onApplyFilters', // Actualizar al cambiar selección
    },

    /**0
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);

        // Estado inicial del widget
        this.currentPage = 1;
        this.currentFilters = {};
        this.currentView = 'cards'; // Estado para la vista: 'cards' o 'table'
        this.currentSpecimens = []; // Almacena los especímenes actuales

        // El modo de edición se detecta con 'this.editableMode'
        if (this.editableMode) {
            // En modo edición, renderizamos datos de ejemplo para visualización.
            this._renderExample();
        } else {
            // En modo público, hacemos la llamada RPC para obtener datos reales.
            this._fetchData();
        }

        return def;
    },
    /**
     * Obtiene los datos de los especímenes desde el controlador y los renderiza.
     * @private
     */
    _fetchData: function () {
        var self = this;
        if (!this.el) return; // Seguridad: Verificar que el widget existe

        const resultsContainer = this.el.querySelector('.herbario_results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div></div>';
        }

        jsonrpc('/herbario/api/specimens', {
            page: this.currentPage,
            limit: 12,
            filters: this.currentFilters,
        }).then(function (data) {
            if (!self.el) return; // Seguridad: Verificar que el widget sigue vivo al volver del servidor
            self.currentSpecimens = data.specimens; // Guardamos los datos
            self._renderFilters(data.filter_options);
            self._renderCurrentView(); // Renderiza la vista actual (tabla o tarjetas)
            self._renderSwitch(); // Renderiza los botones de cambio de vista
            self._renderPagination(data.total, data.page, data.limit);
        }).catch(function (error) {
            if (!self.el) return;
            console.error("Herbario Snippet: Error al llamar al controlador RPC.", error);
            self.el.querySelector('.herbario_results').innerHTML = `
                <div class="col-12"><div class="alert alert-danger">Error al cargar los datos. Revise la consola del navegador (F12) para más detalles.</div></div>
            `;
        });
    },

    /**
     * Renderiza una vista de ejemplo para el modo de edición del sitio web.
     * @private
     */
    _renderExample: function () {
        const exampleData = [ // Datos de ejemplo actualizados con los nuevos campos
            {id: 0, taxon: 'Rosa rubiginosa', code: 'CHEP-00001', family: 'Rosaceae', province: 'Pichincha', image: '/herbario_espoch/static/description/default_specimen2.jpg', card_number: '123', index: 'R-01', genus: 'Rosa', species: 'rubiginosa'},
            {id: 0, taxon: 'Quercus humboldtii', code: 'CHEP-00002', family: 'Fagaceae', province: 'Chimborazo', image: '/herbario_espoch/static/description/default_specimen2.jpg', card_number: '124', index: 'Q-02', genus: 'Quercus', species: 'humboldtii'},
            {id: 0, taxon: 'Eucalyptus globulus', code: 'CHEP-00003', family: 'Myrtaceae', province: 'Azuay', image: '/herbario_espoch/static/description/default_specimen2.jpg', card_number: '125', index: 'E-03', genus: 'Eucalyptus', species: 'globulus'},
            {id: 0, taxon: 'Solanum tuberosum', code: 'CHEP-00004', family: 'Solanaceae', province: 'Cotopaxi', image: '/herbario_espoch/static/description/default_specimen2.jpg', card_number: '126', index: 'S-04', genus: 'Solanum', species: 'tuberosum'},
        ];
        // CORRECCIÓN: Usar la clave 'filter_options' para los datos de ejemplo, igual que en la llamada RPC.
        // Esto asegura que el modo de edición no falle y sea un reflejo fiel de la vista pública.
        const exampleFilterOptions = {families: ['Rosaceae', 'Fagaceae'], provinces: ['Pichincha', 'Chimborazo'], genera:[], herbaria:[], authors:[], determiners:[], collectors:[], countries:[]};
        this._renderFilters(exampleFilterOptions);
        this._renderCards(exampleData); // Por defecto, mostrar tarjetas en modo edición
        this._renderSwitch();
        this._renderPagination(12, 1, 12);
    },

    /**
     * Renderiza los filtros.
     * @param {Object} filters - Objeto con las listas de filtros.
     * @private
     */
    _renderFilters: function (filterOptions) {
        if (!this.el) return;

        const $sidebarContainer = this.$('.herbario_filters_sidebar');
        let $form = this.$('#herbario-filters-form');

        // Helper para generar opciones HTML
        const getOptionsHtml = (placeholder, options) => {
            let opts = `<option value="">${placeholder}</option>`;
            (options || []).forEach(o => { opts += `<option value="${o}">${o}</option>`; });
            return opts;
        };

        // Si el formulario no existe, lo creamos (primera carga)
        if ($form.length === 0) {
            const $card = $(`
            <div class="card shadow-sm">
                <div class="card-header bg-dark text-white"><i class="fa fa-filter"></i> Filtros de Búsqueda</div>
                <div class="card-body">
                    <form id="herbario-filters-form">
                        <div class="form-group"><label>Taxón</label><input type="text" id="filter_taxon" class="form-control form-control-sm" placeholder="Nombre científico..."></div>
                        <div class="form-group"><label>Familia</label><select id="filter_family" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>Género</label><select id="filter_genus" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>Especie</label><input type="text" id="filter_species" class="form-control form-control-sm" placeholder="Nombre especie..."></div>
                        <div class="form-group"><label>Index</label><input type="text" id="filter_index" class="form-control form-control-sm" placeholder="Código index..."></div>
                        <div class="form-group"><label>Herbario</label><select id="filter_herbarium" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>Autor</label><select id="filter_author" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>Determinador</label><select id="filter_determiner" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>Colector</label><select id="filter_collector" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>País</label><select id="filter_country" class="form-control form-control-sm"></select></div>
                        <div class="form-group"><label>Provincia</label><select id="filter_province" class="form-control form-control-sm"></select></div>
                        <div class="form-group">
                            <label>Elevación (m.s.n.m)</label>
                            <div class="input-group input-group-sm">
                                <div class="input-group-prepend">
                                    <select id="filter_elevation_op" class="form-control form-control-sm">
                                        <option value="=">=</option><option value=">">&gt;</option><option value="<">&lt;</option><option value=">=">&gt;=</option><option value="<=">&lt;=</option>
                                    </select>
                                </div>
                                <input type="number" id="filter_elevation_val" class="form-control" placeholder="Valor...">
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-6 pr-1"><button type="button" id="herbario_clear_filters" class="btn btn-secondary btn-block"><i class="fa fa-eraser"></i> Limpiar</button></div>
                            <div class="col-6 pl-1"><button type="button" id="herbario_apply_filters" class="btn btn-primary btn-block"><i class="fa fa-check"></i> Aplicar</button></div>
                        </div>
                    </form>
                </div>
            </div>`);
            $sidebarContainer.empty().append($card);
        }

        // Función para actualizar un select preservando el valor si es posible
        const updateSelect = (id, key, placeholder, options) => {
            const $el = this.$(`#${id}`);
            // Usamos el valor de currentFilters si existe, sino el valor actual del DOM
            const currentVal = this.currentFilters[key] !== undefined ? this.currentFilters[key] : $el.val();
            
            $el.html(getOptionsHtml(placeholder, options));
            
            if (currentVal) {
                $el.val(currentVal);
            }
        };

        updateSelect('filter_family', 'family', 'Todas', filterOptions.families);
        updateSelect('filter_genus', 'genus', 'Todos', filterOptions.genera);
        updateSelect('filter_herbarium', 'herbarium_id', 'Todos', filterOptions.herbaria);
        updateSelect('filter_author', 'author', 'Todos', filterOptions.authors);
        updateSelect('filter_determiner', 'determiner', 'Todos', filterOptions.determiners);
        updateSelect('filter_collector', 'collector', 'Todos', filterOptions.collectors);
        updateSelect('filter_country', 'country', 'Todos', filterOptions.countries);
        updateSelect('filter_province', 'province', 'Todos', filterOptions.provinces);

        // Restaurar inputs de texto si es necesario
        const restoreInput = (id, key) => {
             const $el = this.$(`#${id}`);
             if (this.currentFilters[key] !== undefined && $el.val() !== this.currentFilters[key]) {
                 $el.val(this.currentFilters[key]);
             }
        };
        
        restoreInput('filter_taxon', 'taxon');
        restoreInput('filter_species', 'species');
        restoreInput('filter_index', 'index');
        restoreInput('filter_elevation_val', 'elevation_val');
        restoreInput('filter_elevation_op', 'elevation_op');
    },

    /**
     * Renderiza los controles de paginación.
     * @private
     */
    _renderPagination: function (total, page, limit) {
        if (!this.el) return;

        const paginationEl = this.el.querySelector('.herbario_pagination');
        if (!paginationEl) return; // Si el contenedor no existe, no hacer nada.

        const totalPages = Math.ceil(total / limit);
        if (totalPages <= 1) {
            paginationEl.innerHTML = '';
            return;
        }
        
        let html = '<ul class="pagination justify-content-center flex-wrap">';

        // Botón "Anterior"
        const prevDisabled = page === 1 ? 'disabled' : '';
        html += `<li class="page-item ${prevDisabled}">
                    <a class="page-link herbario-page-link" href="#" data-page="${page - 1}" aria-label="Anterior">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                 </li>`;

        // Lógica para mostrar rango limitado de páginas con elipsis
        const delta = 2;
        const range = [];
        const rangeWithDots = [];
        let l;

        range.push(1);
        for (let i = page - delta; i <= page + delta; i++) {
            if (i < totalPages && i > 1) {
                range.push(i);
            }
        }
        range.push(totalPages);

        for (let i of range) {
            if (l) {
                if (i - l === 2) {
                    rangeWithDots.push(l + 1);
                } else if (i - l !== 1) {
                    rangeWithDots.push('...');
                }
            }
            rangeWithDots.push(i);
            l = i;
        }

        for (let item of rangeWithDots) {
            if (item === '...') {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            } else {
                const active = item === page ? 'active' : '';
                html += `<li class="page-item ${active}">
                            <a class="page-link herbario-page-link" href="#" data-page="${item}">${item}</a>
                         </li>`;
            }
        }

        // Botón "Siguiente"
        const nextDisabled = page === totalPages ? 'disabled' : '';
        html += `<li class="page-item ${nextDisabled}">
                    <a class="page-link herbario-page-link" href="#" data-page="${page + 1}" aria-label="Siguiente">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                 </li>`;

        html += '</ul>';
        paginationEl.innerHTML = html;
    },

    /**
     * Renderiza la vista correcta (tarjetas o tabla) según el estado actual.
     * @private
     */
    _renderCurrentView: function () {
        if (!this.el) return;
        if (this.currentView === 'table') {
            this._renderTable(this.currentSpecimens);
        } else {
            this._renderCards(this.currentSpecimens);
        }
    },
    /**
     * Renderiza los especímenes en formato de tarjetas.
     * @param {Array} specimens - Array de objetos de especímenes.
     * @private
     */
    _renderCards: function (specimens) {
        if (!this.el) return;
        let html = '';
        specimens.forEach(s => {
            html += `
            <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
                <div class="card h-100 shadow-sm herbario-card">
                    <img src="${s.image || '/herbario_espoch/static/description/default_specimen2.jpg'}" class="card-img-top" style="height: 200px; object-fit: cover;"/>
                    <div class="card-body">
                        <h6 class="card-title font-italic" style="min-height: 40px;">${s.taxon || 'N/A'}</h6>
                        <p class="small text-muted mb-2">
                            <strong># Cartulina:</strong> ${s.card_number || 'N/A'}<br/>
                            <strong>Index:</strong> ${s.index || 'N/A'}<br/>
                            <strong>Familia:</strong> ${s.family || 'N/A'}<br/>
                            <strong>Género:</strong> ${s.genus || 'N/A'}<br/>
                            <strong>Herbario(s):</strong> ${(s.herbaria || []).join(', ') || 'N/A'}<br/>
                            <strong>Provincia:</strong> ${s.province || 'N/A'}
                        </p>
                        <a href="/herbario/specimen/${s.id}" class="btn btn-primary btn-sm stretched-link ${this.editableMode ? 'd-none' : ''}">Ver más</a>
                    </div>
                </div>
            </div>`;
        });
        // CORRECCIÓN: Mostrar un mensaje más visible si no hay resultados.
        const resultsContainer = this.el ? this.el.querySelector('.herbario_results') : null;
        if (html) {
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = '<div class="col-12 text-center"><div class="alert alert-warning" role="alert">No se encontraron especímenes que coincidan con los filtros aplicados.</div></div>';
        }
    },

    /**
     * Renderiza los especímenes en formato de tabla.
     * @param {Array} specimens - Array de objetos de especímenes.
     * @private
     */
    _renderTable: function (specimens) {
        if (!this.el) return;
        let html = `<table class="table table-striped table-hover">
            <thead class="thead-light"><tr>
                <th style="width: 80px;">Imagen</th>
                <th># Cartulina</th>
                <th>Index</th>
                <th>Taxón</th>
                <th>Familia</th>
                <th>Género</th>
                <th>Provincia</th>
                <th class="${this.editableMode ? 'd-none' : ''}"></th>
            </tr></thead>
            <tbody>`;
        specimens.forEach(s => {
            html += `<tr>
                <td class="text-center p-1">
                    <img src="${s.image || '/herbario_espoch/static/description/default_specimen2.jpg'}" style="width: 60px; height: 60px; object-fit: cover;" class="rounded"/>
                </td>
                <td>${s.card_number || ''}</td>
                <td>${s.index || ''}</td>
                <td class="font-italic">${s.taxon || ''}</td>
                <td>${s.family || ''}</td>
                <td>${s.genus || ''}</td>
                <td>${s.province || ''}</td>
                <td class="${this.editableMode ? 'd-none' : ''}"><a href="/herbario/specimen/${s.id}" class="btn btn-primary btn-sm">Ver</a></td>
            </tr>`;
        });
        html += "</tbody></table>";
        this.el.querySelector('.herbario_results').innerHTML = html;
    },

    /**
     * Renderiza los botones para cambiar entre vista de tarjeta y tabla.
     * @private
     */
    _renderSwitch: function () {
        if (!this.el) return;
        const isCards = this.currentView === 'cards';
        const cardsClass = isCards ? 'btn-primary' : 'btn-secondary';
        const tableClass = !isCards ? 'btn-primary' : 'btn-secondary';

        this.el.querySelector('.herbario_view_switch').innerHTML = `
            <div class="btn-group" role="group">
                <button data-view="cards" class="btn_view_cards btn ${cardsClass}"><i class="fa fa-th-large"></i> Tarjetas</button>
                <button data-view="table" class="btn_view_table btn ${tableClass}"><i class="fa fa-bars"></i> Tabla</button>
            </div>
        `;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onApplyFilters: function () {
        this.currentFilters = {
            taxon: this.$('#filter_taxon').val(),
            family: this.$('#filter_family').val(),
            genus: this.$('#filter_genus').val(),
            species: this.$('#filter_species').val(),
            index: this.$('#filter_index').val(),
            herbarium_id: this.$('#filter_herbarium').val(),
            author: this.$('#filter_author').val(),
            determiner: this.$('#filter_determiner').val(),
            collector: this.$('#filter_collector').val(),
            country: this.$('#filter_country').val(),
            province: this.$('#filter_province').val(),
            elevation_op: this.$('#filter_elevation_op').val(),
            elevation_val: this.$('#filter_elevation_val').val(),
        };
        // Limpiar filtros vacíos
        this.currentFilters = Object.fromEntries(Object.entries(this.currentFilters).filter(([_, v]) => v != null && v !== ''));
        this.currentPage = 1; // Resetear a la primera página
        this._fetchData();
    },

    _onPageClick: function (ev) {
        ev.preventDefault();
        this.currentPage = parseInt(ev.currentTarget.dataset.page);
        this._fetchData();
    },

    _onClearFilters: function () {
        this.currentFilters = {};
        const form = this.el.querySelector('#herbario-filters-form');
        if (form) form.reset();
        this.currentPage = 1;
        this._fetchData();
    },

    /**
     * Maneja el cambio de vista entre tarjetas y tabla.
     * @param {Event} ev
     * @private
     */
    _onViewChange: function (ev) {
        this.currentView = ev.currentTarget.dataset.view;
        this._renderCurrentView(); // Vuelve a renderizar con los datos actuales
        this._renderSwitch(); // Actualiza el estado visual de los botones
    },
});

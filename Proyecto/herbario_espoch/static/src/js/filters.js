/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

console.log('🌿 Herbario: Archivo filters.js cargado');

document.addEventListener('DOMContentLoaded', function () {
    console.log('🌿 DOM Ready - Inicializando filtros');

    // Elementos del DOM
    const filterForm = document.getElementById('filterForm');
    const clearBtn = document.getElementById('clearFiltersBtn');
    const applyBtn = document.getElementById('applyFiltersBtn');
    
    const familiaSelect = document.getElementById('familia');
    const generoSelect = document.getElementById('genero');
    const paisSelect = document.getElementById('pais');
    const provinciaSelect = document.getElementById('provincia');
    const cantonSelect = document.getElementById('canton');
    const colectorSelect = document.getElementById('colector');
    
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    if (!filterForm) {
        console.warn('⚠️ No se encontró filterForm');
        return;
    }
    
    console.log('✅ Elementos encontrados');

    // Función para obtener filtros actuales
    function getFilters() {
        return {
            familia: familiaSelect ? familiaSelect.value : '',
            genero: generoSelect ? generoSelect.value : '',
            pais: paisSelect ? paisSelect.value : '',
            provincia: provinciaSelect ? provinciaSelect.value : '',
            canton: cantonSelect ? cantonSelect.value : '',
            colector: colectorSelect ? colectorSelect.value : ''
        };
    }

    // Función para actualizar opciones
    function updateOptions() {
        const filters = getFilters();
        console.log('🔄 Actualizando opciones:', filters);
        
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }

        fetch('/herbario/api/filter-options', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: filters,
                id: Date.now()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            console.log('📦 Respuesta:', data);
            
            if (data.result) {
                updateSelect(familiaSelect, data.result.families || [], 'Todas las familias');
                updateSelect(generoSelect, data.result.genera || [], 'Todos los géneros');
                updateSelect(paisSelect, data.result.countries || [], 'Todos los países');
                updateSelect(provinciaSelect, data.result.provinces || [], 'Todas las provincias');
                updateSelect(cantonSelect, data.result.cantones || [], 'Todos los cantones');
                updateSelect(colectorSelect, data.result.collectors || [], 'Todos los colectores');
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        });
    }

    // Función para actualizar un select
    function updateSelect(select, options, placeholder) {
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = placeholder;
        select.appendChild(defaultOption);
        
        options.forEach(function(opt) {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt;
            if (opt === currentValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        
        console.log(`  ✓ ${select.id}: ${options.length} opciones`);
    }

    // Event listeners para selects
    const allSelects = [familiaSelect, generoSelect, paisSelect, provinciaSelect, cantonSelect, colectorSelect];
    
    allSelects.forEach(function(select) {
        if (select) {
            select.addEventListener('change', function() {
                console.log(`📝 ${this.id} cambió a: ${this.value}`);
                updateOptions();
            });
        }
    });

    // Botón aplicar
    if (applyBtn) {
        applyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('✅ Aplicando filtros');
            filterForm.submit();
        });
    }

    // Botón limpiar
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🧹 Limpiando filtros');
            
            // Limpiar inputs
            const inputs = filterForm.querySelectorAll('input[type="text"], input[type="number"]');
            inputs.forEach(function(input) {
                input.value = '';
            });
            
            // Limpiar selects
            const selects = filterForm.querySelectorAll('select');
            selects.forEach(function(select) {
                select.selectedIndex = 0;
            });
            
            // Actualizar opciones
            setTimeout(function() {
                console.log('🔄 Actualizando opciones...');
                updateOptions();
                
                // Redirigir después de actualizar
                setTimeout(function() {
                    const viewInput = document.querySelector('input[name="view"]');
                    const view = viewInput ? viewInput.value : 'cards';
                    console.log('➡️ Redirigiendo...');
                    window.location.href = '/herbario/repositorio?view=' + view;
                }, 500);
            }, 100);
        });
    }

    // Cargar opciones iniciales
    console.log('🔄 Cargando opciones iniciales...');
    updateOptions();
    
    console.log('✅ Filtros inicializados');
});
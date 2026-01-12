from odoo import http
from odoo.http import request
import json
import base64
import logging

_logger = logging.getLogger(__name__)


class HerbarioController(http.Controller):

    # ==================== API PARA EL SNIPPET DEL WEBSITE ====================

    @http.route('/herbario/api/specimens', type='json', auth='public', methods=['POST'], csrf=False)
    def api_list_specimens(self, page=1, limit=12, filters=None, **kwargs): # El JS envía los params aquí
        """
        Devuelve una lista paginada y filtrada de especímenes para el snippet.
        """
        # CORRECCIÓN: Los parámetros de jsonrpc vienen en el diccionario principal, no en 'params'.
        current_filters = filters or {}
        Specimen = request.env['herbario.specimen'].sudo()
        domain = [('es_publico', '=', True), ('status', '=', 'activo')]

        # Construcción del dominio de búsqueda
        if current_filters.get('taxon'):
            domain.append(('taxon_id.name', 'ilike', current_filters['taxon']))
        if current_filters.get('genus'):
            domain.append(('taxon_id.genero', 'ilike', current_filters['genus']))
        if current_filters.get('family'):
            domain.append(('taxon_id.family_id.name', '=', current_filters['family']))
        if current_filters.get('species'):
            domain.append(('taxon_id.especie', 'ilike', current_filters['species']))
        if current_filters.get('index'):
            domain.append(('index_text', 'ilike', current_filters['index']))
        if current_filters.get('herbarium'):
            domain.append(('herbarium_ids.name', '=', current_filters['herbarium']))
        if current_filters.get('author'):
            domain.append(('author_ids.name', 'ilike', current_filters['author']))
        if current_filters.get('determiner'):
            domain.append(('determiner_ids.name', 'ilike', current_filters['determiner']))
        if current_filters.get('collector'):
            domain.append(('collector_ids.name', 'ilike', current_filters['collector']))

        # Filtros de ubicación (requieren buscar en collection_site_ids)
        site_domain = []
        if current_filters.get('country'):
            site_domain.append(('country_id.name', '=', current_filters['country']))
        if current_filters.get('province'):
            site_domain.append(('province_id.name', '=', current_filters['province']))
        
        if current_filters.get('elevation_val') and current_filters.get('elevation_op'):
            try:
                val = float(current_filters['elevation_val'])
                op = current_filters['elevation_op']
                if op in ['=', '<', '>', '<=', '>=']:
                    site_domain.append(('elevation', op, val))
            except (ValueError, TypeError):
                pass # Ignorar si el valor de elevación no es un número

        if site_domain:
            sites = request.env['herbario.collection.site'].sudo().search(site_domain)
            specimen_ids_from_sites = sites.mapped('specimen_id').ids
            domain.append(('id', 'in', specimen_ids_from_sites))

        # Paginación
        total_specimens = Specimen.search_count(domain)
        print("🚨 TOTAL REGISTROS BACKEND:", total_specimens)
        offset = (page - 1) * limit
        specimens = Specimen.search(domain, limit=limit, offset=offset, order='create_date desc')

        data = []
        for spec in specimens:
            primary_image = spec.image_ids.filtered(lambda i: i.is_primary)
            if not primary_image:
                primary_image = spec.image_ids[:1]
            image_url = f'/web/image/herbario.image/{primary_image.id}/image_data' if primary_image else False

            data.append({
                'id': spec.id,
                'url_hash': spec.url_hash,
                'taxon': spec.taxon_id.name if spec.taxon_id else '',
                'family': spec.taxon_id.family_id.name if spec.taxon_id and spec.taxon_id.family_id else '',
                'genus': spec.taxon_id.genero if spec.taxon_id else '',
                'species': spec.taxon_id.especie if spec.taxon_id else '',
                'code': spec.codigo_herbario or '',
                'card_number': spec.numero_cartulina or '',
                'index': spec.index_text or '',
                'province': spec.collection_site_ids[:1].province_id.name if spec.collection_site_ids and spec.collection_site_ids[:1].province_id else '',
                'image': image_url,
            })
        
        # CORRECCIÓN: Devolver siempre las opciones de filtro para mantener la consistencia del frontend.
        # Odoo es eficiente cacheando estas búsquedas, por lo que el impacto en el rendimiento es mínimo.
        all_specimens_for_filters = Specimen.search([('es_publico', '=', True), ('status', '=', 'activo')])
        all_sites_for_filters = request.env['herbario.collection.site'].sudo().search([('specimen_id', 'in', all_specimens_for_filters.ids)])

        filter_options = {
            'families': sorted(list(set(all_specimens_for_filters.mapped('taxon_id.family_id.name')) - {False})),
            'genera': sorted(list(set(all_specimens_for_filters.mapped('taxon_id.genero')) - {False})),
            'herbaria': sorted(list(set(all_specimens_for_filters.mapped('herbarium_ids.name')) - {False})),
            'authors': sorted(list(set(all_specimens_for_filters.mapped('author_ids.name')) - {False})),
            'determiners': sorted(list(set(all_specimens_for_filters.mapped('determiner_ids.name')) - {False})),
            'collectors': sorted(list(set(all_specimens_for_filters.mapped('collector_ids.name')) - {False})),
            'countries': sorted(list(set(all_sites_for_filters.mapped('country_id.name')) - {False})),
            'provinces': sorted(list(set(all_sites_for_filters.mapped('province_id.name')) - {False})),
        }

        return {
            'specimens': data,
            'filter_options': filter_options,
            'total': total_specimens,
            'page': page,
            'limit': limit,
        }

    # ==================== PÁGINA DE DETALLE DE ESPÉCIMEN ====================

    @http.route(['/herbario/specimen/<string:specimen_hash>'], type='http', auth="public", website=True)
    def specimen_detail(self, specimen_hash, **kwargs):
        """
        Muestra la página de detalle para un espécimen específico.
        """
        # LIMPIEZA: Eliminar espacios en blanco que pueden causar que la búsqueda falle
        specimen_hash = str(specimen_hash).strip()
        Specimen = request.env['herbario.specimen'].sudo()
        specimen = False

        # 1. Prioridad ID: Si es un número, buscamos directamente por ID (Modo "Normal")
        if specimen_hash.isdigit():
            found = Specimen.browse(int(specimen_hash))
            if found.exists():
                specimen = found

        # 2. Compatibilidad: Si no se encontró por ID, buscamos por UUID (para QRs antiguos)
        if not specimen:
            specimen = Specimen.search([('url_hash', '=', specimen_hash)], limit=1)

        # DEBUG: Imprimir en el log para verificar por qué falla (Revisar consola de Odoo)
        if not specimen:
            _logger.info(f"HERBARIO DEBUG: No se encontró espécimen con hash '{specimen_hash}'")
        else:
            _logger.info(f"HERBARIO DEBUG: Encontrado ID {specimen.id}. Público: {specimen.es_publico}, Estado: {specimen.status}")

        # Verificación de seguridad
        if not specimen or not specimen.es_publico or specimen.status != 'activo':
            return request.render('herbario_espoch.herbario_specimen_not_found')

        # =======================
        # OBTENER IMAGEN PRINCIPAL
        # =======================
        image_url = False

        main_image = specimen.image_ids.filtered(lambda i: i.is_primary)[:1]
        if not main_image and specimen.image_ids:
            main_image = specimen.image_ids[:1]

        if main_image:
            image_url = f"/web/image/herbario.image/{main_image.id}/image_data"

        # =======================
        # RENDER A LA VISTA
        # =======================
        return request.render('herbario_espoch.herbario_specimen_detail', {
            'specimen': specimen,
            'image_url': image_url,
        })

    # ==================== PÁGINA DE ESTADÍSTICAS Y MAPA ====================

    @http.route('/herbario/statistics', type='http', auth='public', website=True, csrf=False)
    def herbario_statistics(self, **kwargs):
        """
        Renderiza la página principal de estadísticas. 
        Los datos se cargarán dinámicamente vía JavaScript.
        """
        return request.render('herbario_espoch.herbario_statistics_page', {})

    @http.route('/herbario/api/statistics_data', type='json', auth='public', website=True, methods=['POST'])
    def get_statistics_data(self, filters=None, **kwargs):
        """
        API que devuelve datos filtrados para los gráficos y el mapa.
        """
        filters = filters or {}
        domain = [('es_publico', '=', True), ('status', '=', 'activo')]

        # Aplicar filtros recibidos desde el frontend
        # CORRECCIÓN: Añadir todos los filtros que faltaban
        if filters.get('family'):
            domain.append(('taxon_id.family_id.name', '=', filters['family']))
        if filters.get('genus'):
            domain.append(('taxon_id.genero', '=', filters['genus']))
        if filters.get('species'):
            domain.append(('taxon_id.especie', 'ilike', filters['species']))
        if filters.get('author'):
            domain.append(('author_ids.name', '=', filters['author']))
        if filters.get('determiner'):
            domain.append(('determiner_ids.name', '=', filters['determiner']))
        if filters.get('collector'):
            domain.append(('collector_ids.name', '=', filters['collector']))
        if filters.get('herbarium'):
            domain.append(('herbarium_ids.name', '=', filters['herbarium']))
        if filters.get('index'):
            domain.append(('index_text', 'ilike', filters['index']))

        # Filtros de ubicación
        site_domain = []
        if filters.get('country'):
            site_domain.append(('country_id.name', '=', filters['country']))
        if filters.get('province'):
            site_domain.append(('province_id.name', '=', filters['province']))

        if site_domain:
            sites = request.env['herbario.collection.site'].sudo().search(site_domain)
            domain.append(('id', 'in', sites.mapped('specimen_id').ids))

        specimens = request.env['herbario.specimen'].sudo().search(domain)

        # 1. Preparar datos para los gráficos
        family_counts = {}
        for spec in specimens:
            fam_name = spec.taxon_id.family_id.name if spec.taxon_id and spec.taxon_id.family_id else 'Indeterminada'
            family_counts[fam_name] = family_counts.get(fam_name, 0) + 1
        
        # MEJORA: Devolver todas las familias, no solo el top 10.
        top_families = sorted(family_counts.items(), key=lambda x: x[1], reverse=True)
        chart_data = {
            'labels': [item[0] for item in top_families],
            'values': [item[1] for item in top_families],
        }

        # 2. Preparar datos para el mapa (puntos de geolocalización)
        map_points = []
        # Buscamos solo especímenes que tengan al menos una ubicación con coordenadas
        specimens_with_location = specimens.filtered(lambda s: s.collection_site_ids.filtered(lambda l: l.latitude and l.longitude))
        for spec in specimens_with_location:
            # Tomamos la primera ubicación con coordenadas que encontremos
            loc = spec.collection_site_ids.filtered(lambda l: l.latitude and l.longitude)[:1]
            if loc:
                map_points.append({
                    'lat': loc.latitude,
                    'lng': loc.longitude,
                    # MEJORA: El popup ahora contiene un botón con el ID del espécimen para el panel lateral
                    'popup': f"<strong>{spec.taxon_id.name or 'N/A'}</strong><br/>Familia: {spec.taxon_id.family_id.name or 'N/A'}<br/><button class='btn btn-link btn-sm p-0 map-detail-link' data-specimen-id='{spec.id}'>Ver detalle</button>"
                })

        return {
            'chart_data': chart_data,
            'map_points': map_points,
        }

    @http.route('/herbario/api/filter_options', type='json', auth='public', website=True)
    def get_filter_options(self, **kwargs):
        """
        API que devuelve todas las opciones posibles para los filtros desplegables.
        """
        Specimen = request.env['herbario.specimen'].sudo()
        all_specimens = Specimen.search([('es_publico', '=', True), ('status', '=', 'activo')])
        all_sites = request.env['herbario.collection.site'].sudo().search([('specimen_id', 'in', all_specimens.ids)])

        return {
            'families': sorted(list(set(all_specimens.mapped('taxon_id.family_id.name')) - {False})),
            'genera': sorted(list(set(all_specimens.mapped('taxon_id.genero')) - {False})),
            'authors': sorted(list(set(all_specimens.mapped('author_ids.name')) - {False})),
            'determiners': sorted(list(set(all_specimens.mapped('determiner_ids.name')) - {False})),
            'collectors': sorted(list(set(all_specimens.mapped('collector_ids.name')) - {False})),
            'countries': sorted(list(set(all_sites.mapped('country_id.name')) - {False})),
            'provinces': sorted(list(set(all_sites.mapped('province_id.name')) - {False})),
            'herbaria': sorted(list(set(all_specimens.mapped('herbarium_ids.name')) - {False})),
        }

    @http.route('/herbario/api/specimen_details_html/<int:specimen_id>', type='http', auth='public', website=True)
    def get_specimen_details_html(self, specimen_id, **kwargs):
        """
        Renderiza y devuelve el HTML del panel de detalles para un espécimen.
        """
        specimen = request.env['herbario.specimen'].sudo().browse(specimen_id)
        if not specimen.exists() or not specimen.es_publico or specimen.status != 'activo':
            return request.make_response("Espécimen no encontrado.", status=404)

        image_url = False
        if specimen.image_ids:
            image_url = f"/web/image/herbario.image/{specimen.image_ids[0].id}/image_data"

        return request.render('herbario_espoch.specimen_detail_panel', {
            'spec': specimen,
            'image_url': image_url,
        }, mimetype='text/html')

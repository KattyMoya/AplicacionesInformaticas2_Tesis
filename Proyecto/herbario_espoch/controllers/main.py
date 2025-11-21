from odoo import http
from odoo.http import request
import json
import base64


class HerbarioController(http.Controller):

    # ==================== PÁGINA PRINCIPAL ====================
    
    @http.route(['/herbario', '/herbario/'], type='http', auth='public', website=True)
    def herbario_home(self, **kw):
        """Página principal del herbario"""
        Specimen = request.env['herbario.specimen'].sudo()
        
        # Estadísticas generales
        total_specimens = Specimen.search_count([('es_publico', '=', True), ('status', '=', 'activo')])
        total_families = len(Specimen.search([('es_publico', '=', True), ('status', '=', 'activo')]).mapped('taxon_id.family_id'))
        total_images = request.env['herbario.image'].sudo().search_count([
            ('specimen_id.es_publico', '=', True),
            ('deleted_at', '=', False)
        ])
        
        # Últimos especímenes agregados
        recent_specimens = Specimen.search([
            ('es_publico', '=', True),
            ('status', '=', 'activo')
        ], limit=6, order='created_at desc')
        
        return request.render('herbario_espoch.herbario_home', {
            'total_specimens': total_specimens,
            'total_families': total_families,
            'total_images': total_images,
            'recent_specimens': recent_specimens,
        })

    # ==================== ESTADÍSTICAS ====================
    
    @http.route(['/herbario/estadisticas'], type='http', auth='public', website=True)
    def herbario_stats(self, **kw):
        """Página de estadísticas con gráficos"""
        Specimen = request.env['herbario.specimen'].sudo()
        CollectionSite = request.env['herbario.collection.site'].sudo()
        
        specimens = Specimen.search([('es_publico', '=', True), ('status', '=', 'activo')])
        
        # Estadísticas generales
        stats = {
            'total_specimens': len(specimens),
            'total_families': len(specimens.mapped('taxon_id.family_id.name')),
            'total_genera': len(specimens.mapped('taxon_id.genero')),
            'total_species': len(specimens.mapped('taxon_id.especie')),
            'total_locations': CollectionSite.search_count([('specimen_id.es_publico', '=', True)]),
            'total_images': request.env['herbario.image'].sudo().search_count([
                ('specimen_id.es_publico', '=', True),
                ('deleted_at', '=', False)
            ]),
        }
        
        # Top 10 familias más representadas
        families_data = {}
        for spec in specimens:
            families_data[spec.taxon_id.family_id.name] = families_data.get(spec.taxon_id.family_id.name, 0) + 1
        top_families = sorted(families_data.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Especímenes por provincia
        locations = CollectionSite.search([('specimen_id.es_publico', '=', True)])
        provinces_data = {}
        for loc in locations:
            provinces_data[loc.province_id.name] = provinces_data.get(loc.province_id.name, 0) + 1
        top_provinces = sorted(provinces_data.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Especímenes por año de recolección
        years_data = {}
        for loc in locations:
            if loc.fecha_recoleccion:
                year = loc.fecha_recoleccion.year
                years_data[year] = years_data.get(year, 0) + 1
        years_sorted = sorted(years_data.items())
        
        # Coordenadas para el mapa
        map_locations = []
        for loc in locations:
            if loc.latitude and loc.longitude:
                map_locations.append({
                    'lat': loc.latitude,
                    'lng': loc.longitude,
                    'name': loc.specimen_id.taxon_id.name,
                    'locality': loc.locality_id.name,
                    'provincia': loc.province_id.name,
                })
        
        return request.render('herbario_espoch.herbario_statistics', {
            'stats': stats,
            'top_families': top_families,
            'top_provinces': top_provinces,
            'years_data': years_sorted,
            'map_locations': json.dumps(map_locations),
        })

    # ==================== MÉTODO AUXILIAR PARA LIMPIAR PARÁMETROS ====================
    def _clean_params(self, **kwargs):
        """Limpia parámetros vacíos o None"""
        cleaned = {}
        for key, value in kwargs.items():
            if value and str(value).strip() and str(value).lower() != 'none':
                cleaned[key] = str(value).strip()
            else:
                cleaned[key] = ''
        return cleaned

    # ==================== MÉTODOS AUXILIARES ====================  
    def _check_edit_permission(self):
        """Verifica si el usuario tiene permisos de edición"""
        try:
            if request.env.user:
                public_user = request.env.ref('base.public_user', raise_if_not_found=False)
                if public_user and request.env.user.id != public_user.id:
                    return (
                        request.env.user.has_group('herbario_espoch.group_herbario_encargado') or
                        request.env.user.has_group('herbario_espoch.group_herbario_admin_ti') or
                        request.env.user.has_group('base.group_system')
                    )
        except Exception:
            pass
        return False

    def _build_filter_domain(self, domain, site_domain, search, familia, genero, 
                           pais, provincia, canton, localidad, colector, autor, 
                           index, taxon, altitud_operador, altitud_valor, 
                           altitud_min, altitud_max):
        """Construye el dominio de búsqueda basado en filtros"""
        
        CollectionSite = request.env['herbario.collection.site'].sudo()
        
        # Filtros de espécimen
        if search:
            domain += ['|', '|',
                    ('taxon_id.name', 'ilike', search),
                    ('taxon_id.family_id.name', 'ilike', search), # Correcto
                    ('taxon_id.genero', 'ilike', search)]
        
        if taxon:
            domain += [('taxon_id.name', 'ilike', taxon)]
        
        if familia:
            domain += [('taxon_id.family_id.name', '=', familia)]
        
        if genero:
            domain += [('taxon_id.genero', '=', genero)]
        
        if autor:
            domain += [('author_ids.name', 'ilike', autor)] # Correcto
        
        if index:
            domain += [('index_text', 'ilike', index)] # CORREGIDO: El campo se llama index_text
        
        # Filtros de ubicación
        if pais:
            site_domain.append(('country_id.name', '=', pais))

        if provincia:
            site_domain.append(('province_id.name', '=', provincia))

        if canton:
            site_domain.append(('lower_id.name', '=', canton))

        if localidad:
            site_domain.append(('locality_id.name', 'ilike', localidad))
        
        if colector:
            domain += [('collector_ids.name', 'ilike', colector)] # CORREGIDO: El colector está en el espécimen, no en el sitio.
        
        # Filtro por Altitud
        if altitud_operador == 'range':
            if altitud_min:
                try:
                    site_domain.append(('elevation', '>=', float(altitud_min)))
                except ValueError:
                    pass
            if altitud_max:
                try:
                    site_domain.append(('elevation', '<=', float(altitud_max)))
                except ValueError:
                    pass
        elif altitud_valor:
            try:
                valor_float = float(altitud_valor)
                site_domain.append(('elevation', altitud_operador, valor_float))
            except ValueError:
                pass
        
        # Aplicar filtros de ubicación
        if site_domain:
            sites = CollectionSite.search(site_domain)
            specimen_ids_from_sites = sites.mapped('specimen_id').ids
            if specimen_ids_from_sites:
                domain += [('id', 'in', specimen_ids_from_sites)]
            else:
                domain += [('id', '=', False)]
        
        return domain, site_domain

    def _get_intelligent_filter_options(self, familia='', genero='', pais='', 
                                   provincia='', canton='', colector=''):
        """
        Obtiene opciones de filtro INTELIGENTES basadas en la selección actual.
        Solo muestra opciones que tengan especímenes disponibles.
        """
        
        Specimen = request.env['herbario.specimen'].sudo()
        CollectionSite = request.env['herbario.collection.site'].sudo()
        
        print(f"\n=== FILTROS RECIBIDOS ===")
        print(f"Familia: '{familia}', Género: '{genero}', País: '{pais}'")
        print(f"Provincia: '{provincia}', Cantón: '{canton}', Colector: '{colector}'")
        
        # Verificar si hay algún filtro aplicado
        has_filters = any([familia, genero, pais, provincia, canton, colector])
        
        # Si NO hay filtros, devolver TODAS las opciones
        if not has_filters:
            print("DEBUG: Sin filtros - devolviendo TODAS las opciones")
            all_specimens = Specimen.search([('es_publico', '=', True), ('status', '=', 'activo')])
            all_sites = CollectionSite.search([('specimen_id.es_publico', '=', True)])
            
            result = {
                'families': sorted(set(all_specimens.mapped('taxon_id.family_id.name'))), # Correcto
                'genera': sorted(set(all_specimens.mapped('taxon_id.genero'))),
                'countries': sorted(set(all_sites.mapped('country_id.name'))),
                'provinces': sorted(set(all_sites.mapped('province_id.name'))),
                'cantones': sorted(set(all_sites.mapped('lower_id.name'))),
                'collectors': sorted(set(all_specimens.mapped('collector_ids.name'))), # CORREGIDO
                'count': len(all_specimens),
            }
            print(f"Total opciones: {len(result['families'])} familias, {len(result['genera'])} géneros")
            return result
        
        # HAY FILTROS - Aplicar filtrado inteligente
        base_domain = [('es_publico', '=', True), ('status', '=', 'activo')]
        base_site_domain = []
        
        # Aplicar filtros taxonómicos
        if familia:
            base_domain.append(('taxon_id.family_id.name', '=', familia))
        if genero:
            base_domain.append(('taxon_id.genero', '=', genero))
        
        # Aplicar filtros geográficos
        if pais:
            base_site_domain.append(('country_id.name', '=', pais))
        if provincia:
            base_site_domain.append(('province_id.name', '=', provincia))
        if canton:
            base_site_domain.append(('lower_id.name', '=', canton))
        if colector:
            base_domain.append(('collector_ids.name', 'ilike', colector)) # CORREGIDO
        
        # Obtener especímenes filtrados
        if base_site_domain:
            filtered_sites = CollectionSite.search(base_site_domain)
            specimen_ids = filtered_sites.mapped('specimen_id').ids
            if specimen_ids:
                base_domain.append(('id', 'in', specimen_ids))
            else:
                base_domain.append(('id', '=', False))
        
        filtered_specimens = Specimen.search(base_domain)
        print(f"Especímenes filtrados: {len(filtered_specimens)}")
        
        # Si no hay especímenes con estos filtros, devolver opciones vacías
        if not filtered_specimens:
            print("⚠️ No hay especímenes con estos filtros")
            return {
                'families': [],
                'genera': [],
                'countries': [],
                'provinces': [],
                'cantones': [],
                'collectors': [],
                'count': 0,
            }
        
        # Obtener ubicaciones relacionadas con especímenes filtrados
        filtered_sites = CollectionSite.search([
            ('specimen_id', 'in', filtered_specimens.ids)
        ])
        
        # Extraer opciones únicas disponibles
        result = {
            'families': sorted(set(filtered_specimens.mapped('taxon_id.family_id.name'))), # Correcto
            'genera': sorted(set(filtered_specimens.mapped('taxon_id.genero'))),
            'countries': sorted(set(filtered_sites.mapped('country_id.name'))),
            'provinces': sorted(set(filtered_sites.mapped('province_id.name'))),
            'cantones': sorted(set(filtered_sites.mapped('lower_id.name'))),
            'collectors': sorted(set(filtered_specimens.mapped('collector_ids.name'))), # CORREGIDO
            'count': len(filtered_specimens),
        }
        
        print(f"Opciones disponibles: {len(result['families'])} familias, {len(result['genera'])} géneros")
        return result

    def _get_sort_order(self, sort):
        """Determina el orden de clasificación"""
        order = 'write_date desc, id desc'
        if sort == 'date_asc':
            order = 'id asc'
        elif sort == 'name_asc':
            order = 'taxon_id asc'
        elif sort == 'name_desc':
            order = 'taxon_id desc'
        elif sort == 'code_asc':
            order = 'codigo_herbario asc'
        return order
    
    # ==================== REPOSITORIO CON FILTROS ====================
    @http.route([
        '/herbario/repositorio',
        '/herbario/repositorio/page/<int:page>'
    ], type='http', auth='public', website=True)
    def herbario_repository(self, page=1, search='', familia='', genero='', 
                        pais='', provincia='', canton='', localidad='', colector='', 
                        autor='', index='', taxon='', sort='', view='cards',
                        altitud_operador='=', altitud_valor='', 
                        altitud_min='', altitud_max='', **kwargs):
        """Repositorio con filtros avanzados"""
        
        Specimen = request.env['herbario.specimen'].sudo()
        CollectionSite = request.env['herbario.collection.site'].sudo()
        
        # Verificar permisos de edición
        user_can_edit = self._check_edit_permission()
        
        # Logs para depurar (remover después)
        print(f"DEBUG: Parámetros recibidos - familia: '{familia}', genero: '{genero}', pais: '{pais}', view: '{view}'")
        
        # Construir dominio base
        domain = [('es_publico', '=', True), ('status', '=', 'activo')]
        site_domain = []
        
        # Usar el método auxiliar para construir dominio (elimina duplicación)
        domain, site_domain = self._build_filter_domain(
            domain, site_domain, search, familia, genero, pais, provincia, 
            canton, localidad, colector, autor, index, taxon,
            altitud_operador, altitud_valor, altitud_min, altitud_max
        )
        
        # Logs para depurar dominio
        print(f"DEBUG: Dominio construido: {domain}")
        
        # Ordenamiento
        order = self._get_sort_order(sort)
        
        # Obtener especímenes
        specimens_count = Specimen.search_count(domain)
        print(f"DEBUG: Especímenes encontrados: {specimens_count}")
        
        # Paginación
        per_page = 24
        pager = request.website.pager(
            url='/herbario/repositorio',
            total=specimens_count,
            page=page,
            step=per_page,
            url_args={
                'search': search, 'familia': familia, 'genero': genero,
                'pais': pais, 'provincia': provincia, 'canton': canton,
                'localidad': localidad, 'colector': colector, 'autor': autor, 
                'index': index, 'taxon': taxon,
                'altitud_operador': altitud_operador, 
                'altitud_valor': altitud_valor, 'altitud_min': altitud_min, 
                'altitud_max': altitud_max, 'sort': sort, 'view': view
            }
        )
        
        specimens = Specimen.search(domain, limit=per_page, offset=pager['offset'], order=order)
        
        # Filtros inteligentes
        filter_options = self._get_intelligent_filter_options(
            familia, genero, pais, provincia, canton, colector
        )
        
        # Vista
        view_mode = view if view in ['cards', 'table'] else 'cards'
        
        return request.render('herbario_espoch.herbario_repository', {
            'specimens': specimens,
            'total_results': specimens_count,
            'pager': pager,
            'search': search,
            'familia': familia,
            'genero': genero,
            'pais': pais,
            'provincia': provincia,
            'canton': canton,
            'localidad': localidad,
            'colector': colector,
            'autor': autor,
            'index': index,
            'taxon': taxon,
            'altitud_operador': altitud_operador,
            'altitud_valor': altitud_valor,
            'altitud_min': altitud_min,
            'altitud_max': altitud_max,
            'sort': sort,
            'view_mode': view_mode,
            'families': filter_options['families'],
            'genera': filter_options['genera'],
            'countries': filter_options['countries'],
            'provinces': filter_options['provinces'],
            'cantones': filter_options['cantones'],
            'collectors': filter_options['collectors'],
            'user_can_edit': user_can_edit,
        })

    # ==================== API PARA FILTROS DINÁMICOS (AJAX) ====================
    @http.route('/herbario/api/filter-options', type='json', auth='public', methods=['POST'])
    def api_filter_options(self, **kwargs):
        """API para obtener opciones de filtros dinámicamente via AJAX"""
        
        print("\n========== API FILTER OPTIONS ==========")
        print(f"kwargs recibidos: {kwargs}")
        
        # Los parámetros vienen dentro de 'params' cuando es JSON-RPC
        params = kwargs if isinstance(kwargs, dict) else {}
        
        familia = params.get('familia', '') or ''
        genero = params.get('genero', '') or ''
        pais = params.get('pais', '') or ''
        provincia = params.get('provincia', '') or ''
        canton = params.get('canton', '') or ''
        colector = params.get('colector', '') or ''
        
        # Limpiar valores
        familia = str(familia).strip() if familia else ''
        genero = str(genero).strip() if genero else ''
        pais = str(pais).strip() if pais else ''
        provincia = str(provincia).strip() if provincia else ''
        canton = str(canton).strip() if canton else ''
        colector = str(colector).strip() if colector else ''
        
        print(f"Parámetros limpiados:")
        print(f"  familia: '{familia}'")
        print(f"  genero: '{genero}'")
        print(f"  pais: '{pais}'")
        print(f"  provincia: '{provincia}'")
        print(f"  canton: '{canton}'")
        print(f"  colector: '{colector}'")
        
        result = self._get_intelligent_filter_options(
            familia, genero, pais, provincia, canton, colector
        )
        
        print(f"Resultado API: {len(result.get('families', []))} familias")
        print("==========================================\n")
        
        return result
    
    # ==================== GALERÍA ====================
    @http.route([
        '/herbario/galeria',
        '/herbario/galeria/page/<int:page>'
    ], type='http', auth='public', website=True)
    def herbario_gallery(self, page=1, search='', familia='', tipo_imagen='', **kwargs):
        """Galería de imágenes con filtros"""
        
        Image = request.env['herbario.image'].sudo()
        
        # Construir dominio
        domain = [('specimen_id.es_publico', '=', True), ('specimen_id.status', '=', 'activo')]
        
        if search:
            domain += [('specimen_id.taxon_id.name', 'ilike', search)]
        
        if familia:
            domain += [('specimen_id.taxon_id.family_id.name', '=', familia)]
        
        if tipo_imagen:
            domain += [('image_type', '=', tipo_imagen)]
        
        # Contar imágenes
        images_count = Image.search_count(domain)
        
        # Paginación
        per_page = 20
        pager = request.website.pager(
            url='/herbario/galeria',
            total=images_count,
            page=page,
            step=per_page,
            url_args={'search': search, 'familia': familia, 'tipo_imagen': tipo_imagen}
        )
        
        images = Image.search(domain, limit=per_page, offset=pager['offset'], order='id desc')
        
        # Datos para filtros
        all_specimens = request.env['herbario.specimen'].sudo().search([
            ('es_publico', '=', True), ('status', '=', 'activo')
        ])
        families = sorted(set(all_specimens.mapped('taxon_id.family_id.name')))
        
        return request.render('herbario_espoch.herbario_gallery', {
            'images': images,
            'pager': pager,
            'search': search,
            'familia': familia,
            'tipo_imagen': tipo_imagen,
            'families': families,
        })

    # ==================== DETALLE DE ESPÉCIMEN ====================
    @http.route(['/herbario/specimen/<int:specimen_id>'], type='http', auth='public', website=True)
    def herbario_specimen_detail(self, specimen_id, **kw):
        """Página de detalle de un espécimen"""
        Specimen = request.env['herbario.specimen'].sudo()
        specimen = Specimen.browse(specimen_id)
        
        # Verificar que sea público
        if not specimen.exists() or not specimen.es_publico or specimen.status != 'activo':
            return request.redirect('/herbario/repositorio')
        
        # Verificar si el usuario puede editar
        user_can_edit = False
        try:
            if request.env.user:
                public_user = request.env.ref('base.public_user', raise_if_not_found=False)
                if public_user and request.env.user.id != public_user.id:
                    # Verificar si tiene permisos de escritura (encargado o admin)
                    user_can_edit = (
                        request.env.user.has_group('herbario_espoch.group_herbario_encargado') or
                        request.env.user.has_group('herbario_espoch.group_herbario_admin_ti') or
                        request.env.user.has_group('base.group_system')
                    )
        except Exception as e:
            user_can_edit = False
        
        # Registrar escaneo del QR si viene de QR
        if kw.get('from_qr'):
            qr_code = specimen.qr_code_id.filtered(lambda qr: not qr.obsolete)
            if qr_code:
                qr_code.register_scan()
        
        # Especímenes relacionados (misma familia)
        related_specimens = Specimen.search([
            ('taxon_id.family_id', '=', specimen.taxon_id.family_id.id),
            ('id', '!=', specimen.id),
            ('es_publico', '=', True),
            ('status', '=', 'activo')
        ], limit=4)
        
        return request.render('herbario_espoch.herbario_specimen_detail', {
            'specimen': specimen,
            'related_specimens': related_specimens,
            'user_can_edit': user_can_edit,
        })

    # ==================== BÚSQUEDA AJAX ====================
    
    @http.route(['/herbario/api/search'], type='json', auth='public', methods=['POST'])
    def herbario_api_search(self, query, limit=10):
        """API de búsqueda para autocompletado"""
        Specimen = request.env['herbario.specimen'].sudo()
        
        domain = [
            ('es_publico', '=', True),
            ('status', '=', 'activo'),
            '|', '|', '|',
            ('taxon_id.name', 'ilike', query),
            ('taxon_id.family_id.name', 'ilike', query),
            ('taxon_id.genero', 'ilike', query),
            ('taxon_id.especie', 'ilike', query)
        ]
        
        specimens = Specimen.search(domain, limit=limit)
        
        results = []
        for spec in specimens:
            results.append({
                'id': spec.id,
                'nombre_cientifico': spec.taxon_id.name,
                'familia': spec.taxon_id.family_id.name,
                'codigo': spec.codigo_herbario,
                'url': f'/herbario/specimen/{spec.id}'
            })
        
        return results

    # ==================== ABOUT ====================
    
    @http.route(['/herbario/about'], type='http', auth='public', website=True)
    def herbario_about(self, **kw):
        """Página Acerca de"""
        return request.render('herbario_espoch.herbario_about', {})

    # ==================== EXPORTAR DATOS ====================
    
    @http.route(['/herbario/api/export/<string:format>'], type='http', auth='user', methods=['GET'])
    def herbario_export_data(self, format='csv', familia=None, **kw):
        """Exporta datos del herbario (requiere login)"""
        Specimen = request.env['herbario.specimen'].sudo()
        
        domain = [('es_publico', '=', True), ('status', '=', 'activo')]
        if familia:
            domain.append(('taxon_id.family_id.name', '=', familia))
        
        specimens = Specimen.search(domain, order='codigo_herbario asc')
        
        if format == 'csv':
            return self._export_csv(specimens)
        elif format == 'json':
            return self._export_json(specimens)
        else:
            return request.redirect('/herbario/repositorio')

    def _export_csv(self, specimens):
        """Exporta a CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        headers = ['Código', 'Nombre Científico', 'Familia', 'Género', 'Especie', 
                  'Autor', 'Determinado Por', 'Descripción']
        writer.writerow(headers)
        
        # Datos
        for spec in specimens:
            writer.writerow([
                spec.codigo_herbario,
                spec.taxon_id.name,
                spec.taxon_id.family_id.name,
                spec.taxon_id.genero,
                spec.taxon_id.especie,
                ", ".join(spec.author_ids.mapped('name')) or '',
                ", ".join(spec.determiner_ids.mapped('name')) or '',
                spec.descripcion_especie or ''
            ])
        
        content = output.getvalue()
        output.close()
        
        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename=herbario_espoch.csv')
            ]
        )

    def _export_json(self, specimens):
        """Exporta a JSON"""
        data = []
        for spec in specimens:
            data.append({
                'codigo_herbario': spec.codigo_herbario,
                'nombre_cientifico': spec.taxon_id.name,
                'familia': spec.taxon_id.family_id.name,
                'genero': spec.taxon_id.genero,
                'especie': spec.taxon_id.especie,
                'autor_cientifico': ", ".join(spec.author_ids.mapped('name')) or '',
                'determinado_por': ", ".join(spec.determiner_ids.mapped('name')) or '',
                'descripcion_especie': spec.descripcion_especie,
                'ubicaciones': [{
                    'localidad': loc.locality_id.name,
                    'provincia': loc.province_id.name,
                    'pais': loc.country_id.name,
                    'latitud': loc.latitude,      # CORREGIDO
                    'longitud': loc.longitude,    # CORREGIDO
                    'colector': loc.colector,
                    'fecha_recoleccion': str(loc.fecha_recoleccion) if loc.fecha_recoleccion else None
                } for loc in spec.collection_site_ids]
            })
        
        return request.make_response(
            json.dumps(data, indent=2),
            headers=[
                ('Content-Type', 'application/json'),
                ('Content-Disposition', 'attachment; filename=herbario_espoch.json')
            ]
        )

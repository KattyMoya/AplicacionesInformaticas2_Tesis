from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class HerbarioHerbarium(models.Model):
    _name = 'herbario.herbarium'
    _description = 'Herbarios'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del Herbario',
        required=True,
        index=True,
        tracking=True
    )

    specimen_ids = fields.One2many(
        'herbario.specimen',
        'herbarium_id',
        string='Especímenes'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'El nombre del herbario debe ser único!')
    ]

    def name_get(self):
        return [(record.id, record.name) for record in self]

class Country(models.Model):
    _name = 'herbario.country'
    _description = 'País'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del País', required=True, tracking=True)
    code = fields.Char(string='Código de País', size=2, tracking=True)
    province_ids = fields.One2many('herbario.province', 'country_id', string='Provincias')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El nombre del país debe ser único!')
    ]

    def name_get(self):
        return [(record.id, f"{record.name} ({record.code})" if record.code else record.name) 
                for record in self]

class Province(models.Model):
    _name = 'herbario.province'
    _description = 'Provincia'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre de la Provincia', required=True, tracking=True)
    country_id = fields.Many2one('herbario.country', string='País', 
                                required=True, ondelete='cascade', tracking=True)
    lower_political_ids = fields.One2many('herbario.lower.political', 'province_id', 
                                         string='Cantones/Distritos')
    
    _sql_constraints = [
        ('name_country_uniq', 'unique(name, country_id)', 
         'El nombre de la provincia debe ser único por país!')
    ]

    def name_get(self):
        return [(record.id, f"{record.name}, {record.country_id.name}") 
                for record in self]

class LowerPolitical(models.Model):
    _name = 'herbario.lower.political'
    _description = 'Cantón/Distrito'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del Cantón', required=True, tracking=True)
    province_id = fields.Many2one('herbario.province', string='Provincia', 
                                 required=True, ondelete='cascade', tracking=True)
    locality_ids = fields.One2many('herbario.locality', 'lower_id', string='Localidades')

    _sql_constraints = [
        ('name_province_uniq', 'unique(name, province_id)', 
         'El nombre del cantón debe ser único por provincia!')
    ]

    def name_get(self):
        return [(record.id, f"{record.name}, {record.province_id.name}") 
                for record in self]

class Locality(models.Model):
    _name = 'herbario.locality'
    _description = 'Localidad'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre de la Localidad', required=True, tracking=True)
    lower_id = fields.Many2one('herbario.lower.political', string='Cantón', 
                              required=True, ondelete='cascade', tracking=True)
    vicinity_ids = fields.One2many('herbario.vicinity', 'locality_id', string='Vecindades')
    description = fields.Text(string='Descripción', tracking=True)
    
    # Campo computado para la ubicación completa
    ubicacion_completa = fields.Char(
        string='Ubicación Completa',
        compute='_compute_ubicacion_completa',
        store=True
    )

    @api.depends('name', 'lower_id.name', 'lower_id.province_id.name', 
                 'lower_id.province_id.country_id.name')
    def _compute_ubicacion_completa(self):
        for record in self:
            partes = [record.name]
            if record.lower_id:
                partes.append(record.lower_id.name)
                if record.lower_id.province_id:
                    partes.append(record.lower_id.province_id.name)
                    if record.lower_id.province_id.country_id:
                        partes.append(record.lower_id.province_id.country_id.name)
            record.ubicacion_completa = ', '.join(partes)

    def name_get(self):
        return [(record.id, f"{record.name}, {record.lower_id.name}") 
                for record in self]

class Vicinity(models.Model):
    _name = 'herbario.vicinity'
    _description = 'Vecindad'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Text(string='Nombre de la Vecindad', required=True, tracking=True)
    locality_id = fields.Many2one('herbario.locality', string='Localidad', 
                                 required=True, ondelete='cascade', tracking=True)
    description = fields.Text(string='Descripción', tracking=True)
    specimen_ids = fields.One2many('herbario.specimen', 'vicinity_id', string='Especímenes')
    coordinate_ids = fields.One2many('herbario.coordinates', 'vicinity_id', 
                                    string='Coordenadas')

    def name_get(self):
        return [(record.id, f"{record.name} ({record.locality_id.name})")
                for record in self]


# ============================================================================
# MODELO: COORDINATES - Coordenadas Geográficas de Referencia
# ============================================================================
class Coordinates(models.Model):
    """
    Coordenadas geográficas de referencia para vecindades.
    Pueden ser puntos de referencia, límites, centros, etc.
    """
    _name = 'herbario.coordinates'
    _description = 'Coordenadas Geográficas'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _order = 'id desc'

    # ========== RELACIÓN PRINCIPAL ==========
    vicinity_id = fields.Many2one(
        'herbario.vicinity',
        string='Vecindad',
        required=False,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    
    coordenadas_zona = fields.Char(
        string='Coordenadas en Grados',
        tracking=True,
        help="Ingrese coordenadas en formato '01.34S 78.40W' o '1°20\'30\"S 78°24\'15\"W'. "
             "El sistema calculará la latitud y longitud automáticamente."
    )

    # ========== COORDENADAS GPS ==========
    latitude = fields.Float(
        string='Latitud',
        digits=(12, 9),
        tracking=True,
        help='Latitud en grados decimales (-90 a 90)'
    )
    longitude = fields.Float(
        string='Longitud',
        digits=(12, 9),
        tracking=True,
        help='Longitud en grados decimales (-180 a 180)'
    )
    elevation = fields.Float(
        string='Elevación (m.s.n.m.)',
        digits=(7, 2),
        tracking=True,
        help='Elevación sobre el nivel del mar en metros'
    )

    # ========== FORMATO ALTERNATIVO ==========
    utm = fields.Char(
        string='Coordenadas UTM',
        tracking=True,
        help='Coordenadas en formato UTM (Universal Transverse Mercator)'
    )

    # ========== CAMPOS COMPUTADOS ==========
    maps_url = fields.Char(
        string='URL de Google Maps',
        compute='_compute_maps_url',
        store=True,
        help='Enlace directo a la ubicación en Google Maps'
    )

    # ========== DESCRIPCIÓN ==========
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción del punto: entrada, centro, límite, etc.'
    )
    tipo_punto = fields.Selection([
        ('centro', 'Punto Central'),
        ('entrada', 'Punto de Entrada'),
        ('limite', 'Límite/Perímetro'),
        ('referencia', 'Punto de Referencia'),
        ('otro', 'Otro')
    ], string='Tipo de Punto', default='referencia')

    # ========== MÉTODOS ONCHANGE PARA AUTOMATIZACIÓN ==========
    @api.onchange('coordenadas_zona')
    def _onchange_coordenadas_zona(self):
        """
        Parsea el campo 'coordenadas_zona' y actualiza latitud y longitud.
        Admite formatos como: 01.34S 78.40W
        """
        if not self.coordenadas_zona:
            return

        # Expresión regular para capturar los valores y direcciones
        pattern = re.compile(
            r"^\s*(\d{1,2}(?:\.\d{1,6})?)\s*([NSns])"  # Latitud: 1-2 dígitos, decimal opcional, N o S
            r"\s+"                                # Espacio separador
            r"(\d{1,3}(?:\.\d{1,6})?)\s*([WEwe])\s*$", # Longitud: 1-3 dígitos, decimal opcional, W o E
            re.IGNORECASE
        )
        
        match = pattern.match(self.coordenadas_zona)

        if match:
            try:
                lat_val, lat_dir, lon_val, lon_dir = match.groups()

                # Convertir a float y aplicar signo
                lat = float(lat_val)
                if lat_dir.upper() == 'S':
                    lat = -lat

                lon = float(lon_val)
                if lon_dir.upper() == 'W':
                    lon = -lon

                # Asignar a los campos, Odoo manejará la actualización en la vista
                self.latitude = lat
                self.longitude = lon
            except (ValueError, TypeError):
                # Si la conversión falla, no hacer nada
                pass

    @api.onchange('latitude', 'longitude')
    def _onchange_lat_lon(self):
        """
        Actualiza el campo 'coordenadas_zona' cuando cambian latitud o longitud.
        """
        if self.latitude is not None and self.longitude is not None:
            lat_abs = abs(self.latitude)
            lat_dir = 'S' if self.latitude < 0 else 'N'
            lon_abs = abs(self.longitude)
            lon_dir = 'W' if self.longitude < 0 else 'E'
            
            # Actualiza el campo de texto con el formato deseado
            self.coordenadas_zona = f"{lat_abs:.4f}{lat_dir} {lon_abs:.4f}{lon_dir}"

    # ========== MÉTODOS COMPUTADOS ==========
    @api.depends('latitude', 'longitude')
    def _compute_maps_url(self):
        """Genera URL de Google Maps con las coordenadas"""
        for record in self:
            if record.latitude and record.longitude:
                record.maps_url = f"https://www.google.com/maps?q={record.latitude},{record.longitude}"
            else:
                record.maps_url = False

    # ========== VALIDACIONES ==========
    @api.constrains('latitude', 'longitude', 'elevation')
    def _check_coordinates(self):
        """Valida que las coordenadas estén en rangos válidos"""
        for record in self:
            # Validar latitud
            if record.latitude:
                if record.latitude < -90 or record.latitude > 90:
                    raise ValidationError(
                        f'La latitud debe estar entre -90 y 90 grados.\n'
                        f'Valor ingresado: {record.latitude}'
                    )

            # Validar longitud
            if record.longitude:
                if record.longitude < -180 or record.longitude > 180:
                    raise ValidationError(
                        f'La longitud debe estar entre -180 y 180 grados.\n'
                        f'Valor ingresado: {record.longitude}'
                    )

            # Advertencia para elevaciones extremas
            if record.elevation:
                if record.elevation < -500 or record.elevation > 9000:
                    raise ValidationError(
                        f'La elevación parece fuera de rango (-500 a 9000 m).\n'
                        f'Valor ingresado: {record.elevation}\n'
                        f'Verifique el dato.'
                    )

    # ========== CONVERSIÓN AUTOMÁTICA DE FORMATO ==========
    @api.model
    def create(self, vals):
        """Convierte comas a puntos automáticamente al crear"""
        vals = self._convert_comma_to_dot(vals)
        return super().create(vals)

    def write(self, vals):
        """Convierte comas a puntos automáticamente al actualizar"""
        vals = self._convert_comma_to_dot(vals)
        return super().write(vals)

    def _convert_comma_to_dot(self, vals):
        """
        Convierte separadores decimales de coma (,) a punto (.)
        Soluciona el error: invalid input syntax for type numeric
        """
        coordinate_fields = ['latitude', 'longitude', 'elevation']

        for field in coordinate_fields:
            if field in vals and vals[field] is not None:
                value = vals[field]

                # Si viene como string con coma
                if isinstance(value, str):
                    # Limpiar espacios
                    value = value.strip()

                    # Reemplazar coma por punto
                    if ',' in value:
                        value = value.replace(',', '.')

                    # Convertir a float
                    try:
                        vals[field] = float(value) if value else None
                    except ValueError:
                        # Si falla, dejar como None o el original
                        vals[field] = None

                # Asegurar que sea float si es numérico
                elif isinstance(value, (int, float)):
                    vals[field] = float(value)

        return vals

    # ========== ACCIONES ==========
    def action_open_in_maps(self):
        """Abre la ubicación en Google Maps en nueva pestaña"""
        self.ensure_one()
        if not self.maps_url:
            raise ValidationError(
                'Esta ubicación no tiene coordenadas GPS válidas.\n'
                'Por favor ingrese latitud y longitud.'
            )

        return {
            'type': 'ir.actions.act_url',
            'url': self.maps_url,
            'target': 'new',
        }

    # ========== VISUALIZACIÓN ==========
    def name_get(self):
        """Nombre descriptivo para el registro"""
        result = []
        for record in self:
            if record.latitude is not None and record.longitude is not None:
                lat_abs = abs(record.latitude)
                lat_dir = 'S' if record.latitude < 0 else 'N'
                lon_abs = abs(record.longitude)
                lon_dir = 'W' if record.longitude < 0 else 'E'
                
                # Formato: 1.3800S 77.5300W
                name = f"{lat_abs:.4f}{lat_dir} {lon_abs:.4f}{lon_dir}"
            else:
                name = f"Coordenada #{record.id}"
            
            result.append((record.id, name))
        return result


# ============================================================================
# MODELO: COLLECTION SITE - Sitio de Colección del Espécimen
# ============================================================================
class CollectionSite(models.Model):
    """
    Sitio específico donde se recolectó un espécimen.
    Incluye información de colección, ubicación geográfica y coordenadas GPS propias.
    """
    _name = 'herbario.collection.site'
    _description = 'Sitio de Colección del Espécimen'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_recoleccion desc, id desc'

    # ========== RELACIONES PRINCIPALES ==========
    specimen_id = fields.Many2one(
        'herbario.specimen', 
        string='Espécimen', 
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True
    )
    herbarium_id = fields.Many2one(
        'herbario.herbarium', 
        string='Herbario',
        ondelete='restrict',
        tracking=True
    )
    
    # ========== UBICACIÓN GEOGRÁFICA JERÁRQUICA ==========
    country_id = fields.Many2one(
        'herbario.country', 
        string='País',
        ondelete='restrict',
        tracking=True
    )
    province_id = fields.Many2one(
        'herbario.province', 
        string='Provincia',
        ondelete='restrict',
        tracking=True,
        domain="[('country_id', '=', country_id)]"
    )
    lower_id = fields.Many2one(
        'herbario.lower.political', 
        string='Cantón/Distrito',
        ondelete='restrict',
        tracking=True,
        domain="[('province_id', '=', province_id)]"
    )
    locality_id = fields.Many2one(
        'herbario.locality', 
        string='Localidad',
        ondelete='restrict',
        tracking=True,
        domain="[('lower_id', '=', lower_id)]"
    )
    vicinity_id = fields.Many2one(
        'herbario.vicinity', 
        string='Vecindad',
        ondelete='restrict',
        tracking=True,
        domain="[('locality_id', '=', locality_id)]"
    )

    # ========== DATOS DE COLECCIÓN ==========
    numero_coleccion = fields.Char(
        string='Número de Colección',
        tracking=True,
        index=True,
        help='Número único asignado por el colector'
    )
    fecha_recoleccion = fields.Date(
        string='Fecha de Recolección',
        tracking=True,
        index=True,
        help='Fecha en que se recolectó el espécimen'
    )
    metodo_recoleccion = fields.Char(
        string='Método de Recolección',
        tracking=True,
        help='Técnica o método usado para recolectar'
    )
    is_primary = fields.Boolean(
        string='Ubicación Principal',
        default=False,
        tracking=True,
        help='Marcar como la ubicación principal de este espécimen'
    )
    
    # ========== NOTAS ADICIONALES ==========
    habitat = fields.Text(
        string='Descripción del Hábitat',
        help='Descripción del entorno, vegetación asociada, suelo, etc.'
    )
    notas_campo = fields.Text(
        string='Notas de Campo',
        help='Observaciones adicionales tomadas en campo'
    )

    # ========== RELACIÓN CON COORDENADAS ==========
    coordinate_id = fields.Many2one(
        'herbario.coordinates',
        string='Coordenadas GPS',
        ondelete='restrict',
        tracking=True,
        help='Coordenadas GPS asociadas a este sitio de colección'
    )

    # Campo relacionado para la entrada rápida de coordenadas en la vista de árbol
    coordenadas_zona = fields.Char(
        related='coordinate_id.coordenadas_zona',
        string='Coordenadas en Grados',
        readonly=False,  # Permite la edición para crear/actualizar la coordenada
        help="Ingrese coordenadas en formato '01.34S 78.40W'. "
             "Esto creará o actualizará el registro de coordenadas."
    )

    # ========== CAMPOS RELATED DE COORDENADAS ==========
    # Estos campos hacen que los datos de las coordenadas sean accesibles
    # directamente desde el sitio de colección, lo que es necesario para las vistas.
    latitude = fields.Float(
        related='coordinate_id.latitude',
        string='Latitud (Relacionada)',
        store=True, # store=True es necesario para que el campo sea buscable
        readonly=False
    )
    longitude = fields.Float(
        related='coordinate_id.longitude',
        string='Longitud (Relacionada)',
        store=True,
        readonly=False
    )
    elevation = fields.Float(
        related='coordinate_id.elevation',
        string='Elevación (Relacionada)',
        store=True,
        readonly=False
    )

    maps_url = fields.Char(
        related='coordinate_id.maps_url',
        string='URL del Mapa (Relacionado)',
        store=True,
        readonly=True
    )

    # ========== CAMPOS COMPUTADOS ==========
    ubicacion_completa = fields.Char(
        string='Ubicación Completa',
        compute='_compute_ubicacion_completa',
        store=False,
        help='Cadena con la jerarquía completa de ubicación'
    )

    # ========== MÉTODOS COMPUTADOS ==========
    @api.depends('vicinity_id', 'locality_id', 'lower_id', 'province_id', 'country_id')
    def _compute_ubicacion_completa(self):
        """Construye la ubicación completa en formato jerárquico"""
        for record in self:
            partes = []

            if record.vicinity_id:
                partes.append(record.vicinity_id.name)
            if record.locality_id:
                partes.append(record.locality_id.name)
            if record.lower_id:
                partes.append(record.lower_id.name)
            if record.province_id:
                partes.append(record.province_id.name)
            if record.country_id:
                partes.append(record.country_id.name)

            record.ubicacion_completa = ', '.join(partes) if partes else 'Sin ubicación registrada'

    # ========== VALIDACIONES ==========
    @api.constrains('is_primary', 'specimen_id')
    def _check_only_one_primary(self):
        """Asegura que solo haya UNA ubicación principal por espécimen"""
        for record in self:
            if record.is_primary and record.specimen_id:
                other_primary = self.search([
                    ('specimen_id', '=', record.specimen_id.id),
                    ('is_primary', '=', True),
                    ('id', '!=', record.id)
                ])
                if other_primary:
                    raise ValidationError(
                        f'YA EXISTE UNA UBICACIÓN PRINCIPAL\n\n'
                        f'El espécimen "{record.specimen_id.codigo_herbario}" ya tiene '
                        f'otra ubicación marcada como principal.\n\n'
                        f'Desmarca la otra antes de marcar esta como principal.'
                    )

    # ========== ACCIONES ==========
    def action_open_in_maps(self):
        """Abre la ubicación en Google Maps"""
        self.ensure_one()

        # Usar coordenadas del sitio si tiene, sino del coordinate_id
        if self.coordinate_id and self.coordinate_id.maps_url:
            url = self.coordinate_id.maps_url
        else:
            raise ValidationError(
                'SIN COORDENADAS GPS\n\n'
                'Esta ubicación no tiene coordenadas GPS registradas.\n'
                'Por favor asocie coordenadas GPS a este sitio de colección.'
            )

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_set_as_primary(self):
        """Marca este sitio como ubicación principal del espécimen"""
        self.ensure_one()
        
        # Desmarcar otras ubicaciones primarias del mismo espécimen
        other_primaries = self.search([
            ('specimen_id', '=', self.specimen_id.id),
            ('is_primary', '=', True),
            ('id', '!=', self.id)
        ])
        
        if other_primaries:
            other_primaries.write({'is_primary': False})
        
        # Marcar esta como primaria
        self.is_primary = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✓ Ubicación Principal',
                'message': f'Marcada como ubicación principal',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_copy_coordinates_from_vicinity(self):
        """Asocia coordenadas desde la vecindad si están disponibles"""
        self.ensure_one()

        if not self.vicinity_id:
            raise ValidationError('No hay una vecindad seleccionada.')

        # Buscar coordenadas de la vecindad
        coords = self.vicinity_id.coordinate_ids[:1]
        if not coords:
            raise ValidationError(
                'La vecindad seleccionada no tiene coordenadas de referencia registradas.'
            )

        # Asociar las coordenadas
        self.write({
            'coordinate_id': coords.id,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Coordenadas Asociadas',
                'message': f'Coordenadas asociadas desde {self.vicinity_id.name}',
                'type': 'success',
                'sticky': False,
            }
        }

    # ========== AUDITORÍA DE CAMBIOS ==========
    @api.model
    def create(self, vals):
        """Registra la creación de un nuevo sitio de colección."""
        site = super(CollectionSite, self).create(vals)
        if site.specimen_id:
            description = f"Se agregó el sitio de colección #{site.id} ({site.numero_coleccion or 'Sin Nro.'}) al espécimen."
            self.env['herbario.audit.log']._log_change(
                res_model='herbario.specimen',
                res_id=site.specimen_id.id,
                action='updated', # Agregar una ubicación es una actualización del espécimen
                description=description
            )
        return site

    def write(self, vals):
        """Registra las modificaciones en los sitios de colección."""
        tracked_fields = {
            'numero_coleccion': 'Número de Colección',
            'fecha_recoleccion': 'Fecha de Recolección',
            'country_id': 'País',
            'province_id': 'Provincia',
            'lower_id': 'Cantón/Distrito',
            'locality_id': 'Localidad',
            'vicinity_id': 'Vecindad',
            'coordinate_id': 'Coordenadas GPS',
            'latitude': 'Latitud',
            'longitude': 'Longitud',
            'elevation': 'Elevación',
            'habitat': 'Hábitat',
            'notas_campo': 'Notas de Campo',
        }

        for site in self:
            if not site.specimen_id:
                continue

            changes_to_log = []
            for field, label in tracked_fields.items():
                if field in vals:
                    old_value = site[field]
                    new_value_from_vals = vals[field]

                    # Manejo para campos Many2one
                    if site._fields[field].type == 'many2one':
                        old_display = old_value.display_name if old_value else "No asignado"
                        # El nuevo valor puede ser un ID (int)
                        if isinstance(new_value_from_vals, int):
                            new_record = self.env[site._fields[field].comodel_name].browse(new_value_from_vals)
                            new_display = new_record.display_name if new_record else "No asignado"
                        else:
                            new_display = new_value_from_vals or "No asignado"
                        
                        if old_display != new_display:
                            changes_to_log.append({'field': f"Ubicación: {label}", 'old': old_display, 'new': new_display})

                    # Manejo para otros tipos de campos
                    elif old_value != new_value_from_vals:
                        changes_to_log.append({'field': f"Ubicación: {label}", 'old': str(old_value or ''), 'new': str(new_value_from_vals or '')})
            
            if changes_to_log:
                description = f"Se modificó un sitio de colección del espécimen '{site.specimen_id.display_name}'."
                self.env['herbario.audit.log']._log_change('herbario.specimen', site.specimen_id.id, 'updated', description, changes=changes_to_log)

        return super(CollectionSite, self).write(vals)

    def unlink(self):
        """Registra la eliminación de un sitio de colección."""
        for site in self:
            if site.specimen_id:
                description = f"Se eliminó el sitio de colección #{site.id} (Nro. Colección: {site.numero_coleccion or 'N/A'}) del espécimen."
                self.env['herbario.audit.log']._log_change(
                    res_model='herbario.specimen',
                    res_id=site.specimen_id.id,
                    action='updated', # Eliminar una ubicación es una actualización del espécimen
                    description=description
                )
        return super(CollectionSite, self).unlink()

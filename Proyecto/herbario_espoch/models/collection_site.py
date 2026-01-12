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

    specimen_ids = fields.Many2many(
        'herbario.specimen',
        'herbario_specimen_herbarium_rel',
        'herbarium_id',
        'specimen_id',
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
                                required=False, ondelete='cascade', tracking=True)
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
                                 required=False, ondelete='cascade', tracking=True)
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
                              required=False, ondelete='cascade', tracking=True)
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
                                 required=False, ondelete='cascade', tracking=True)
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

    # ---------- Helper para parsear coordenadas en texto ----------
    def _parse_coordenadas_zona_str(self, text):
        """
        Recibe una cadena tipo '01.34S 78.40W' y devuelve (lat, lon) como floats,
        o (None, None) si no puede parsear.
        """
        if not text or not isinstance(text, str):
            return (None, None)
        pattern = re.compile(
            r"^\s*(\d{1,2}(?:\.\d{1,6})?)\s*([NSns])\s+(\d{1,3}(?:\.\d{1,6})?)\s*([WEwe])\s*$",
            re.IGNORECASE
        )
        m = pattern.match(text.strip())
        if not m:
            return (None, None)
        try:
            lat_val, lat_dir, lon_val, lon_dir = m.groups()
            lat = float(lat_val)
            if lat_dir.upper() == 'S':
                lat = -lat
            lon = float(lon_val)
            if lon_dir.upper() == 'W':
                lon = -lon
            return (lat, lon)
        except Exception:
            return (None, None)

    # ========== MÉTODOS ONCHANGE PARA AUTOMATIZACIÓN ==========
    @api.onchange('coordenadas_zona')
    def _onchange_coordenadas_zona(self):
        """
        Parsea el campo 'coordenadas_zona' y actualiza latitud y longitud.
        Admite formatos como: '01.34S 78.40W'
        """
        if not self.coordenadas_zona:
            self.latitude = 0.0
            self.longitude = 0.0
            return

        lat, lon = self._parse_coordenadas_zona_str(self.coordenadas_zona)
        if lat is not None and lon is not None:
            self.latitude = lat
            self.longitude = lon
        else:
            # If parsing fails, clear lat/lon to indicate invalid input
            self.latitude = 0.0
            self.longitude = 0.0

        # Original parsing logic (now replaced by _parse_coordenadas_zona_str)
        # # Expresión regular para capturar los valores y direcciones
        # pattern = re.compile(
        #     r"^\s*(\d{1,2}(?:\.\d{1,6})?)\s*([NSns])"  # Latitud: 1-2 dígitos, decimal opcional, N o S
        #     r"\s+"                                # Espacio separador
        #     r"(\d{1,3}(?:\.\d{1,6})?)\s*([WEwe])\s*$", # Longitud: 1-3 dígitos, decimal opcional, W o E
        #     re.IGNORECASE
        # )
        # match = pattern.match(self.coordenadas_zona)
        # if match:
        #     try:
        #         lat_val, lat_dir, lon_val, lon_dir = match.groups()
        #         lat = float(lat_val)
        #         if lat_dir.upper() == 'S':
        #             lat = -lat
        #         lon = float(lon_val)
        #         if lon_dir.upper() == 'W':
        #             lon = -lon
        #         self.latitude = lat
        #         self.longitude = lon
        #     except (ValueError, TypeError):
        #         pass

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
        return super(Coordinates, self).create(vals)

    def write(self, vals):
        """Convierte comas a puntos automáticamente al actualizar"""
        return super(Coordinates, self).write(vals)

    # ========== ACCIONES ==========
    def action_open_in_maps(self):
        """Abre la ubicación en Google Maps en nueva pestaña"""
        self.ensure_one()
        if not self.maps_url:
            raise ValidationError('Esta ubicación no tiene coordenadas GPS válidas.')
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
        ondelete='set null',
        tracking=True
    )
    province_id = fields.Many2one(
        'herbario.province', 
        string='Provincia',
        ondelete='set null',
        tracking=True,
        domain="['|', ('country_id', '=', country_id), ('country_id', '=', False)]"
    )
    lower_id = fields.Many2one(
        'herbario.lower.political', 
        string='Cantón/Distrito',
        ondelete='set null',
        tracking=True,
        domain="['|', ('province_id', '=', province_id), ('province_id', '=', False)]"
    )
    locality_id = fields.Many2one(
        'herbario.locality', 
        string='Localidad',
        ondelete='set null',
        tracking=True,
        domain="['|', ('lower_id', '=', lower_id), ('lower_id', '=', False)]"
    )
    vicinity_id = fields.Many2one(
        'herbario.vicinity', 
        string='Vecindad',
        ondelete='set null',
        tracking=True,
        domain="['|', ('locality_id', '=', locality_id), ('locality_id', '=', False)]"
    )

    # ========== DATOS DE COLECCIÓN ==========
    numero_coleccion = fields.Char(
        string='Número de Colección',
        tracking=True,
        index=True,
        help='Número único asignado por el colector',
        copy=False
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

    # CORRECCIÓN: Campo virtual (no related) para la entrada de datos.
    # Ahora es un campo related para que refleje el valor del coordinate_id
    coordenadas_zona = fields.Char(
        string='Coordenadas (Ingresar)',
        related='coordinate_id.coordenadas_zona',
        readonly=False, # Permitir edición para que el onchange funcione
        store=True, # Almacenar para búsqueda, el valor se sincroniza con el related
        force_save="1", # Asegura que los cambios se guarden en el registro relacionado
        help="Ingrese coordenadas en formato '01.34S 78.40W'."
    )

    # ========== CAMPOS RELATED DE COORDENADAS ==========
    # Estos campos hacen que los datos de las coordenadas sean accesibles
    # directamente desde el sitio de colección, lo que es necesario para las vistas.
    # Se añade force_save="1" para que los cambios en estos campos se propaguen
    # al registro de herbario.coordinates.
    latitude = fields.Float(
        related='coordinate_id.latitude',
        string='Latitud (Relacionada)',
        store=True, # store=True es necesario para que el campo sea buscable
        readonly=False, # Permitir que el onchange lo actualice
        force_save="1" # Asegura que los cambios se guarden en el registro relacionado
    )
    longitude = fields.Float(
        related='coordinate_id.longitude',
        string='Longitud (Relacionada)',
        store=True,
        readonly=False, # Permitir que el onchange lo actualice
        force_save="1" # Asegura que los cambios se guarden en el registro relacionado
    )
    elevation = fields.Float(
        related='coordinate_id.elevation',
        string='Elevación (Relacionada)',
        store=True,
        readonly=False, # Permitir edición manual o por onchange
        force_save="1" # Asegura que los cambios se guarden en el registro relacionado
    )

    # Campos 'sombra' de tipo Char para la entrada de datos en la vista de árbol.
    # Esto evita el error de conversión de Odoo con comas decimales.
    latitude_char = fields.Char(
        string='Latitud (Texto)',
        compute='_compute_char_fields',
        inverse='_inverse_latitude_char',
        store=False # No se guardan en la base de datos
    )
    longitude_char = fields.Char(
        string='Longitud (Texto)',
        compute='_compute_char_fields',
        inverse='_inverse_longitude_char',
        store=False
    )
    # ========== MÉTODOS ONCHANGE PARA AUTOMATIZACIÓN EN COLLECTION.SITE ==========
    @api.onchange('coordenadas_zona')
    def _onchange_coordenadas_zona_collection_site(self):
        """
        Parsea el campo 'coordenadas_zona' y actualiza latitud y longitud
        en el CollectionSite, lo que a su vez actualiza el Coordinate relacionado.
        """
        if not self.coordenadas_zona:
            self.latitude = 0.0
            self.longitude = 0.0
            return

        # Llama al helper de parseo del modelo herbario.coordinates
        lat, lon = self.env['herbario.coordinates']._parse_coordenadas_zona_str(self.coordenadas_zona)
        if lat is not None and lon is not None:
            self.latitude = lat
            self.longitude = lon
        else:
            self.latitude = 0.0
            self.longitude = 0.0

    @api.onchange('latitude', 'longitude')
    def _onchange_lat_lon_collection_site(self):
        """
        Actualiza el campo de texto 'coordenadas_zona' cuando cambian
        manualmente la latitud o longitud.
        """
        # Este onchange ahora también actualiza los campos _char para mantener la sincronización.
        self._compute_char_fields()

        # Solo actuar si ambos campos tienen un valor numérico y están en el rango correcto.
        lat_valid = isinstance(self.latitude, float) and -90 <= self.latitude <= 90
        lon_valid = isinstance(self.longitude, float) and -180 <= self.longitude <= 180

        if lat_valid and lon_valid:
            lat_abs = abs(self.latitude)
            lat_dir = 'S' if self.latitude < 0 else 'N'
            lon_abs = abs(self.longitude)
            lon_dir = 'W' if self.longitude < 0 else 'E'
            
            self.coordenadas_zona = f"{lat_abs:.6f}{lat_dir} {lon_abs:.6f}{lon_dir}"

    # ========== ONCHANGE PARA JERARQUÍA DE UBICACIÓN ==========
    @api.onchange('country_id')
    def _onchange_country_id(self):
        """ Limpieza hacia abajo: si cambia el país, se limpian los niveles inferiores. """
        if self.province_id and self.province_id.country_id != self.country_id:
            self.province_id = False
            self.lower_id = False
            self.locality_id = False
            self.vicinity_id = False

    @api.onchange('province_id')
    def _onchange_province_id(self):
        """ Corrección hacia arriba y limpieza hacia abajo. """
        if self.province_id and self.province_id.country_id:
            self.country_id = self.province_id.country_id
        if self.lower_id and self.lower_id.province_id != self.province_id:
            self.lower_id = False
            self.locality_id = False
            self.vicinity_id = False

    @api.onchange('lower_id')
    def _onchange_lower_id(self):
        """ Corrección hacia arriba y limpieza hacia abajo. """
        if self.lower_id and self.lower_id.province_id:
            self.province_id = self.lower_id.province_id
        if self.locality_id and self.locality_id.lower_id != self.lower_id:
            self.locality_id = False
            self.vicinity_id = False

    @api.onchange('locality_id')
    def _onchange_locality_id(self):
        """ Corrección hacia arriba y limpieza hacia abajo. """
        if self.locality_id and self.locality_id.lower_id:
            self.lower_id = self.locality_id.lower_id
        if self.vicinity_id and self.vicinity_id.locality_id != self.locality_id:
            self.vicinity_id = False

    @api.onchange('vicinity_id')
    def _onchange_vicinity_id(self):
        """ Corrección hacia arriba. """
        if self.vicinity_id and self.vicinity_id.locality_id:
            self.locality_id = self.vicinity_id.locality_id
            # Esto desencadenará en cascada los otros onchanges hacia arriba
            # para rellenar cantón, provincia y país si no están ya establecidos.
            if self.locality_id.lower_id:
                self.lower_id = self.locality_id.lower_id


    # Métodos compute/inverse para los campos Char 'sombra'
    @api.depends('latitude', 'longitude')
    def _compute_char_fields(self):
        """Actualiza los campos de texto cuando los campos float cambian."""
        for record in self:
            record.latitude_char = str(record.latitude or '0.0')
            record.longitude_char = str(record.longitude or '0.0')
            
    def _inverse_latitude_char(self):
        """
        Se activa al escribir en el campo de texto de latitud.
        Limpia la entrada y actualiza el campo float real.
        El onchange de 'latitude' se encargará del resto.
        """
        for record in self:
            if record.latitude_char:
                try:
                    # Reemplazar coma y convertir a float
                    clean_value = record.latitude_char.strip().replace(',', '.')
                    record.latitude = float(clean_value)
                except (ValueError, TypeError):
                    record.latitude = 0.0

    def _inverse_longitude_char(self):
        """Actualiza el campo float cuando el campo de texto de longitud cambia."""
        for record in self:
            if record.longitude_char:
                try:
                    clean_value = record.longitude_char.strip().replace(',', '.')
                    record.longitude = float(clean_value)
                except (ValueError, TypeError):
                    record.longitude = 0.0

    maps_url = fields.Char(
        related='coordinate_id.maps_url',
        string='URL del Mapa (Relacionado)',
        store=True,
        readonly=True # Este sí debe ser siempre de solo lectura
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
    # CORRECCIÓN: Sobrescribir create y write para manejar la creación/actualización de coordenadas
    @api.model
    def create(self, vals):
        # Si no se proporciona un coordinate_id, pero hay datos de coordenadas,
        # crear un registro de coordenadas vacío para que los campos related puedan escribir en él.
        # Los campos related con force_save=True se encargarán de escribir los valores.

        if not vals.get('coordinate_id') and any(vals.get(f) for f in ['coordenadas_zona', 'latitude', 'longitude', 'elevation']):
            new_coord = self.env['herbario.coordinates'].create({})
            vals['coordinate_id'] = new_coord.id

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
        # Procesar cada registro individualmente para manejar la creación de coordinate_id si es necesario
        for site in self:
            current_vals = dict(vals) # Copia de vals para cada registro

            # Si no hay coordinate_id pero se están proporcionando datos de coordenadas, crear uno.
            if not site.coordinate_id and any(current_vals.get(f) for f in ['coordenadas_zona', 'latitude', 'longitude', 'elevation']):
                new_coord = self.env['herbario.coordinates'].create({})
                current_vals['coordinate_id'] = new_coord.id

            # Llamar al super.write para el registro actual con los valores potencialmente modificados
            super(CollectionSite, site).write(current_vals)

        return True # write method should return True

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
                        f'Ya existe una ubicación principal para el espécimen "{record.specimen_id.codigo_herbario}".\n\n'
                        f'Por favor, desmarque la otra ubicación antes de marcar esta como principal.'
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

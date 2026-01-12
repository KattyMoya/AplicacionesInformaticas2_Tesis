from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
from datetime import datetime
import uuid


class SpecimenRegistry(models.Model):
    _name = 'herbario.specimen'
    _description = 'Registro de Especímenes Botánicos'
    _order = 'codigo_herbario desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Identificador único para URL pública (Hash)
    url_hash = fields.Char(
        string='Hash URL',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: str(uuid.uuid4())
    )

    # Identificación
    codigo_herbario = fields.Char(
        string='Código Herbario',
        required=True,
        index=True,
        copy=False,
        readonly=True,
        default='Nuevo',  # CAMBIO: Mostrar "Nuevo" en lugar de generar el código
        store=True,
        tracking=True,
        help='Código único CHEP-XXXXXXX (se genera automáticamente al guardar)'
    )
    numero_cartulina = fields.Integer(
        string='Número de Cartulina',
        index=True,
        help='Número físico de cartulina del herbario'
    )

    #Relacion principal
    taxon_id = fields.Many2one(
        'herbario.taxon',
        string='Taxón',
        ondelete='restrict',
        index=True,
        tracking=True
    )

    # --- CAMPOS SOMBRA PARA CREACIÓN/EDICIÓN INLINE DE TAXÓN ---
    # Estos campos no se almacenan y solo se usan en la vista para la entrada de datos.
    taxon_name_new = fields.Char(
        string='Nombre Científico (Nuevo Taxón)',
        help="Escriba el nombre completo (ej. 'Género especie') para crear un nuevo taxón.",
        store=False
    )
    taxon_family_id = fields.Many2one(
        'herbario.family',
        string='Familia (Nuevo Taxón)',
        help="Seleccione la familia para crear un nuevo taxón.",
        store=False
    )
    taxon_genero = fields.Char(
        string='Género',
        help="Género del taxón, calculado automáticamente.",
        readonly=True,
        store=False # No es necesario almacenarlo aquí
    )
    taxon_especie = fields.Char(
        string='Especie',
        help="Especie del taxón, calculada automáticamente.",
        readonly=True,
        store=False # No es necesario almacenarlo aquí
    )
    # Campos relacionados para mostrar el género y especie del taxón seleccionado
    taxon_genero_related = fields.Char(
        related='taxon_id.genero', 
        string='Género (del Taxón)', 
        readonly=True
    )
    taxon_especie_related = fields.Char(
        related='taxon_id.especie', 
        string='Especie (del Taxón)', 
        readonly=True
    )
    taxon_family_related = fields.Many2one(
        'herbario.family',
        related='taxon_id.family_id',
        string='Familia (del Taxón)',
        readonly=True # CORRECCIÓN: Debe ser readonly para evitar creación implícita y conflictos.
    )

    # Campos que vienen del taxón (related fields)
    nombre_cientifico = fields.Char(
        related='taxon_id.name',
        string='Nombre Científico',
        store=True,
        readonly=True
    )
    
    author_ids = fields.Many2many(
        'herbario.author',
        'herbario_specimen_author',
        'specimen_id',
        'author_id',
        string='Autores',
        tracking=True
    )
    
    collector_ids = fields.Many2many(
        'herbario.collector',
        'herbario_specimen_collector',
        'specimen_id',
        'collector_id',
        string='Colectores',
        tracking=True
    )

    # Identificación y Determinación
    determiner_ids = fields.Many2many(
        'herbario.determiner',
        'herbario_specimen_determiner',
        'specimen_id',
        'determiner_id',
        string='Determinadores',
        tracking=True
    )
    
    # Campos descriptivos
    index_text = fields.Char( # Este es el único campo necesario.
        string='Índice',
        tracking=True,
        help='Índice de referencia. Escriba para buscar o crear, o seleccione uno existente de la lista.'
    )
    
    herbarium_ids = fields.Many2many(
        'herbario.herbarium',
        'herbario_specimen_herbarium_rel',
        'specimen_id',
        'herbarium_id',
        string='Herbarios',
        tracking=True,
        help='Herbarios a los que pertenece o está duplicado el espécimen'
    )

    # Descripción
    description_specimen = fields.Text(
        string='Descripción de la Especie',
        help='Descripción botánica detallada'
    )
    phenology = fields.Char(
        string='Fenología',
        help='Estado fenológico general (floración, fructificación, etc.)'
    )
    
    def _get_year_selection(self):
        """Genera una lista de años desde 1950 hasta el año actual."""
        current_year = datetime.now().year
        # Devuelve una lista de tuplas (valor, etiqueta), ej: [('2024', '2024'), ...]
        return [(str(year), str(year)) for year in range(current_year, 1949, -1)]

    patente_year = fields.Selection(
        selection=_get_year_selection,
        string='Año de Patente',
        help='Año de patente o registro oficial'
    )

    # Relaciones
    vicinity_id = fields.Many2one(
        'herbario.vicinity',
        string='Vecindad',
        ondelete='restrict',
        tracking=True
    )

    # coordinate_id eliminado - ahora las coordenadas se manejan a través de collection_site_ids
    coordinate_id = fields.Many2one(
        'herbario.coordinates',
        string='Coordenadas GPS (Principal)',
        ondelete='set null',
        tracking=True
    )
    
    collection_date = fields.Date(
        string='Fecha de Colección',
        tracking=True,
        help='Fecha en que se recolectó el espécimen'
    )
    
    # Campo computado para mostrar el historial de cambios.
    audit_log_ids = fields.One2many(
        'herbario.audit.log',
        compute='_compute_audit_log_ids',
        string='Historial de Cambios'
    )

    collection_site_ids = fields.One2many(
        'herbario.collection.site',
        'specimen_id',
        string='Sitios de Colección'
    )
    
    elevation = fields.Float(
        string='Elevación (m.s.n.m.)',
        tracking=True,
        help='Elevación sobre el nivel del mar en metros'
    )
    # Relaciones con otros modelos
    # Acceder a imágenes directamente desde taxon_id
    # Este campo ahora es el principal y está relacionado con las imágenes del taxón.
    # Se le permite la escritura para que desde el formulario del espécimen se puedan
    # añadir/modificar las imágenes que pertenecen al taxón.
    image_ids = fields.One2many(
        'herbario.image',
        related='taxon_id.image_ids',
        string='Imágenes',
        readonly=False # Es crucial para poder añadir imágenes desde el espécimen al taxón.
    )

    # Acceder a QR codes directamente desde taxon_id
    # Los QR codes se relacionan con el taxón, no con el espécimen
    qr_code_ids = fields.One2many(
        'herbario.qr.code',
        'taxon_id',
        string='Códigos QR',
        related='taxon_id.qr_code_ids',
        readonly=True
    )

    # Campos Computados
    total_ubicaciones = fields.Integer(
        string='Total de Ubicaciones',
        compute='_compute_total_ubicaciones',
        store=False  # CORRECCIÓN: Quitar store=True para que se calcule siempre en tiempo real.
    )
    primary_image = fields.Binary(
        string='Imagen Principal',
        compute='_compute_primary_image'
    )
    primary_location = fields.Char(
        string='Ubicación Principal',
        compute='_compute_primary_location'
    )

    # Estado y Auditoría (sin cambios, solo contexto)
    status = fields.Selection([('borrador', 'Borrador'), ('revision', 'En Revisión'), ('activo', 'Activo'), ('archivado', 'Archivado'), ('eliminado', 'Eliminado')], string='Estado', default='borrador', required=True, index=True, tracking=True)

    # Campos de auditoría
    created_by = fields.Many2one('res.users', string='Creado Por', default=lambda self: self.env.user, readonly=True)
    created_at = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now, readonly=True)
    updated_by = fields.Many2one('res.users', string='Modificado Por')
    updated_at = fields.Datetime(string='Última Modificación')

    # Campos para el sitio web
    es_publico = fields.Boolean(string='Visible en Web', default=True)

    _sql_constraints = [
        ('codigo_herbario_unique', 'UNIQUE(codigo_herbario)', 'El código de herbario debe ser único.'),
        ('url_hash_unique', 'UNIQUE(url_hash)', 'El hash de URL debe ser único.'),
    ]
    
    @api.model
    def _get_next_code(self):
        """Genera el siguiente código CHEP-XXXXXXX"""
        # Buscar el último código registrado
        last_specimen = self.search([
            ('codigo_herbario', '!=', 'Nuevo'),
            ('codigo_herbario', 'like', 'CHEP-%'),
            ('codigo_herbario', 'not like', '%(Provisional)') # Excluir códigos provisionales
        ], order='id desc', limit=1)
        
        if last_specimen and last_specimen.codigo_herbario:
            try:
                # Extraer el número del último código (ej: CHEP-0000001 -> 1)
                code_part = last_specimen.codigo_herbario.split('-')[-1]
                last_number = int(re.search(r'\d+', code_part).group())
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        # Generar el nuevo código con formato CHEP-0000001 (7 dígitos)
        return f'CHEP-{new_number:07d}'

    @api.model
    def _get_existing_indices(self):
        """
        Busca todos los valores únicos del campo index_text y los devuelve
        en el formato que espera un campo Selection. Es una consulta eficiente.
        """
        self.env.cr.execute("SELECT DISTINCT index_text FROM herbario_specimen WHERE index_text IS NOT NULL AND index_text != '' ORDER BY index_text")
        existing_values = self.env.cr.fetchall()
        # Convierte [('A-01',), ('B-02',)] a [('A-01', 'A-01'), ('B-02', 'B-02')]
        return [(val[0], val[0]) for val in existing_values]

    @api.depends('collection_site_ids')
    def _compute_total_ubicaciones(self):
        """Cuenta el total de ubicaciones desde collection_site_ids"""
        for record in self:
            record.total_ubicaciones = len(record.collection_site_ids)
    
    @api.depends('taxon_id', 'taxon_id.image_ids', 'taxon_id.image_ids.is_primary')
    def _compute_primary_image(self):
        """Obtiene la imagen principal directamente desde el taxón."""
        for record in self:
            primary_img_record = self.env['herbario.image'] # Iniciar un recordset vacío
            if record.taxon_id and record.taxon_id.image_ids:
                # 1. Buscar la imagen marcada como principal
                primary_img_record = record.taxon_id.image_ids.filtered(lambda img: img.is_primary)[:1] # CORRECCIÓN: Tomar solo el primer resultado
                # 2. Si no hay principal, tomar la primera de la lista
                if not primary_img_record:
                    primary_img_record = record.taxon_id.image_ids[:1]
            
            # Asignar el campo binario de forma segura
            record.primary_image = primary_img_record.image_data if primary_img_record else False

    @api.onchange('taxon_name_new')
    def _onchange_taxon_name_new(self):
        """
        Parsea el nombre del nuevo taxón para autocompletar género y especie.
        """
        if self.taxon_name_new:
            parts = self.taxon_name_new.strip().split()
            if len(parts) >= 2:
                self.taxon_genero = parts[0].capitalize()
                self.taxon_especie = ' '.join(parts[1:]).lower()
            elif len(parts) == 1:
                self.taxon_genero = parts[0].capitalize()
                self.taxon_especie = 'indeterminado'
        else:
            self.taxon_genero = ''
            self.taxon_especie = ''
    
    @api.depends('collection_site_ids', 'collection_site_ids.is_primary', 'collection_site_ids.ubicacion_completa')
    def _compute_primary_location(self):
        """Obtiene la ubicación completa desde collection_site_ids usando el campo computado"""
        for record in self:
            primary_site = record.collection_site_ids.filtered(lambda s: s.is_primary) or record.collection_site_ids[:1]
            if primary_site:
                record.primary_location = primary_site[0].ubicacion_completa
            else:
                record.primary_location = 'Sin ubicación registrada'

    @api.model
    def create(self, vals, **kwargs):
        """
        Override para:
        1. Manejar la creación de un nuevo taxón a partir de los campos sombra.
        2. Asignar el código secuencial del herbario.
        3. Registrar la creación en el log de auditoría.
        """
        # --- LÓGICA DE CREACIÓN DE TAXÓN ---
        if not vals.get('taxon_id') and vals.get('taxon_name_new') and vals.get('taxon_family_id'):
            taxon_name = vals.get('taxon_name_new')
            family_val = vals.get('taxon_family_id') # Puede ser un ID (int) o un comando (tuple)
            
            final_family_id = None

            # 1. Determinar el ID de la familia, manejando la creación "al vuelo".
            if isinstance(family_val, int):
                # Caso 1: Se seleccionó una familia existente.
                final_family_id = family_val
            elif isinstance(family_val, tuple) and family_val[0] == 0:
                # Caso 2: Se está creando una nueva familia. El valor es (0, 0, {'name': '...'})
                family_create_vals = family_val[2]
                # Buscar si ya existe para evitar duplicados, si no, crearla.
                family = self.env['herbario.family'].search([('name', '=', family_create_vals.get('name'))], limit=1)
                final_family_id = family.id if family else self.env['herbario.family'].create(family_create_vals).id

            # 2. Con el ID de la familia resuelto, buscar o crear el taxón.
            if final_family_id:
                new_taxon_id = self._find_or_create_taxon_id(taxon_name, final_family_id)
                if new_taxon_id:
                    # Asignar el ID del taxón resultante de vuelta a 'vals' para que se guarde.
                    vals['taxon_id'] = new_taxon_id
        elif vals.get('taxon_name_new') and not vals.get('taxon_family_id'):
            # Si solo se da el nombre pero no la familia, lanzar el error.
            raise ValidationError("Debe seleccionar una familia para crear un nuevo taxón.")

        if not vals.get('codigo_herbario') or vals.get('codigo_herbario') == 'Nuevo':
            vals['codigo_herbario'] = self._get_next_code()
        
        # Limpiar los campos sombra ANTES de llamar a super() para evitar conflictos.
        clean_vals = {k: v for k, v in vals.items() if k not in ['taxon_name_new', 'taxon_family_id']}
        specimen = super(SpecimenRegistry, self).create(clean_vals)

        # Registrar creación en el nuevo audit_log
        description = f"Se creó el espécimen '{specimen.display_name}' con código {specimen.codigo_herbario}."
        self.env['herbario.audit.log']._log_change(
            res_model='herbario.specimen',
            res_id=specimen.id,
            action='created',
            description=description
        )
        return specimen

    def _find_or_create_taxon_id(self, taxon_name, family_id):
        """
        Busca o crea un taxón y DEVUELVE su ID.
        Esta es una función helper que no modifica diccionarios.
        """
        if not taxon_name or not family_id:
            return None

        # 1. Parsear el nombre para obtener género y especie
        parts = taxon_name.strip().split()
        genero = 'Indeterminado'
        especie = 'indeterminado'
        if len(parts) >= 2:
            genero = parts[0].capitalize()
            especie = ' '.join(parts[1:]).lower()
        elif len(parts) == 1:
            genero = parts[0].capitalize()

        # 2. Buscar si ya existe un taxón con estos datos
        existing_taxon = self.env['herbario.taxon'].search([
            # CORRECCIÓN: La restricción SQL es solo por genero y especie.
            # La búsqueda debe coincidir con la restricción para evitar errores de unicidad.
            ('genero', '=', genero),
            ('especie', '=', especie)
        ], limit=1)

        if existing_taxon:
            return existing_taxon.id
        else:
            # Si no existe, creamos el nuevo taxón y devolvemos su ID
            new_taxon = self.env['herbario.taxon'].create({
                'family_id': family_id, 'genero': genero, 'especie': especie})
            return new_taxon.id

    def write(self, vals):
        """Override para crear taxón si es necesario y registrar cambios."""

        # Lista de campos a auditar
        tracked_fields = {
            'taxon_id': 'Taxón',
            'numero_cartulina': 'Número de Cartulina',
            'index_text': 'Texto Índice',
            'herbarium_ids': 'Herbarios',
            'author_ids': 'Autores',
            'collector_ids': 'Colectores',
            'determiner_ids': 'Determinadores',
            'status': 'Estado',
            'es_publico': 'Es Público',
            'description_specimen': 'Descripción',
            'phenology': 'Fenología',
        }

        vals['updated_by'] = self.env.user.id
        vals['updated_at'] = fields.Datetime.now()

        old_values = {}
        # Solo iterar si hay campos auditables en los valores a escribir
        if any(field in vals for field in tracked_fields):
            for specimen in self:
                old_values[specimen.id] = {}
                for field in tracked_fields:
                    if field in vals:
                        old_values[specimen.id][field] = specimen[field]

        # --- LÓGICA DE CREACIÓN DE TAXÓN (para edición) ---
        if not vals.get('taxon_id') and vals.get('taxon_name_new') and vals.get('taxon_family_id'):
            taxon_name = vals.get('taxon_name_new')
            family_val = vals.get('taxon_family_id')
            final_family_id = None

            if isinstance(family_val, int):
                final_family_id = family_val
            elif isinstance(family_val, tuple) and family_val[0] == 0:
                family_create_vals = family_val[2]
                family = self.env['herbario.family'].search([('name', '=', family_create_vals.get('name'))], limit=1)
                final_family_id = family.id if family else self.env['herbario.family'].create(family_create_vals).id

            if final_family_id:
                new_taxon_id = self._find_or_create_taxon_id(taxon_name, final_family_id)
                if new_taxon_id:
                    vals['taxon_id'] = new_taxon_id
        elif vals.get('taxon_name_new') and not vals.get('taxon_family_id'):
            raise ValidationError("Debe seleccionar una familia para crear un nuevo taxón.")

        # Limpiar los campos sombra ANTES de llamar a super()
        clean_vals = {k: v for k, v in vals.items() if k not in ['taxon_name_new', 'taxon_family_id']}
        if not clean_vals: # Si después de limpiar no hay nada que escribir, no continuar.
            return True

        result = super(SpecimenRegistry, self).write(clean_vals)

        for record in self:
            if record.id in old_values:
                changes_to_log = []
                for field, old_value in old_values[record.id].items():
                    new_value = record[field]

                    # Formatear valores para que sean legibles en el log
                    if record._fields[field].type == 'many2one':
                        old_display = old_value.display_name if old_value else "No asignado"
                        new_display = new_value.display_name if new_value else "No asignado"
                    elif record._fields[field].type == 'many2many':
                        old_display = ", ".join(old_value.mapped('name')) or "Vacío"
                        new_display = ", ".join(new_value.mapped('name')) or "Vacío"
                    else:
                        old_display = old_value
                        new_display = new_value

                    if old_display != new_display:
                        changes_to_log.append({
                            'field': tracked_fields.get(field, field),
                            'old': old_display,
                            'new': new_display,
                        })

                if changes_to_log:
                    description = f"Se modificó el espécimen '{record.display_name}'."
                    self.env['herbario.audit.log']._log_change(
                        res_model='herbario.specimen',
                        res_id=record.id,
                        action='updated',
                        description=description,
                        changes=changes_to_log
                    )
        return result

    def unlink(self):
        """Override para registrar eliminación con el nuevo sistema de auditoría."""
        for record in self:
            description = f"Se eliminó el espécimen '{record.display_name}' (Código: {record.codigo_herbario})."
            self.env['herbario.audit.log']._log_change(
                res_model='herbario.specimen',
                res_id=record.id,
                action='deleted',
                description=description
            )
        return super(SpecimenRegistry, self).unlink()
    
    def action_generate_qr(self):
        """Acción para generar código QR"""
        self.ensure_one()
        return self.env['herbario.qr.code'].generate_qr_for_specimen(self)

    def action_view_history(self):
        """Acción para ver historial de cambios"""
        self.ensure_one()
        return {
            'name': f'Historial de {self.codigo_herbario}',
            'type': 'ir.actions.act_window',
            'res_model': 'herbario.audit.log',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', 'herbario.specimen'), ('res_id', '=', self.id)],
            'context': {}
        }

    def name_get(self):
        """Personaliza el nombre mostrado"""
        result = []
        for record in self:
            name = f"{record.codigo_herbario}"
            if record.nombre_cientifico:
                name += f" - {record.nombre_cientifico}"
            if record.collection_date:
                name += f" ({record.collection_date})"
            result.append((record.id, name))
        return result

    def _compute_audit_log_ids(self):
        """
        Busca en el log de auditoría todos los registros relacionados con este espécimen.
        """
        for specimen in self:
            specimen.audit_log_ids = self.env['herbario.audit.log'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', specimen.id)
            ])
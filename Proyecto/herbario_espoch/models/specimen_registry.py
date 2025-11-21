from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class SpecimenRegistry(models.Model):
    _name = 'herbario.specimen'
    _description = 'Registro de Especímenes Botánicos'
    _order = 'codigo_herbario desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
    # Campo auxiliar para saber si ya está guardado
    is_new_record = fields.Boolean(default=True, copy=False)
    
    numero_cartulina = fields.Integer(
        string='Número de Cartulina',
        index=True,
        help='Número físico de cartulina del herbario'
    )

    #Relacion principal
    taxon_id = fields.Many2one(
        'herbario.taxon',
        string='Taxón',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True
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
    index_text = fields.Char(
        string='Texto Índice',
        tracking=True,
        help='Texto de indexación para búsquedas'
    )
    
    herbarium_id = fields.Many2one(
        'herbario.herbarium',
        string='Herbario',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Herbario al que pertenece el espécimen'
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
    patente_year = fields.Integer(
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
    # Las imágenes se relacionan con el taxón. Este campo muestra esas imágenes.
    image_ids = fields.One2many(
        'herbario.image',
        related='taxon_id.image_ids', # Muestra las imágenes del taxón
        string='Imágenes',
        readonly=False # Permite la creación, el contexto de la vista se encarga del resto.
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
        store=True
    )
    primary_image = fields.Binary(
        string='Imagen Principal',
        compute='_compute_primary_image'
    )
    primary_image_base64 = fields.Char(
        string='Imagen Principal Base64',
        compute='_compute_primary_image_base64'
    )
    primary_location = fields.Char(
        string='Ubicación Principal',
        compute='_compute_primary_location'
    )

    # Estado y Auditoría
    status = fields.Selection([
        ('borrador', 'Borrador'),
        ('revision', 'En Revisión'),
        ('activo', 'Activo'),
        ('archivado', 'Archivado'),
        ('eliminado', 'Eliminado')
    ], string='Estado', default='borrador', required=True, index=True, tracking=True)

    # Campos de auditoría
    created_by = fields.Many2one('res.users', string='Creado Por', default=lambda self: self.env.user, readonly=True)
    created_at = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now, readonly=True)
    updated_by = fields.Many2one('res.users', string='Modificado Por')
    updated_at = fields.Datetime(string='Última Modificación')

    # Campos para el sitio web
    es_publico = fields.Boolean(string='Visible en Web', default=True)

    _sql_constraints = [
        ('codigo_herbario_unique', 'UNIQUE(codigo_herbario)', 'El código de herbario debe ser único.'),
    ]
    
    @api.depends('is_new_record')
    def _compute_codigo_herbario(self):
        """Muestra el código provisional o el real"""
        for record in self:
            # Si el registro aún no tiene ID, significa que no se ha guardado todavía
            if not record.id or record.is_new_record:
                # Calcular el siguiente código que se asignará
                last_specimen = self.search([
                    ('is_new_record', '=', False),
                    ('codigo_herbario', 'like', 'CHEP-%')
                ], order='id desc', limit=1)

                if last_specimen and last_specimen.codigo_herbario:
                    try:
                        last_number = int(last_specimen.codigo_herbario.split('-')[-1])
                        next_number = last_number + 1
                    except (ValueError, IndexError):
                        next_number = 1
                else:
                    next_number = 1

                record.codigo_herbario = f'CHEP-{next_number:07d} (Provisional)'
            else:
                # Si ya tiene un ID, asumimos que el registro ya está guardado
                # (puedes mantener el mismo código o dejar vacío)
                record.codigo_herbario = record.codigo_herbario or ''

    @api.model
    def _get_next_code(self):
        """Genera el siguiente código CHEP-XXXXXXX"""
        # Buscar el último código registrado
        last_specimen = self.search([
            ('codigo_herbario', '!=', 'Nuevo'),
            ('codigo_herbario', 'like', 'CHEP-%')
        ], order='id desc', limit=1)
        
        if last_specimen and last_specimen.codigo_herbario:
            try:
                # Extraer el número del último código (ej: CHEP-0000001 -> 1)
                last_number = int(last_specimen.codigo_herbario.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        # Generar el nuevo código con formato CHEP-0000001 (7 dígitos)
        return f'CHEP-{new_number:07d}'

    @api.depends('collection_site_ids')
    def _compute_total_ubicaciones(self):
        """Cuenta el total de ubicaciones desde collection_site_ids"""
        for record in self:
            record.total_ubicaciones = len(record.collection_site_ids)
    
    @api.depends('taxon_id.image_ids')
    def _compute_primary_image(self):
        """Obtiene la imagen principal del taxón"""
        for record in self:
            if record.taxon_id and record.taxon_id.image_ids:
                primary_img = record.taxon_id.image_ids.filtered(lambda img: img.is_primary)
                if primary_img:
                    record.primary_image = primary_img[0].image_data
                else:
                    record.primary_image = record.taxon_id.image_ids[0].image_data
            else:
                record.primary_image = False

    @api.depends('primary_image')
    def _compute_primary_image_base64(self):
        """Convierte la imagen binaria a base64 string"""
        for record in self:
            if record.primary_image:
                try:
                    if isinstance(record.primary_image, str):
                        record.primary_image_base64 = record.primary_image
                    else:
                        record.primary_image_base64 = record.primary_image.decode('utf-8')
                except (AttributeError, UnicodeDecodeError):
                    record.primary_image_base64 = False
            else:
                record.primary_image_base64 = False

    
    @api.depends('collection_site_ids', 'collection_site_ids.ubicacion_completa')
    def _compute_primary_location(self):
        """Obtiene la ubicación completa desde collection_site_ids usando el campo computado"""
        for record in self:
            primary_site = record.collection_site_ids.filtered(lambda s: s.is_primary) or record.collection_site_ids[:1]
            if primary_site:
                site = primary_site[0]
                record.primary_location = site.ubicacion_completa or 'Sin ubicación registrada'
            else:
                record.primary_location = 'Sin ubicación registrada'

    def _compute_audit_log_ids(self):
        """
        Busca en el log de auditoría todos los registros relacionados con este espécimen.
        """
        for specimen in self:
            specimen.audit_log_ids = self.env['herbario.audit.log'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', specimen.id)
            ])

    @api.model
    def create(self, vals):
        """Override para asignar código y registrar creación en el nuevo sistema de auditoría."""
        if not vals.get('codigo_herbario') or vals.get('codigo_herbario') == 'Nuevo':
            vals['codigo_herbario'] = self._get_next_code()
        
        specimen = super(SpecimenRegistry, self).create(vals)
        
        # Registrar creación en el nuevo audit_log
        description = f"Se creó el espécimen '{specimen.display_name}' con código {specimen.codigo_herbario}."
        self.env['herbario.audit.log']._log_change(
            res_model='herbario.specimen',
            res_id=specimen.id,
            action='created',
            description=description
        )
        return specimen

    def write(self, vals):
        """Override para registrar cambios en el historial con el nuevo sistema de auditoría."""
        # Lista de campos a auditar
        tracked_fields = {
            'taxon_id': 'Taxón',
            'numero_cartulina': 'Número de Cartulina',
            'index_text': 'Texto Índice',
            'herbarium_id': 'Herbario',
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

        result = super(SpecimenRegistry, self).write(vals)

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
        return self.env['herbario.qr.code'].generate_qr_for_taxon(self.taxon_id)

    #NUEVO: Normalización de taxones -------------------------------
    @api.depends('nombre_cientifico', 'familia', 'genero', 'especie')
    def _compute_taxon_id(self):
        """Asigna o crea el taxón automáticamente basado en nombre_cientifico"""
        for record in self:
            if record.nombre_cientifico:
                # Busca si ya existe un taxón con el mismo nombre científico
                taxon = self.env['herbario.taxon'].search([
                    ('nombre_cientifico', '=', record.nombre_cientifico)
                ], limit=1)
                if not taxon:
                    # Crea un nuevo taxón si no existe
                    taxon = self.env['herbario.taxon'].create({
                        'nombre_cientifico': record.nombre_cientifico,
                        'familia': record.familia,
                        'genero': record.genero,
                        'especie': record.especie,
                        #'autor_cientifico': record.autor_cientifico,
                    })
                record.taxon_id = taxon.id
            else:
                record.taxon_id = False

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
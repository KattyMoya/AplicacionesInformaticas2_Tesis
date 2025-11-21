from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import hashlib
import os
from PIL import Image
from io import BytesIO
import json

class HerbarioImage(models.Model):
    _name = 'herbario.image'
    _description = 'Imágenes de Especímenes Botánicos'
    _order = 'display_order asc, id asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Relaciones
    specimen_id = fields.Many2one(
        'herbario.specimen',
        string='Espécimen',
        required=False, # No es requerido directamente, se usa para obtener el taxón. Se vuelve requerido por la lógica de la vista.
        store=True,     # CORRECCIÓN: Es crucial para guardar la relación.
        index=True
    )
    taxon_id = fields.Many2one(
        'herbario.taxon',
        string='Taxón',
        required=True, # La imagen siempre debe pertenecer a un taxón.
        ondelete='cascade',
        index=True,
        tracking=True
    )

    # Información del archivo
    filename_original = fields.Char(
        string='Nombre Original',
        required=True,
        help='Nombre original del archivo subido'
    )
    filename_stored = fields.Char(
        string='Nombre Almacenado',
        help='Nombre UUID del archivo almacenado'
    )
    
    # Imagen y datos binarios
    image_data = fields.Binary(
        string='Imagen',
        attachment=True,
        required=True
    )
    thumbnail = fields.Binary(
        string='Miniatura Pequeña',
        #compute='_compute_thumbnails',
        #store=True,
        readonly=True
    )
    thumbnail_medium = fields.Binary(
        string='Miniatura Mediana',
        #compute='_compute_thumbnails',
        #store=True,
        readonly=True
    )
    
    # Metadatos del archivo
    file_size = fields.Integer(
        string='Tamaño (bytes)',
        readonly=True,
        #compute='_compute_file_metadata',
        #store=True,
        help='Tamaño del archivo en bytes'
    )
    image_width = fields.Integer(
        string='Ancho (px)',
        readonly=True
        #compute='_compute_file_metadata',
        #store=True
    )
    image_height = fields.Integer(
        string='Alto (px)',
        #compute='_compute_file_metadata',
        #store=True
        readonly=True
    )
    mime_type = fields.Char(
        string='Tipo MIME',
        default='image/jpeg',
        help='Tipo MIME del archivo'
    )
    file_hash = fields.Char(
        string='Hash SHA-256',
        readonly=True,
        #compute='_compute_file_hash',
        #store=True,
        index=True,
        help='Hash para detección de duplicados'
    )
    
    # Datos EXIF
    exif_data = fields.Text(
        string='Datos EXIF',
        help='Metadatos EXIF extraídos de la imagen (JSON)'
    )
    exif_camera = fields.Char(
        string='Cámara',
        readonly=True
        #compute='_compute_exif_fields',
        #store=True
    )
    exif_date = fields.Datetime(
        string='Fecha de Captura',
        readonly=True
        #compute='_compute_exif_fields',
        #store=True
    )
    
    # Descripción y orden
    description = fields.Char(
        string='Descripción',
        help='Descripción de la imagen (ej: Vista del haz, Detalle de flores)'
    )
    is_primary = fields.Boolean(
        string='Imagen Principal',
        default=False,
        help='Indica si es la imagen principal del espécimen'
    )
    display_order = fields.Integer(
        string='Orden de Visualización',
        default=1,
        help='Orden en que se muestra en la galería'
    )
    
    # Auditoría
    uploaded_by = fields.Many2one(
        'res.users',
        string='Subido Por',
        default=lambda self: self.env.user,
        readonly=True
    )
    uploaded_at = fields.Datetime(
        string='Fecha de Subida',
        default=fields.Datetime.now,
        readonly=True
    )
    deleted_at = fields.Datetime(
        string='Fecha de Eliminación',
        help='Borrado lógico'
    )

    # Campos adicionales
    photographer = fields.Many2one('res.partner', string="Fotógrafo", help="El fotógrafo que tomó la imagen", tracking=True)

    # Campos computados
    file_size_human = fields.Char(
        string='Tamaño',
        compute='_compute_file_size_human'
    )
    resolution = fields.Char(
        string='Resolución',
        compute='_compute_resolution'
    )
   
    specimen_codigo = fields.Char(
        string='Código del Espécimen',
        compute='_compute_specimen_info',
        store=False,
        help='Código CHEP del espécimen asociado'
    )

    specimen_nombre_cientifico = fields.Char(
        string='Nombre Científico',
        compute='_compute_specimen_info',
        store=False,
        help='Nombre científico del espécimen asociado'
    )

    specimen_display = fields.Char(
        string='ID Técnico del Espécimen',
        compute='_compute_specimen_info',
        store=False,
        help='Referencia técnica del espécimen (herbario.specimen,ID)'
    )
    
    # Validación para asegurar que la imagen esté relacionada con al menos un registro
    @api.constrains('taxon_id', 'specimen_id')
    def _check_relations(self):
        for record in self:
            if not record.taxon_id and not record.specimen_id:
                raise ValidationError('La imagen debe estar relacionada con un Taxón')
    

    def _process_image(self, image_data_b64):
        """Procesa la imagen y genera todos los metadatos y miniaturas"""
        if not image_data_b64:
            return {}
        
        try:
            image_bytes = base64.b64decode(image_data_b64)
            image_stream = BytesIO(image_bytes)
            image = Image.open(image_stream)
            
            result = {
                'file_size': len(image_bytes),
                'image_width': image.width,
                'image_height': image.height,
                'file_hash': hashlib.sha256(image_bytes).hexdigest(),
            }
            
            # Generar miniaturas
            # Miniatura pequeña (80x80)
            image_small = image.copy()
            image_small.thumbnail((80, 80), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
            output_small = BytesIO()
            image_small.save(output_small, format='PNG')
            result['thumbnail'] = base64.b64encode(output_small.getvalue())
            
            # Miniatura mediana (200x200)
            image_medium = image.copy()
            image_medium.thumbnail((200, 200), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
            output_medium = BytesIO()
            image_medium.save(output_medium, format='PNG')
            result['thumbnail_medium'] = base64.b64encode(output_medium.getvalue())
            
            # Extraer EXIF
            exif_dict = self._extract_exif_dict(image)
            if exif_dict:
                result['exif_data'] = json.dumps(exif_dict)
                result['exif_camera'] = exif_dict.get('camera', '')
                result['exif_date'] = exif_dict.get('date_taken', False)
            
            return result
        except Exception as e:
            return {
                'file_size': 0,
                'image_width': 0,
                'image_height': 0,
            }

    def _extract_exif_dict(self, image):
        """Extrae EXIF como diccionario"""
        try:
            exif_dict = {}
            if hasattr(image, '_getexif') and image._getexif():
                from PIL.ExifTags import TAGS
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['Make', 'Model', 'DateTime', 'DateTimeOriginal']:
                        exif_dict[tag.lower()] = str(value)
                
                # Formar el nombre de la cámara
                if 'make' in exif_dict or 'model' in exif_dict:
                    camera_parts = []
                    if 'make' in exif_dict:
                        camera_parts.append(exif_dict['make'])
                    if 'model' in exif_dict:
                        camera_parts.append(exif_dict['model'])
                    exif_dict['camera'] = ' '.join(camera_parts)
                
                # Fecha
                if 'datetimeoriginal' in exif_dict:
                    exif_dict['date_taken'] = exif_dict['datetimeoriginal']
                elif 'datetime' in exif_dict:
                    exif_dict['date_taken'] = exif_dict['datetime']
            
            return exif_dict if exif_dict else None
        except Exception:
            return None
        
    @api.onchange('image_data')
    def _onchange_image_data(self):
        """Calcula metadatos en tiempo real cuando se sube la imagen"""
        if self.image_data:
            metadata = self._process_image(self.image_data)
            # Actualizar los campos en el formulario (no en BD aún)
            self.file_size = metadata.get('file_size', 0)
            self.image_width = metadata.get('image_width', 0)
            self.image_height = metadata.get('image_height', 0)
            self.file_hash = metadata.get('file_hash', False)
            self.thumbnail = metadata.get('thumbnail', False)
            self.thumbnail_medium = metadata.get('thumbnail_medium', False)
            self.exif_data = metadata.get('exif_data', False)
            self.exif_camera = metadata.get('exif_camera', '')
            self.exif_date = metadata.get('exif_date', False)
            # 🔹 Si no tiene nombre de archivo, generar automáticamente
            if not self.filename_original:
                self.filename_original = "imagen_%s" % fields.Datetime.now().strftime("%Y%m%d_%H%M%S")

    @api.depends('file_size')
    def _compute_file_size_human(self):
        for record in self:
            if record.file_size:
                size = float(record.file_size)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        record.file_size_human = f"{size:.2f} {unit}"
                        break
                    size /= 1024.0
            else:
                record.file_size_human = '0 B'
                
    @api.depends('taxon_id', 'taxon_id.name')
    def _compute_specimen_info(self):
        """Obtiene información del taxón asociado"""
        for record in self:
            if record.taxon_id:
                record.specimen_codigo = 'N/A (Imagen de Taxón)'
                record.specimen_nombre_cientifico = record.taxon_id.name
                record.specimen_display = f'herbario.taxon,{record.taxon_id.id}'
            else:
                record.specimen_codigo = 'Sin taxón'
                record.specimen_nombre_cientifico = 'Sin taxón'
                record.specimen_display = 'N/A'

    @api.depends('image_width', 'image_height')
    def _compute_resolution(self):
        for record in self:
            if record.image_width and record.image_height:
                record.resolution = f"{record.image_width}x{record.image_height}"
            else:
                record.resolution = 'Desconocida'

    @api.constrains('file_hash')
    def _check_duplicate_image(self):
        for record in self:
            if record.file_hash:
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('specimen_id', '=', record.specimen_id.id),
                    ('file_hash', '=', record.file_hash),
                    ('deleted_at', '=', False)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f'Esta imagen ya existe para este espécimen (subida el {duplicate.uploaded_at}).'
                    )

    @api.model
    def create(self, vals):
        # 🔹 Generar automáticamente el nombre del archivo si no se proporciona
        if not vals.get('filename_original'):
            vals['filename_original'] = "imagen_%s" % datetime.now().strftime("%Y%m%d_%H%M%S")

        # 🔹 Procesar metadatos de imagen
        if vals.get('image_data'):
            metadata = self._process_image(vals['image_data'])
            vals.update(metadata)

        # 🔹 Gestionar imagen principal (si no hay otra, esta será la principal)
        if vals.get('taxon_id'):
            existing_images = self.search([
                ('taxon_id', '=', vals['taxon_id']),
                ('deleted_at', '=', False)
            ])
            if not existing_images:
                vals['is_primary'] = True

        # 🔹 Si se marca como principal, desmarcar las demás
        if vals.get('is_primary') and vals.get('taxon_id'):
            self.search([
                ('taxon_id', '=', vals['taxon_id']),
                ('is_primary', '=', True),
                ('deleted_at', '=', False)
            ]).write({'is_primary': False})

        # 🔹 Crear el registro
        image = super(HerbarioImage, self).create(vals)

        # 🔹 Registrar en el historial del espécimen padre
        if image.taxon_id:
            description = f"Se añadió una nueva imagen ('{image.filename_original or 'imagen sin nombre'}') al taxón '{image.taxon_id.name}'."
            self.env['herbario.audit.log']._log_change(
                res_model='herbario.taxon',
                res_id=image.taxon_id.id,
                action='updated', # Añadir una imagen es una actualización del espécimen
                description=description
            )

        return image

    def write(self, vals):
        # Si se actualiza la imagen, recalcular metadatos
        if vals.get('image_data'):
            metadata = self._process_image(vals['image_data'])
            vals.update(metadata)
        
        # --- Auditoría ---
        for record in self:
            if record.taxon_id:
                changes = []
                if 'description' in vals:
                    changes.append({'field': 'Descripción de Imagen', 'old': record.description, 'new': vals['description']})
                if 'is_primary' in vals and vals['is_primary']:
                    changes.append({'field': 'Imagen Principal', 'old': 'No', 'new': 'Sí'})
                
                if changes:
                    description = f"Se modificó una imagen del taxón '{record.taxon_id.name}'."
                    self.env['herbario.audit.log']._log_change('herbario.taxon', record.taxon_id.id, 'updated', description, changes=changes)
        # --- Fin Auditoría ---

        if vals.get('is_primary'):
            for record in self:
                self.search([
                    ('taxon_id', '=', record.taxon_id.id),
                    ('id', '!=', record.id),
                    ('is_primary', '=', True),
                    ('deleted_at', '=', False)
                ]).write({'is_primary': False})
        
        return super(HerbarioImage, self).write(vals)

    def unlink(self):
        """Borrado lógico"""
        for image in self:
            # Registrar fecha de eliminación
            image.write({'deleted_at': fields.Datetime.now()})

            if image.taxon_id:
                description = f"Se eliminó una imagen ('{image.filename_original or 'imagen sin nombre'}') del taxón '{image.taxon_id.name}'."
                self.env['herbario.audit.log']._log_change('herbario.taxon', image.taxon_id.id, 'updated', description)

                # Si era imagen principal, limpiar la referencia visual
                #if image.is_primary:
                    #image.specimen_id.primary_image = False

                # 🔁 Forzar recomputar la miniatura del espécimen
                #image.specimen_id._compute_primary_image()
        return True

    def action_set_as_primary(self):
        """Establece esta imagen como principal"""
        self.ensure_one()
        self.search([
            ('taxon_id', '=', self.taxon_id.id),
            ('id', '!=', self.id),
            ('is_primary', '=', True),
            ('deleted_at', '=', False)
        ]).write({'is_primary': False})
        self.write({'is_primary': True})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def name_get(self):
        """Muestra el nombre científico del espécimen en lugar del nombre del archivo"""
        result = []
        for record in self:
            # Usar el nombre científico del taxón
            if record.taxon_id and record.taxon_id.name:
                name = record.taxon_id.name
            else:
                # Fallback al nombre original del archivo
                name = record.description or record.filename_original or 'Imagen sin nombre'
            
            # Agregar estrella si es imagen principal
            if record.is_primary:
                name = f"⭐ {name}"
            
            result.append((record.id, name))
        return result
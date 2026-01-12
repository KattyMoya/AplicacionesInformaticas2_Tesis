from odoo import models, fields, api
from odoo.exceptions import ValidationError
import qrcode
from io import BytesIO
import base64
import hashlib

ERROR_CORRECTION_MAP = {
    'L': qrcode.constants.ERROR_CORRECT_L,  # 7%
    'M': qrcode.constants.ERROR_CORRECT_M,  # 15%
    'Q': qrcode.constants.ERROR_CORRECT_Q,  # 25%
    'H': qrcode.constants.ERROR_CORRECT_H,  # 30%
}


class HerbarioQRCode(models.Model):
    """Modelo para códigos QR de taxones"""
    _name = 'herbario.qr.code'
    _description = 'Códigos QR de Taxones'
    _order = 'generation_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # ========== RELACIONES ==========
    specimen_id = fields.Many2one(
        'herbario.specimen',
        string='Espécimen',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True
    )

    taxon_id = fields.Many2one(
        'herbario.taxon',
        related='specimen_id.taxon_id',
        string='Taxón',
        store=True,
        readonly=True
    )

    specimen_code = fields.Char(
        related='specimen_id.codigo_herbario',
        string="Código de Espécimen",
        store=True,
        readonly=True
    )

    specimen_ref = fields.Char(
        string="Referencia Técnica",
        compute='_compute_specimen_ref',
        store=False
    )

    # ========== DATOS DEL QR ==========
    qr_image = fields.Binary(
        string='Imagen QR',
        attachment=True,
        help='Imagen del código QR generada'
    )

    qr_url = fields.Char(
        string='URL del QR',
        required=True,
        help='URL que el QR codifica'
    )

    qr_data = fields.Char(
        string='Datos del QR',
        help='Datos adicionales del código QR'
    )

    # ========== CONFIGURACIÓN QR ==========
    resolution = fields.Selection([
        ('300', '300x300 px (Pequeño)'),
        ('600', '600x600 px (Mediano)'),
        ('1200', '1200x1200 px (Grande)'),
        ('2400', '2400x2400 px (Muy Grande)')
    ], string='Resolución', default='600', required=True)

    error_correction = fields.Selection([
        ('L', 'Bajo (7%)'),
        ('M', 'Medio (15%)'),
        ('Q', 'Alto (25%)'),
        ('H', 'Máximo (30%)')
    ], string='Corrección de Errores', default='H')

    box_size = fields.Integer(string='Tamaño de Caja', default=10)
    border = fields.Integer(string='Borde', default=4)

    # ========== ESTADÍSTICAS DE USO ==========
    download_count = fields.Integer(
        string='Descargas',
        default=0,
        readonly=True
    )
    last_downloaded_at = fields.Datetime(
        string='Última Descarga',
        readonly=True
    )

    scan_count = fields.Integer(
        string='Escaneos',
        default=0,
        readonly=True
    )
    last_scanned_at = fields.Datetime(
        string='Último Escaneo',
        readonly=True
    )

    # ========== VERSIONAMIENTO ==========
    version = fields.Integer(
        string='Versión QR',
        default=1,
        tracking=True
    )

    status = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('deprecated', 'Obsoleto')
    ], string='Estado', default='draft', tracking=True, required=True)

    obsolete = fields.Boolean(
        string='Obsoleto',
        default=False,
        help='Indica si el QR fue regenerado'
    )

    # ========== AUDITORÍA ==========
    generated_by = fields.Many2one(
        'res.users',
        string='Generado Por',
        default=lambda self: self.env.user,
        readonly=True
    )
    generation_date = fields.Datetime(
        string='Fecha de Generación',
        default=fields.Datetime.now,
        readonly=True
    )

    # ========== CAMPOS COMPUTADOS ==========
    taxon_name = fields.Char(
        string='Nombre Científico',
        compute='_compute_taxon_name',
        store=True
    )

    qr_filename = fields.Char(
        string='Nombre de Archivo',
        compute='_compute_qr_filename'
    )

    file_size_bytes = fields.Integer(
        string='Tamaño (Bytes)',
        compute='_compute_file_size'
    )

    checksum = fields.Char(
        string='Checksum SHA256',
        compute='_compute_checksum'
    )

    # ========== RELACIONES ONE2MANY ==========
    scan_log_ids = fields.One2many(
        'herbario.qr.scan.log',
        'qr_code_id',
        string='Historial de Escaneos'
    )

    # ========== CONSTRAINTS ==========
    _sql_constraints = [
        ('unique_active_specimen_qr',
         'UNIQUE(specimen_id, status)',
         'Solo puede haber un código QR activo por espécimen.')
    ]

    # ========== MÉTODOS COMPUTADOS ==========
    @api.depends('specimen_id', 'specimen_id.taxon_id.name')
    def _compute_taxon_name(self):
        """Obtiene el nombre científico del taxón"""
        for record in self:
            record.taxon_name = record.specimen_id.taxon_id.name if record.specimen_id and record.specimen_id.taxon_id else ''

    @api.depends('specimen_id')
    def _compute_specimen_ref(self):
        for record in self:
            if record.specimen_id:
                record.specimen_ref = f"herbario.specimen,{record.specimen_id.id}"
            else:
                record.specimen_ref = ""

    @api.depends('specimen_id.codigo_herbario', 'version')
    def _compute_qr_filename(self):
        """Genera nombre de archivo para descarga"""
        for record in self:
            if record.specimen_id and record.specimen_id.codigo_herbario:
                safe_code = "".join([c for c in record.specimen_id.codigo_herbario if c.isalnum() or c in ('-','_')])
                record.qr_filename = f"QR_{safe_code}_v{record.version}.png"
            else:
                record.qr_filename = f"QR_specimen_v{record.version}.png"

    @api.depends('qr_image')
    def _compute_file_size(self):
        """Calcula tamaño de la imagen QR"""
        for record in self:
            try:
                if record.qr_image:
                    if isinstance(record.qr_image, str):
                        data = record.qr_image + '=' * (-len(record.qr_image) % 4)
                        decoded = base64.b64decode(data, validate=True)
                        record.file_size_bytes = len(decoded)
                    elif isinstance(record.qr_image, bytes):
                        record.file_size_bytes = len(base64.b64decode(record.qr_image))
                    else:
                        record.file_size_bytes = 0
                else:
                    record.file_size_bytes = 0
            except Exception:
                record.file_size_bytes = 0

    @api.depends('qr_image')
    def _compute_checksum(self):
        """Calcula checksum SHA256 de la imagen"""
        for record in self:
            if record.qr_image:
                try:
                    image_bytes = base64.b64decode(record.qr_image)
                    record.checksum = hashlib.sha256(image_bytes).hexdigest()
                except Exception:
                    record.checksum = False
            else:
                record.checksum = False

    # ========== MÉTODOS PRINCIPALES ==========
    def _generate_qr_image(self, qr_content=None):
        """Genera la imagen QR basada en los datos"""
        self.ensure_one()

        qr_data = qr_content or self.qr_url

        error_correction_value = ERROR_CORRECTION_MAP.get(
            self.error_correction,
            qrcode.constants.ERROR_CORRECT_H
        )

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_correction_value,
            box_size=self.box_size or 10,
            border=self.border or 4
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_image = base64.b64encode(buffer.getvalue())

    @api.model
    def create(self, vals):
        """Al crear, genera automáticamente la imagen QR"""
        record = super(HerbarioQRCode, self).create(vals)
        if not record.qr_image:
            record._generate_qr_image()
        return record

    def write(self, vals):
        """Si cambian parámetros de QR, regenera la imagen"""
        res = super(HerbarioQRCode, self).write(vals)
        if any(field in vals for field in ['resolution', 'error_correction', 'box_size', 'border', 'qr_url']):
            for record in self:
                record._generate_qr_image()
        return res

    @api.constrains('status')
    def _check_active_qr(self):
        """Valida que solo haya un QR activo por espécimen"""
        for record in self:
            if record.status == 'active':
                active_qrs = self.search([
                    ('specimen_id', '=', record.specimen_id.id),
                    ('status', '=', 'active'),
                    ('id', '!=', record.id)
                ])
                if active_qrs:
                    raise ValidationError(
                        'Ya existe un código QR activo para este espécimen. '
                        'Desactive el existente antes de activar uno nuevo.'
                    )

    # ========== ACCIONES ==========
    def action_download(self):
        """Descarga la imagen QR e incrementa contador"""
        self.ensure_one()
        self.write({
            'download_count': self.download_count + 1,
            'last_downloaded_at': fields.Datetime.now()
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/herbario.qr.code/{self.id}/qr_image/{self.qr_filename}?download=true',
            'target': 'self',
        }

    def action_regenerate(self):
        """Regenera el QR y marca el anterior como obsoleto"""
        self.ensure_one()
        self.write({'obsolete': True})
        
        new_qr = self.create({
            'specimen_id': self.specimen_id.id,
            'qr_url': self.qr_url,
            'qr_data': self.qr_data,
            'version': self.version + 1,
            'status': 'draft',
            'resolution': self.resolution,
            'error_correction': self.error_correction,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'herbario.qr.code',
            'view_mode': 'form',
            'res_id': new_qr.id,
            'target': 'current',
        }

    def action_set_active(self):
        """Establece el QR como activo"""
        self.ensure_one()
        self.write({'status': 'active'})

    def action_set_inactive(self):
        """Establece el QR como inactivo"""
        self.ensure_one()
        self.write({'status': 'inactive'})

    def action_set_deprecated(self):
        """Establece el QR como deprecado"""
        self.ensure_one()
        self.write({'status': 'deprecated'})

    def register_scan(self):
        """Registra un escaneo del QR"""
        self.ensure_one()
        self.write({
            'scan_count': self.scan_count + 1,
            'last_scanned_at': fields.Datetime.now()
        })

    def action_open_in_maps(self):
        """Abre el URL del QR en una ventana nueva"""
        self.ensure_one()
        if self.qr_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.qr_url,
                'target': 'new',
            }
        raise ValidationError('No hay URL asociada a este código QR.')

    def toggle_obsolete(self):
        """Alterna el estado de obsoleto"""
        self.ensure_one()
        self.write({'obsolete': not self.obsolete})

    @api.model
    def generate_qr_for_specimen(self, specimen):
        """
        Busca un QR activo para un espécimen. Si no existe, crea uno nuevo.
        Devuelve una acción para abrir la vista del QR.
        """
        if not specimen:
            raise ValidationError("No se puede generar un QR sin un espécimen asociado.")

        # Buscar un QR activo existente para este espécimen
        existing_qr = self.search([
            ('specimen_id', '=', specimen.id),
            ('status', '=', 'active')
        ], limit=1)

        if existing_qr:
            qr_id = existing_qr.id
        else:
            # Si no hay QR activo, crear uno nuevo apuntando al detalle del espécimen
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # Ruta al detalle del espécimen
            qr_url = f"{base_url}/herbario/specimen/{specimen.id}"

            new_qr = self.create({
                'specimen_id': specimen.id,
                'qr_url': qr_url,
                'status': 'active',  # Lo creamos como activo directamente
                'resolution': '600',
                'error_correction': 'H',
            })
            qr_id = new_qr.id

        return {
            'name': 'Código QR del Espécimen',
            'type': 'ir.actions.act_window',
            'res_model': 'herbario.qr.code',
            'view_mode': 'form',
            'res_id': qr_id,
            'target': 'current',
        }

    # ========== DISPLAY NAME ==========
    def name_get(self):
        """Personaliza el nombre mostrado"""
        result = []
        for record in self:
            status_label = dict(record._fields['status'].selection).get(record.status, '')
            specimen_code = record.specimen_id.codigo_herbario or 'Sin Código'
            name = f"QR {specimen_code} v{record.version} [{status_label}]"
            if record.obsolete:
                name += " (OBSOLETO)"
            result.append((record.id, name))
        return result

from odoo import models, fields, api
from odoo.http import request
import json

class HerbarioQRScanLog(models.Model):
    _name = 'herbario.qr.scan.log'
    _description = 'Historial de Escaneos de QR'
    _order = 'scanned_at desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Relación con QR Code
    qr_code_id = fields.Many2one(
        'herbario.qr.code',
        string='Código QR',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Relación
    """
    specimen_id = fields.Many2one(
        'herbario.specimen',
        string='Espécimen',
        related='qr_code_id.specimen_id',
        store=True,
        readonly=True
    )"""
    taxon_id = fields.Many2one(
        'herbario.taxon',
        string='Taxón',
        related='qr_code_id.taxon_id',
        store=True,
        readonly=True,
        index=True
    )

    # Información del escaneo
    scanned_at = fields.Datetime(
        string='Fecha de Escaneo',
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )
    
    ip_address = fields.Char(
        string='Dirección IP',
        readonly=True
    )
    
    user_agent = fields.Char(
        string='Navegador/Dispositivo',
        readonly=True
    )
    
    location = fields.Char(
        string='Ubicación',
        readonly=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        readonly=True
    )

    def name_get(self):
        result = []
        for record in self:
            name = f"Escaneo {record.id}"
            if record.taxon_id:
                name += f" - {record.taxon_id.name}"
            if record.scanned_at:
                name += f" ({record.scanned_at.strftime('%Y-%m-%d %H:%M')})"
            result.append((record.id, name))
        return result
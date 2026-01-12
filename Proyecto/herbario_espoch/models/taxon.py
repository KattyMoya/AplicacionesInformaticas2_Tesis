from odoo import models, fields, api  # Agrega 'api' aquí
from odoo.exceptions import ValidationError

class HerbarioFamily(models.Model):
    _name = 'herbario.family'
    _description = 'Familia Botánica'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre de Familia',
        required=True,
        index=True,
        tracking=True
    )
    description = fields.Text(
        string='Descripción',
        tracking=True
    )
    taxon_ids = fields.One2many(
        'herbario.taxon',
        'family_id',
        string='Taxones'
    )
    total_taxons = fields.Integer(
        string='Total de Taxones',
        compute='_compute_total_taxons',
        store=True
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El nombre de la familia debe ser único!')
    ]

    @api.depends('taxon_ids')
    def _compute_total_taxons(self):
        for record in self:
            record.total_taxons = len(record.taxon_ids)

    def name_get(self):
        return [(record.id, record.name) for record in self]

class HerbarioTaxon(models.Model):
    _name = 'herbario.taxon'
    _description = 'Taxón del Herbario'
    _order = 'genero, especie'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    name = fields.Char(
        string='Nombre Científico',
        compute='_compute_scientific_name',
        store=True,
        index=True
    )
    genero = fields.Char(
        string='Género',
        index=True,
        tracking=True,
        default='Indeterminado'
    )
    especie = fields.Char(
        string='Especie',
        index=True,
        tracking=True,
        default='Indeterminado'
    )

    # Relaciones
    family_id = fields.Many2one(
        'herbario.family',
        string='Familia',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True
    )
    specimen_ids = fields.One2many(
        'herbario.specimen',
        'taxon_id',
        string='Especímenes'
    )
    image_ids = fields.One2many(
        'herbario.image',
        'taxon_id',
        string='Imágenes',
        auto_join=True,
        ondelete='cascade'
    )
    qr_code_ids = fields.One2many(
        'herbario.qr.code',
        'taxon_id',
        string='Códigos QR'
    )

    # Campos computados
    total_specimens = fields.Integer(
        string='Total Especímenes',
        compute='_compute_total_specimens',
        store=True
    )
    total_images = fields.Integer(
        string='Total Imágenes',
        compute='_compute_total_images',
        store=True
    )

    _sql_constraints = [
        ('genero_especie_uniq',
         'unique(genero, especie)',
         'La combinación de género y especie debe ser única!')
    ]

    @api.depends('genero', 'especie')
    def _compute_scientific_name(self):
        for record in self:
            if record.genero:
                # Si hay especie y no es "indeterminado", concatenar. Si no, solo Género.
                if record.especie and record.especie.lower() not in ['indeterminado', 'sp', 'sp.']:
                    record.name = f"{record.genero} {record.especie}"
                else:
                    record.name = record.genero
            else:
                record.name = False

    @api.depends('specimen_ids')
    def _compute_total_specimens(self):
        for record in self:
            record.total_specimens = len(record.specimen_ids)

    @api.depends('image_ids')
    def _compute_total_images(self):
        for record in self:
            record.total_images = len(record.image_ids)

    @api.constrains('genero')
    def _check_genero_format(self):
        for record in self:
            if record.genero:
                if not record.genero[0].isupper():
                    raise ValidationError('El género debe comenzar con mayúscula')
                if not record.genero.replace(' ', '').isalpha():
                    raise ValidationError('El género solo debe contener letras')

    @api.constrains('especie')
    def _check_especie_format(self):
        for record in self:
            if record.especie:
                if not record.especie[0].islower():
                    raise ValidationError('La especie debe comenzar con minúscula')
                if not record.especie.replace(' ', '').isalpha():
                    raise ValidationError('La especie solo debe contener letras')

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.genero} {record.especie}"
            if record.family_id:
                name = f"{name} ({record.family_id.name})"
            result.append((record.id, name))
        return result

    def action_view_specimens(self):
        self.ensure_one()
        return {
            'name': 'Especímenes',
            'view_mode': 'tree,form',
            'res_model': 'herbario.specimen',
            'domain': [('taxon_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_taxon_id': self.id},
        }

    def action_view_images(self):
        self.ensure_one()
        return {
            'name': 'Imágenes',
            'view_mode': 'tree,form',
            'res_model': 'herbario.image',
            'domain': [('taxon_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_taxon_id': self.id},
        }
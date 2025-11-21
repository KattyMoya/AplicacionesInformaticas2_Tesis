from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    session_timeout_minutes = fields.Integer(
        string='Timeout de Sesión (minutos)',
        default=30,
        config_parameter='herbario.session_timeout_minutes',
        help='Tiempo de inactividad antes de cerrar sesión automáticamente'
    )
    
    password_expiry_days = fields.Integer(
        string='Expiración de Contraseña (días)',
        default=90,
        config_parameter='herbario.password_expiry_days',
        help='Días antes de forzar cambio de contraseña (0 = nunca)'
    )
    
    max_login_attempts = fields.Integer(
        string='Intentos Máximos de Login',
        default=5,
        config_parameter='herbario.max_login_attempts',
        help='Número de intentos fallidos antes de bloquear cuenta'
    )
    
    require_strong_password = fields.Boolean(
        string='Requerir Contraseñas Fuertes',
        default=True,
        config_parameter='herbario.require_strong_password',
        help='Validar fortaleza de contraseñas (8 chars, mayúsc, número, símbolo)'
    )
    
    require_institutional_email = fields.Boolean(
        string='Requerir Correo Institucional',
        default=True,
        config_parameter='herbario.require_institutional_email',
        help='Solo permitir correos @espoch.edu.ec'
    )
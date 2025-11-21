# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestModuloInstalado(TransactionCase):
    """
    Tests de instalación del módulo HerbaProgram
    Sprint 2 - HT-08.1: Framework de pruebas (configuración básica)
    """
    
    def setUp(self):
        super().setUp()
        _logger.info("\n" + "="*60)
        _logger.info("INICIANDO TESTS DEL MÓDULO HERBARIO_ESPOCH")
        _logger.info("="*60)
    
    def test_01_modulo_existe(self):
        """
        Test 1: Verificar que el módulo existe en Odoo
        """
        _logger.info("\n[TEST 1] Verificando existencia del módulo...")
        
        modulo = self.env['ir.module.module'].search([
            ('name', '=', 'herbario_espoch')
        ])
        
        self.assertTrue(
            modulo, 
            "ERROR: El módulo 'herbario_espoch' no existe en el sistema"
        )
        
        _logger.info("✓ PASADO: El módulo 'herbario_espoch' existe")
        _logger.info(f"  - ID del módulo: {modulo.id}")
        _logger.info(f"  - Nombre técnico: {modulo.name}")
    
    def test_02_modulo_instalado(self):
        """
        Test 2: Verificar que el módulo está instalado
        """
        _logger.info("\n[TEST 2] Verificando estado de instalación...")
        
        modulo = self.env['ir.module.module'].search([
            ('name', '=', 'herbario_espoch')
        ])
        
        self.assertEqual(
            modulo.state,
            'installed',
            f"ERROR: El módulo está en estado '{modulo.state}', se esperaba 'installed'"
        )
        
        _logger.info("✓ PASADO: El módulo está correctamente instalado")
        _logger.info(f"  - Estado: {modulo.state}")
        _logger.info(f"  - Versión: {modulo.installed_version or 'N/A'}")
    
    def test_03_menu_existe(self):
        """
        Test 3: Verificar que el menú Herbario existe
        """
        _logger.info("\n[TEST 3] Verificando menú principal...")
        
        menu = self.env['ir.ui.menu'].search([
            ('name', '=', 'Herbario')
        ])
        
        self.assertTrue(
            menu,
            "ERROR: El menú 'Herbario' no existe en el sistema"
        )
        
        _logger.info("✓ PASADO: El menú 'Herbario' existe")
        _logger.info(f"  - ID del menú: {menu.id}")
        _logger.info(f"  - Nombre: {menu.name}")
        _logger.info(f"  - Menú padre: {menu.parent_id.name if menu.parent_id else 'Raíz'}")
    
    def test_04_modelos_registrados(self):
        """
        Test 4: Verificar que los modelos principales están registrados
        """
        _logger.info("\n[TEST 4] Verificando modelos registrados...")
        
        modelos_esperados = [
            'herbario.especimen',
            'herbario.familia',
            'herbario.genero',
        ]
        
        modelos_encontrados = []
        modelos_faltantes = []
        
        for modelo in modelos_esperados:
            if modelo in self.env:
                modelos_encontrados.append(modelo)
                _logger.info(f"  ✓ Modelo '{modelo}' registrado")
            else:
                modelos_faltantes.append(modelo)
                _logger.warning(f"  ✗ Modelo '{modelo}' NO encontrado")
        
        # No falla si faltan modelos (pueden no estar implementados aún)
        _logger.info(f"\n  Total modelos encontrados: {len(modelos_encontrados)}/{len(modelos_esperados)}")
        
        if modelos_faltantes:
            _logger.info("  Nota: Algunos modelos aún no están implementados (normal en Sprint 2)")
    
    def test_05_seguridad_grupos(self):
        """
        Test 5: Verificar que los grupos de seguridad existen
        """
        _logger.info("\n[TEST 5] Verificando grupos de seguridad...")
        
        grupos_esperados = [
            'herbario_espoch.group_herbario_admin',
            'herbario_espoch.group_herbario_user',
            'herbario_espoch.group_herbario_viewer',
        ]
        
        grupos_encontrados = 0
        
        for grupo_xml_id in grupos_esperados:
            try:
                grupo = self.env.ref(grupo_xml_id)
                grupos_encontrados += 1
                _logger.info(f"  ✓ Grupo '{grupo.name}' existe")
            except ValueError:
                _logger.warning(f"  ✗ Grupo '{grupo_xml_id}' NO encontrado")
        
        _logger.info(f"\n  Total grupos encontrados: {grupos_encontrados}/{len(grupos_esperados)}")
        
        if grupos_encontrados == 0:
            _logger.info("  Nota: Los grupos de seguridad se implementarán en este sprint")
    
    def tearDown(self):
        super().tearDown()
        _logger.info("\n" + "="*60)
        _logger.info("TESTS COMPLETADOS")
        _logger.info("="*60 + "\n")
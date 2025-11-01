#!/usr/bin/env python
"""
Comando de verificación del sistema de cambio de planes.
Ejecutar con: python manage.py verificar_sistema
"""

import os
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.conf import settings


class Command(BaseCommand):
    help = "Verifica la configuración completa del sistema de cambio de planes"

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("VERIFICACIÓN DEL SISTEMA DE CAMBIO DE PLANES")
        self.stdout.write("=" * 80)
        self.stdout.write()

        # Importar modelos
        try:
            from usuarios.models import Usuario, SolicitudCambioPlan
            self.stdout.write(self.style.SUCCESS("✓ Modelos importados correctamente"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"✗ Error importando modelos: {e}"))
            return

        # Verificar URLs
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VERIFICACIÓN DE URLS")
        self.stdout.write("=" * 80)

        urls_requeridas = [
            ('usuarios:dashboard', '/usuarios/dashboard/'),
            ('usuarios:solicitar_cambio_plan', '/usuarios/solicitar-cambio-plan/'),
            ('usuarios:cancelar_solicitud_plan', '/usuarios/cancelar-solicitud-plan/'),
            ('usuarios:cambiar_plan_usuario', '/usuarios/api/cambiar-plan/'),
            ('usuarios:buscar_usuarios', '/usuarios/api/buscar/'),
            ('usuarios:gestionar_solicitudes', '/usuarios/gestionar-solicitudes/'),
        ]

        for url_name, expected_path in urls_requeridas:
            try:
                actual_path = reverse(url_name)
                if actual_path == expected_path:
                    self.stdout.write(self.style.SUCCESS(f"✓ {url_name:40} → {actual_path}"))
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠ {url_name:40} → {actual_path} (esperado: {expected_path})")
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ {url_name:40} → ERROR: {e}"))

        # Verificar usuarios gestores
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VERIFICACIÓN DE USUARIOS GESTORES")
        self.stdout.write("=" * 80)

        gestores = Usuario.objects.filter(tipo_usuario='gestor')
        if gestores.exists():
            self.stdout.write(self.style.SUCCESS(f"✓ Encontrados {gestores.count()} usuarios gestores:"))
            for gestor in gestores:
                self.stdout.write(f"  - {gestor.email} ({gestor.nombre_completo})")
        else:
            self.stdout.write(self.style.WARNING("⚠ No hay usuarios gestores configurados"))
            self.stdout.write("  Para crear uno, ejecuta en shell:")
            self.stdout.write("  >>> user = Usuario.objects.get(email='tu@email.com')")
            self.stdout.write("  >>> user.tipo_usuario = 'gestor'")
            self.stdout.write("  >>> user.save()")

        # Verificar usuarios regulares
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VERIFICACIÓN DE USUARIOS REGULARES")
        self.stdout.write("=" * 80)

        usuarios_total = Usuario.objects.filter(tipo_usuario='usuario').count()
        usuarios_pro = Usuario.objects.filter(tipo_usuario='usuario', plan='pro').count()
        usuarios_gratuitos = Usuario.objects.filter(tipo_usuario='usuario', plan='gratuito').count()

        self.stdout.write(f"Total de usuarios: {usuarios_total}")
        self.stdout.write(f"  - Plan Pro: {usuarios_pro}")
        self.stdout.write(f"  - Plan Gratuito: {usuarios_gratuitos}")

        if usuarios_total > 0:
            self.stdout.write("\nEjemplos de usuarios:")
            for usuario in Usuario.objects.filter(tipo_usuario='usuario')[:3]:
                plan_icon = "⭐" if usuario.es_pro() else "👤"
                self.stdout.write(f"  {plan_icon} {usuario.email} - {usuario.get_plan_display()}")

        # Verificar solicitudes
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VERIFICACIÓN DE SOLICITUDES DE CAMBIO DE PLAN")
        self.stdout.write("=" * 80)

        solicitudes_pendientes = SolicitudCambioPlan.objects.filter(estado='pendiente').count()
        solicitudes_procesadas = SolicitudCambioPlan.objects.filter(estado='procesada').count()
        solicitudes_canceladas = SolicitudCambioPlan.objects.filter(estado='cancelada').count()

        self.stdout.write(f"Solicitudes pendientes: {solicitudes_pendientes}")
        self.stdout.write(f"Solicitudes procesadas: {solicitudes_procesadas}")
        self.stdout.write(f"Solicitudes canceladas: {solicitudes_canceladas}")

        if solicitudes_pendientes > 0:
            self.stdout.write("\nSolicitudes pendientes actuales:")
            for sol in SolicitudCambioPlan.objects.filter(estado='pendiente'):
                tipo_icon = "⬆️" if sol.tipo_solicitud == 'solicitar_pro' else "⬇️"
                self.stdout.write(
                    f"  {tipo_icon} {sol.usuario.email} - {sol.get_tipo_solicitud_display()} "
                    f"({sol.dias_pendiente} días)"
                )

        # Verificar estructura de archivos
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VERIFICACIÓN DE ESTRUCTURA DE ARCHIVOS")
        self.stdout.write("=" * 80)

        templates_base = os.path.join(settings.BASE_DIR, 'templates', 'usuarios')
        archivos_requeridos = [
            'dashboard.html',
            'partials/lista_usuarios.html',
            'partials/user_card.html',
        ]

        for archivo in archivos_requeridos:
            ruta_completa = os.path.join(templates_base, archivo)
            if os.path.exists(ruta_completa):
                size_kb = os.path.getsize(ruta_completa) / 1024
                self.stdout.write(self.style.SUCCESS(f"✓ {archivo:35} ({size_kb:.1f} KB)"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ {archivo:35} NO ENCONTRADO"))

        # Verificar vistas
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("VERIFICACIÓN DE VISTAS")
        self.stdout.write("=" * 80)

        try:
            from usuarios import views
            vistas_requeridas = [
                'solicitar_cambio_plan_view',
                'cancelar_solicitud_plan_view',
                'cambiar_plan_usuario_view',
                'buscar_usuarios_view',
                'gestionar_solicitudes_view',
            ]

            for vista in vistas_requeridas:
                if hasattr(views, vista):
                    self.stdout.write(self.style.SUCCESS(f"✓ {vista}"))
                else:
                    self.stdout.write(self.style.ERROR(f"✗ {vista} NO ENCONTRADA"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"✗ Error importando vistas: {e}"))

        # Resumen final
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("RESUMEN")
        self.stdout.write("=" * 80)

        problemas = []

        if gestores.count() == 0:
            problemas.append("No hay usuarios gestores configurados")

        if usuarios_total == 0:
            problemas.append("No hay usuarios registrados")

        if solicitudes_pendientes > 10:
            problemas.append(f"Hay {solicitudes_pendientes} solicitudes pendientes acumuladas")

        if not os.path.exists(os.path.join(templates_base, 'dashboard.html')):
            problemas.append("Archivo dashboard.html no encontrado")

        if len(problemas) == 0:
            self.stdout.write(self.style.SUCCESS("✓ ¡Todo parece estar correcto!"))
            self.stdout.write("\nPróximos pasos:")
            self.stdout.write("1. Reiniciar el servidor Django")
            self.stdout.write("2. Limpiar cache del navegador")
            self.stdout.write("3. Hacer login como gestor")
            self.stdout.write("4. Probar cambio de plan de un usuario")
        else:
            self.stdout.write(self.style.WARNING(f"⚠ Se encontraron {len(problemas)} problema(s):"))
            for i, problema in enumerate(problemas, 1):
                self.stdout.write(f"  {i}. {problema}")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("FIN DE LA VERIFICACIÓN")
        self.stdout.write("=" * 80)
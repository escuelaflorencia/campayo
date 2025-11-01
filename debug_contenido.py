from ejercicios.models import CategoriaEjercicio, Ejercicio
from test_lectura.models import TestLectura
from usuarios.models import Usuario

print("=== DIAGNÓSTICO DE CONTENIDO ===")

# 1. Verificar datos básicos
categorias = CategoriaEjercicio.objects.filter(activa=True)
ejercicios = Ejercicio.objects.filter(activo=True)
tests = TestLectura.objects.filter(activo=True)
usuarios = Usuario.objects.filter(tipo_usuario='usuario')

print(f"\n1. DATOS EN BASE DE DATOS:")
print(f"   - Categorías activas: {categorias.count()}")
print(f"   - Ejercicios activos: {ejercicios.count()}")
print(f"   - Tests activos: {tests.count()}")
print(f"   - Usuarios normales: {usuarios.count()}")

if categorias.exists():
    print(f"\n   Categorías encontradas:")
    for cat in categorias:
        print(f"     - {cat.codigo}: {cat.nombre}")

# 2. Verificar ejercicios por nivel
print(f"\n2. EJERCICIOS POR NIVEL:")
for nivel in range(1, 6):
    ejs_nivel = ejercicios.filter(nivel=nivel)
    print(f"   - Nivel {nivel}: {ejs_nivel.count()} ejercicios")
    for ej in ejs_nivel[:2]:  # Primeros 2
        print(f"     * {ej.codigo} - Requiere Pro: {ej.requiere_pro}")

# 3. Verificar acceso de usuario
if usuarios.exists():
    usuario = usuarios.first()
    print(f"\n3. VERIFICACIÓN DE ACCESO (Usuario: {usuario.email}):")
    print(f"   - Plan: {usuario.plan}")
    print(f"   - Es Pro: {usuario.es_pro()}")
    print(f"   - Es Gestor: {usuario.es_gestor()}")
    
    for nivel in range(1, 6):
        print(f"   - Puede acceder nivel {nivel}: {usuario.puede_acceder_nivel(nivel)}")
    
    # Verificar ejercicios específicos
    print(f"\n   Ejercicios específicos:")
    for ej in ejercicios.filter(nivel__lte=3)[:3]:
        try:
            puede_acceder = ej.puede_acceder(usuario)
            requisitos = ej.get_requisitos_acceso(usuario) if not puede_acceder else []
            print(f"     - {ej.codigo}: {'✓' if puede_acceder else '✗'} {requisitos}")
        except Exception as e:
            print(f"     - {ej.codigo}: ERROR - {e}")

# 4. Verificar tests
print(f"\n4. TESTS DISPONIBLES:")
for test in tests[:3]:
    print(f"   - {test.nombre}: {test.titulo}")
    if usuarios.exists():
        try:
            puede, msg = test.puede_acceder(usuarios.first())
            print(f"     Acceso: {'✓' if puede else '✗'} {msg}")
        except Exception as e:
            print(f"     Error verificando acceso: {e}")

print(f"\n=== FIN DIAGNÓSTICO ===")
# ejercicios/views.py - VISTA ACTUALIZADA PARA LISTA DE EJERCICIOS

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
from collections import defaultdict
import random

from .models import Ejercicio, CategoriaEjercicio, BloquePrevio
from usuarios.models import Usuario, EjercicioRealizado, ProgresoTests


@login_required
def lista_ejercicios_view(request):
    """
    Vista principal que muestra ejercicios organizados por categorías.
    Cada categoría contiene ejercicios agrupados por código base con sus niveles.
    """
    usuario = request.user
    
    # Verificar si ha completado el test inicial
    test_inicial_completado = ProgresoTests.objects.filter(
        usuario=usuario,
        test_nombre='test_inicial',
        completado=True
    ).exists()
    
    # Obtener todas las categorías activas
    categorias = CategoriaEjercicio.objects.filter(activa=True).order_by('orden')
    
    # Obtener todos los ejercicios realizados por el usuario
    ejercicios_realizados = set(
        EjercicioRealizado.objects.filter(
            usuario=usuario,
            realizado=True
        ).values_list('ejercicio_codigo', flat=True)
    )
    
    categorias_ejercicios = []
    total_completados = 0
    total_disponibles = 0
    total_bloqueados = 0
    
    for categoria in categorias:
        # Obtener todos los ejercicios de esta categoría
        ejercicios = Ejercicio.objects.filter(
            categoria=categoria,
            activo=True
        ).order_by('nivel', 'orden_en_bloque')
        
        # Agrupar ejercicios por código base (sin el número de nivel)
        ejercicios_agrupados_dict = defaultdict(list)
        
        for ejercicio in ejercicios:
            # El código del ejercicio incluye el tipo (EL1, EL2, EO1, etc.)
            # Extraemos solo la parte alfabética + primer número (ej: EL1, EO2)
            # Cada código completo sin el nivel es el código base
            import re
            # Extraer la parte del código que identifica el ejercicio (sin el nivel)
            # Ejemplo: EL1_Nivel_1 -> EL1, EO2_Nivel_3 -> EO2
            codigo_base = ejercicio.codigo.split('_')[0] if '_' in ejercicio.codigo else ejercicio.codigo
            
            # Verificar acceso
            puede_acceder, requisitos = ejercicio.puede_acceder_con_detalles(usuario)
            completado = ejercicio.codigo in ejercicios_realizados
            
            # Contar estadísticas
            if completado:
                total_completados += 1
            elif puede_acceder:
                total_disponibles += 1
            else:
                total_bloqueados += 1
            
            ejercicios_agrupados_dict[codigo_base].append({
                'ejercicio': ejercicio,
                'puede_acceder': puede_acceder,
                'completado': completado,
                'requisitos': requisitos.split(', ') if requisitos else []
            })
        
        # Convertir a lista y añadir información adicional
        ejercicios_agrupados = []
        for codigo_base, niveles in ejercicios_agrupados_dict.items():
            # Ordenar niveles por nivel
            niveles_ordenados = sorted(niveles, key=lambda x: x['ejercicio'].nivel)
            
            # Contar completados
            completados_count = sum(1 for n in niveles_ordenados if n['completado'])
            
            # Obtener nombre del primer ejercicio (todos deberían tener el mismo nombre base)
            nombre = niveles_ordenados[0]['ejercicio'].nombre if niveles_ordenados else ''
            
            ejercicios_agrupados.append({
                'codigo_base': codigo_base,
                'nombre': nombre,
                'niveles': niveles_ordenados,
                'completados': completados_count,
                'total': len(niveles_ordenados)
            })
        
        # Ordenar por código base
        ejercicios_agrupados.sort(key=lambda x: x['codigo_base'])
        
        # Contar completados en esta categoría
        completados_categoria = sum(1 for ej in ejercicios if ej.codigo in ejercicios_realizados)
        
        categorias_ejercicios.append({
            'categoria': categoria,
            'ejercicios_agrupados': ejercicios_agrupados,
            'completados': completados_categoria,
            'total': ejercicios.count()
        })
    
    context = {
        'categorias_ejercicios': categorias_ejercicios,
        'test_inicial_completado': test_inicial_completado,
        'total_completados': total_completados,
        'total_disponibles': total_disponibles,
        'total_bloqueados': total_bloqueados,
        'usuario': usuario
    }
    
    return render(request, 'ejercicios/lista.html', context)


@login_required
def detalle_ejercicio_view(request, ejercicio_id):
    """
    Vista para ejercicio individual.
    """
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id, activo=True)
    usuario = request.user
    
    # Verificar acceso
    puede_acceder, mensaje_error = ejercicio.puede_acceder_con_detalles(usuario)
    if not puede_acceder:
        messages.error(request, f"No puedes acceder a este ejercicio: {mensaje_error}")
        return redirect('ejercicios:lista')
    
    # Configuración del ejercicio
    configuracion_json = json.dumps(ejercicio.configuracion)
    
    # Preparar tests disponibles para ejercicios de lectura (EL5-EL8)
    available_tests_json = '[]'
    if ejercicio.codigo and any(x in ejercicio.codigo for x in ['EL5', 'EL6', 'EL7', 'EL8']):
        available_tests = _get_available_tests_for_exercises()
        available_tests_json = json.dumps(available_tests)
    
    context = {
        'ejercicio': ejercicio,
        'configuracion': configuracion_json,
        'available_tests': available_tests_json,
        'usuario': usuario
    }
    
    return render(request, 'ejercicios/ejercicio_base.html', context)


@login_required
@require_POST
def completar_ejercicio_view(request):
    """
    Vista AJAX para marcar un ejercicio como completado.
    """
    ejercicio_id = request.POST.get('ejercicio_id')
    tiempo_ms = request.POST.get('tiempo_ms', '0')
    
    try:
        ejercicio = Ejercicio.objects.get(id=ejercicio_id, activo=True)
        usuario = request.user
        
        # Verificar acceso
        puede_acceder, mensaje_error = ejercicio.puede_acceder_con_detalles(usuario)
        if not puede_acceder:
            return JsonResponse({
                'success': False,
                'error': f'No puedes realizar este ejercicio: {mensaje_error}'
            })
        
        # Marcar como realizado
        ejercicio_realizado, created = EjercicioRealizado.objects.get_or_create(
            usuario=usuario,
            ejercicio_codigo=ejercicio.codigo,
            defaults={'realizado': True}
        )
        
        if not created:
            ejercicio_realizado.fecha_realizacion = timezone.now()
            ejercicio_realizado.save()
        
        # Verificar desbloqueos
        mensaje_desbloqueado = _verificar_desbloqueos(usuario, ejercicio)
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Ejercicio {ejercicio.codigo} completado',
            'desbloqueado': mensaje_desbloqueado
        })
        
    except Ejercicio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ejercicio no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mi_progreso_view(request):
    """
    Vista para mostrar el progreso del usuario en ejercicios.
    """
    usuario = request.user
    
    # Ejercicios realizados
    ejercicios_realizados = EjercicioRealizado.objects.filter(
        usuario=usuario,
        realizado=True
    ).order_by('-fecha_realizacion')
    
    # Estadísticas por categoría
    categorias = CategoriaEjercicio.objects.filter(activa=True).order_by('orden')
    progreso_por_categoria = {}
    
    for categoria in categorias:
        ejercicios_categoria = Ejercicio.objects.filter(
            categoria=categoria,
            activo=True
        )
        
        total_ejercicios = ejercicios_categoria.count()
        realizados = ejercicios_realizados.filter(
            ejercicio_codigo__startswith=categoria.codigo
        ).count()
        
        progreso_por_categoria[categoria.codigo] = {
            'categoria': categoria,
            'total': total_ejercicios,
            'realizados': realizados,
            'porcentaje': round((realizados / total_ejercicios * 100), 1) if total_ejercicios > 0 else 0
        }
    
    # Progreso por bloques
    progreso_bloques = {}
    for bloque in [1, 2, 3]:
        ejercicios_bloque = Ejercicio.objects.filter(bloque=bloque, activo=True)
        total_bloque = ejercicios_bloque.count()
        
        realizados_bloque = 0
        for ejercicio in ejercicios_bloque:
            if EjercicioRealizado.objects.filter(
                usuario=usuario,
                ejercicio_codigo=ejercicio.codigo,
                realizado=True
            ).exists():
                realizados_bloque += 1
        
        progreso_bloques[bloque] = {
            'total': total_bloque,
            'realizados': realizados_bloque,
            'completado': realizados_bloque >= total_bloque,
            'porcentaje': round((realizados_bloque / total_bloque * 100), 1) if total_bloque > 0 else 0
        }
    
    context = {
        'ejercicios_realizados': ejercicios_realizados[:10],
        'progreso_por_categoria': progreso_por_categoria,
        'progreso_bloques': progreso_bloques,
        'total_ejercicios_realizados': ejercicios_realizados.count(),
        'usuario': usuario
    }
    
    return render(request, 'ejercicios/mi_progreso.html', context)


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _get_available_tests_for_exercises():
    """
    Obtiene tests de lectura disponibles para ejercicios EL5-EL8.
    Versión mejorada que proporciona más variedad de textos.
    """
    try:
        from test_lectura.models import TestLectura
        
        # Obtener tests activos con suficiente contenido
        tests = TestLectura.objects.filter(
            activo=True,
            numero_palabras__gte=300  # Reducir el mínimo para más variedad
        ).order_by('?')[:15]  # Seleccionar hasta 15 tests aleatorios
        
        available_tests = []
        
        # Textos por defecto mejorados
        default_texts = [
            {
                'name': 'Lectura Rápida Campayo',
                'text_content': '''La técnica de lectura rápida desarrollada por Ramón Campayo ha revolucionado la forma en que miles de personas procesan información escrita. Este método se basa en principios científicos que permiten incrementar la velocidad de lectura sin sacrificar la comprensión.

El entrenamiento visual es fundamental para desarrollar esta habilidad. Los ojos deben aprender a realizar movimientos más eficientes, reduciendo las fijaciones y ampliando el campo de visión periférica. La práctica constante de ejercicios específicos fortalece estos músculos oculares.

La concentración mental juega un papel crucial en el proceso. Cuando la mente está relajada pero alerta, el cerebro puede procesar información a velocidades sorprendentes. Las técnicas de relajación y meditación complementan perfectamente el entrenamiento técnico.

Los resultados obtenidos por los estudiantes del método Campayo son extraordinarios. Muchos han logrado multiplicar por cinco o diez su velocidad de lectura inicial, manteniendo e incluso mejorando su nivel de comprensión. Esto se traduce en ventajas significativas tanto en el ámbito académico como profesional.''',
                'word_count': 167
            },
            {
                'name': 'Neuroplasticidad y Aprendizaje',
                'text_content': '''El cerebro humano posee una capacidad extraordinaria para adaptarse y reorganizarse. Esta propiedad, conocida como neuroplasticidad, permite que las conexiones neuronales se modifiquen y fortalezcan a través del entrenamiento y la práctica deliberada.

La lectura rápida aprovecha esta neuroplasticidad para crear nuevas rutas neuronales más eficientes. Cuando practicamos ejercicios de velocidad de lectura, estamos literalmente reentrenando nuestro cerebro para procesar información visual de manera más efectiva.

Los estudios en neurociencia han demostrado que el entrenamiento visual intensivo puede modificar la estructura y función de áreas cerebrales específicas. Las regiones responsables del procesamiento visual y la comprensión lectora se vuelven más activas y coordinadas.

Este proceso de reorganización neural no tiene límites de edad. Tanto jóvenes como adultos pueden beneficiarse del entrenamiento en lectura rápida, desarrollando habilidades que permanecerán activas durante toda la vida. La clave está en la consistencia y la práctica regular.''',
                'word_count': 162
            },
            {
                'name': 'Tecnología y Educación',
                'text_content': '''La integración de la tecnología en los procesos educativos ha transformado radicalmente la manera en que adquirimos y procesamos conocimientos. Las herramientas digitales ofrecen posibilidades antes impensables para personalizar el aprendizaje según las necesidades individuales de cada estudiante.

Los dispositivos móviles y las aplicaciones especializadas permiten llevar el entrenamiento de lectura rápida a cualquier lugar. Esta flexibilidad facilita la práctica regular, elemento esencial para el desarrollo de habilidades de velocidad lectora. La gamificación convierte el aprendizaje en una experiencia más atractiva y motivadora.

Las plataformas online pueden adaptar automáticamente el nivel de dificultad según el progreso del usuario. Los algoritmos de inteligencia artificial analizan el rendimiento en tiempo real y sugieren ejercicios específicos para mejorar áreas débiles. Esta personalización optimiza significativamente los resultados del entrenamiento.

La realidad virtual y aumentada abren nuevas fronteras en el entrenamiento visual. Estas tecnologías permiten crear entornos tridimensionales donde los ojos pueden practicar movimientos y patrones de lectura en espacios virtuales, expandiendo las posibilidades tradicionales del entrenamiento en papel.''',
                'word_count': 185
            },
            {
                'name': 'Memoria y Comprensión',
                'text_content': '''La relación entre velocidad de lectura y comprensión es uno de los aspectos más fascinantes del método Campayo. Contrariamente a la creencia popular, aumentar la velocidad de lectura puede mejorar la comprensión y retención de información.

Cuando leemos lentamente, la mente tiende a divagar y perder concentración. El cerebro procesa información mucho más rápido de lo que generalmente leemos, creando espacios vacíos que se llenan con pensamientos irrelevantes. La lectura rápida mantiene la mente ocupada y enfocada.

Las técnicas de memorización se complementan perfectamente con la lectura acelerada. Los mapas mentales, las asociaciones visuales y los métodos mnemotécnicos permiten organizar y retener grandes cantidades de información procesada a alta velocidad.

La práctica regular desarrolla una forma de lectura más activa e interactiva. El lector rápido no solo consume información pasivamente, sino que la analiza, relaciona y organiza mentalmente mientras lee. Este proceso activo mejora significativamente la comprensión y el aprendizaje.''',
                'word_count': 158
            }
        ]
        
        # Agregar tests de la base de datos si están disponibles
        for test in tests:
            if hasattr(test, 'texto_contenido') and test.texto_contenido:
                content = test.texto_contenido.strip()
                if len(content) > 100:  # Asegurar contenido mínimo
                    available_tests.append({
                        'name': test.titulo or test.nombre or f'Test {test.id}',
                        'text_content': content,
                        'word_count': test.numero_palabras or len(content.split())
                    })
        
        # Si no hay suficientes tests de la base de datos, usar los textos por defecto
        if len(available_tests) < 6:
            available_tests.extend(default_texts)
        
        # Mezclar para mayor variedad
        random.shuffle(available_tests)
        
        # Limitar a 20 tests máximo para no sobrecargar
        return available_tests[:20]
        
    except ImportError:
        # Si el módulo test_lectura no existe, usar textos por defecto
        default_texts = [
            {
                'name': 'Técnicas de Estudio',
                'text_content': '''Las técnicas de estudio eficaces son fundamentales para el éxito académico y profesional. La organización del tiempo, la creación de mapas conceptuales y la práctica de la lectura activa son herramientas poderosas que pueden transformar completamente la experiencia de aprendizaje.

La lectura rápida se convierte en una habilidad esencial cuando se combina con estas técnicas. Permite procesar grandes volúmenes de información en tiempo reducido, liberando horas valiosas para la reflexión y la práctica. Los estudiantes que dominan estas habilidades obtienen ventajas competitivas significativas.

El ambiente de estudio también influye en el rendimiento. Un espacio bien iluminado, libre de distracciones y ergonómicamente diseñado facilita la concentración prolongada. La música instrumental suave puede mejorar el enfoque en algunas personas, mientras que otras prefieren el silencio absoluto.

La revisión espaciada es otra técnica comprobada científicamente. Repasar el material en intervalos crecientes fortalece la memoria a largo plazo y mejora la retención. Esta técnica se complementa perfectamente con la lectura rápida para optimizar el tiempo de estudio.''',
                'word_count': 178
            },
            {
                'name': 'Desarrollo Personal',
                'text_content': '''El crecimiento personal es un viaje continuo que requiere dedicación, autoconocimiento y la voluntad de salir de la zona de confort. Cada día presenta oportunidades para aprender algo nuevo, desarrollar habilidades y fortalecer el carácter personal.

La lectura regular es una de las inversiones más valiosas que podemos hacer en nosotros mismos. Los libros nos exponen a nuevas ideas, perspectivas y experiencias que amplían nuestra comprensión del mundo. La lectura rápida multiplica exponencialmente esta exposición al conocimiento.

Los hábitos positivos son los cimientos del desarrollo personal sostenible. Pequeñas acciones consistentes, repetidas día tras día, crean transformaciones profundas a largo plazo. El entrenamiento en lectura rápida es un ejemplo perfecto de cómo la práctica deliberada conduce a la maestría.

La mentalidad de crecimiento versus la mentalidad fija determina en gran medida nuestro potencial de desarrollo. Quienes creen que las habilidades pueden desarrollarse a través del esfuerzo y la práctica logran resultados superiores a quienes consideran que las capacidades son inmutables.''',
                'word_count': 171
            }
        ]
        return default_texts
        
    except Exception as e:
        print(f"Error al obtener tests de lectura: {e}")
        # Texto por defecto básico en caso de error
        return [{
            'name': 'Ejercicio de Lectura',
            'text_content': '''La práctica constante es la clave del éxito en cualquier disciplina. Los ejercicios de lectura rápida requieren dedicación y paciencia para desarrollar las habilidades visuales necesarias.

El cerebro humano tiene una capacidad extraordinaria para adaptarse y mejorar con el entrenamiento adecuado. Cada sesión de práctica fortalece las conexiones neuronales y mejora la eficiencia del procesamiento visual.

Los resultados del entrenamiento en lectura rápida son acumulativos. Lo que al principio puede parecer difícil se vuelve natural con la práctica regular. La persistencia y la consistencia son más importantes que la intensidad del entrenamiento.''',
            'word_count': 98
        }]


def _verificar_desbloqueos(usuario, ejercicio_completado):
    """
    Verifica si al completar un ejercicio se desbloquea contenido nuevo.
    """
    bloque = ejercicio_completado.bloque
    
    if usuario.bloque_completado(bloque):
        if bloque == 1:
            test_1_existe = ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_1',
                completado=True
            ).exists()
            
            if not test_1_existe and usuario.es_pro():
                return "Se ha desbloqueado el Test de Lectura 1"
        
        elif bloque == 2:
            test_2_existe = ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_2',
                completado=True
            ).exists()
            
            if not test_2_existe and usuario.es_pro():
                return "Se ha desbloqueado el Test de Lectura 2"
        
        return f"Has completado el bloque {bloque}"
    
    return None
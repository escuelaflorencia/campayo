# test_lectura/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction, models
import json
from django.urls import reverse
from datetime import timedelta

from .models import TestLectura, PreguntaTest, OpcionRespuesta, SesionTest, RespuestaUsuario
from usuarios.models import Usuario, ProgresoTests


@login_required
def lista_tests_view(request):
    """
    Vista principal para mostrar todos los tests disponibles.
    """
    usuario = request.user
    
    # Obtener tests accesibles para el usuario
    tests_disponibles = []
    tests = TestLectura.objects.filter(activo=True).order_by('numero_test')
    
    for test in tests:
        puede_acceder, mensaje_error = test.puede_acceder(usuario)
        
        # Verificar si ya lo ha completado
        ya_completado = SesionTest.objects.filter(
            usuario=usuario,
            test=test,
            completado=True
        ).exists()
        
        # Obtener mejor resultado si existe
        mejor_resultado = None
        if ya_completado:
            mejor_sesion = SesionTest.objects.filter(
                usuario=usuario,
                test=test,
                completado=True
            ).order_by('-velocidad_lectura').first()
            
            if mejor_sesion:
                mejor_resultado = {
                    'velocidad_lectura': mejor_sesion.velocidad_lectura,
                    'velocidad_memorizacion': mejor_sesion.velocidad_memorizacion,
                    'respuestas_correctas': mejor_sesion.respuestas_correctas,
                    'fecha': mejor_sesion.fecha_fin,
                    'sesion_id': mejor_sesion.id
                }
        
        tests_disponibles.append({
            'test': test,
            'puede_acceder': puede_acceder and not ya_completado,  # No puede repetir
            'mensaje_error': mensaje_error if not puede_acceder else ('Ya completado' if ya_completado else ''),
            'ya_completado': ya_completado,
            'mejor_resultado': mejor_resultado
        })
    
    # Estadísticas globales
    sesiones_completadas = SesionTest.objects.filter(
        usuario=usuario,
        completado=True
    )
    
    total_tests = sesiones_completadas.count()
    mejor_velocidad = sesiones_completadas.aggregate(
        models.Max('velocidad_lectura')
    )['velocidad_lectura__max'] or 0
    mejor_vm = sesiones_completadas.aggregate(
        models.Max('velocidad_memorizacion')
    )['velocidad_memorizacion__max'] or 0
    
    # Promedio de comprensión
    if total_tests > 0:
        promedio_comprension = sesiones_completadas.aggregate(
            models.Avg('respuestas_correctas')
        )['respuestas_correctas__avg']
        promedio_comprension = round((promedio_comprension / 20) * 100, 1)
    else:
        promedio_comprension = 0
    
    # Evolución por test
    evolucion_por_test = {}
    for test in tests:
        intentos = SesionTest.objects.filter(
            usuario=usuario,
            test=test,
            completado=True
        ).order_by('-fecha_fin')
        
        if intentos.exists():
            evolucion_por_test[test.nombre] = {
                'test': test,
                'intentos': intentos
            }
    
    context = {
        'tests_disponibles': tests_disponibles,
        'usuario': usuario,
        'total_tests': total_tests,
        'mejor_velocidad': mejor_velocidad,
        'mejor_vm': mejor_vm,
        'promedio_comprension': promedio_comprension,
        'evolucion_por_test': evolucion_por_test
    }
    
    return render(request, 'test_lectura/lista.html', context)


@login_required
def iniciar_test_view(request, test_id):
    """
    Vista para iniciar un test de lectura.
    """
    test = get_object_or_404(TestLectura, id=test_id, activo=True)
    usuario = request.user
    
    # Verificar si ya completó el test
    ya_completado = SesionTest.objects.filter(
        usuario=usuario,
        test=test,
        completado=True
    ).exists()
    
    if ya_completado:
        messages.warning(request, 'Ya has completado este test. Solo puedes hacerlo una vez.')
        return redirect('test_lectura:lista_tests')
    
    # Verificar acceso
    puede_acceder, mensaje_error = test.puede_acceder(usuario)
    if not puede_acceder:
        messages.error(request, mensaje_error)
        return redirect('test_lectura:lista_tests')
    
    # Verificar password si es necesario
    if test.requiere_password and request.method == 'GET':
        return render(request, 'test_lectura/solicitar_password.html', {'test': test})
    
    if test.requiere_password and request.method == 'POST':
        password_ingresado = request.POST.get('password', '')
        puede_acceder, mensaje_error = test.puede_acceder(usuario, password_ingresado)
        if not puede_acceder:
            messages.error(request, mensaje_error)
            return render(request, 'test_lectura/solicitar_password.html', {'test': test})
    
    # Buscar sesión existente no completada
    sesion = SesionTest.objects.filter(
        usuario=usuario,
        test=test,
        completado=False
    ).first()
    
    # Si no existe, crear nueva sesión
    if not sesion:
        sesion = SesionTest.objects.create(
            usuario=usuario,
            test=test,
            fecha_inicio=timezone.now()
        )
    
    # Determinar fase
    if sesion.tiempo_lectura:
        # Ya leyó, mostrar preguntas
        preguntas = PreguntaTest.objects.filter(test=test).prefetch_related('opciones')
        context = {
            'test': test,
            'sesion': sesion,
            'preguntas': preguntas,
            'fase': 'preguntas'
        }
    else:
        # Fase de lectura
        context = {
            'test': test,
            'sesion': sesion,
            'fase': 'lectura'
        }
    
    return render(request, 'test_lectura/realizar_test.html', context)


@login_required
@require_POST
def finalizar_lectura_view(request):
    """
    Vista AJAX para finalizar la fase de lectura y pasar a las preguntas.
    """
    sesion_id = request.POST.get('sesion_id')
    tiempo_lectura_ms = request.POST.get('tiempo_lectura_ms')
    
    try:
        sesion = SesionTest.objects.get(id=sesion_id, usuario=request.user)
        
        # Guardar tiempo de lectura
        tiempo_lectura = timedelta(milliseconds=int(tiempo_lectura_ms))
        sesion.tiempo_lectura = tiempo_lectura
        sesion.save()
        
        # Obtener preguntas del test
        preguntas = list(PreguntaTest.objects.filter(test=sesion.test).prefetch_related('opciones'))
        
        # Preparar datos de preguntas para JSON
        preguntas_data = []
        for pregunta in preguntas:
            opciones_data = []
            for opcion in pregunta.opciones.all():
                opciones_data.append({
                    'id': opcion.id,
                    'texto': opcion.texto
                })
            
            preguntas_data.append({
                'id': pregunta.id,
                'pregunta': pregunta.pregunta,
                'opciones': opciones_data
            })
        
        return JsonResponse({
            'success': True,
            'preguntas': preguntas_data,
            'total_preguntas': len(preguntas_data)
        })
        
    except SesionTest.DoesNotExist:
        return JsonResponse({'error': 'Sesión no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def finalizar_test_view(request):
    """
    Vista AJAX para finalizar el test completo y guardar respuestas.
    """
    sesion_id = request.POST.get('sesion_id')
    respuestas_json = request.POST.get('respuestas')
    
    try:
        with transaction.atomic():
            sesion = SesionTest.objects.get(id=sesion_id, usuario=request.user)
            respuestas = json.loads(respuestas_json)
            
            # Guardar respuestas
            respuestas_correctas = 0
            total_preguntas = len(respuestas)
            
            for pregunta_id, opcion_id in respuestas.items():
                pregunta = PreguntaTest.objects.get(id=pregunta_id)
                opcion = OpcionRespuesta.objects.get(id=opcion_id)
                
                # Crear respuesta del usuario
                RespuestaUsuario.objects.create(
                    sesion=sesion,
                    pregunta=pregunta,
                    opcion_seleccionada=opcion
                )
                
                if opcion.es_correcta:
                    respuestas_correctas += 1
            
            # Actualizar sesión con resultados
            sesion.respuestas_correctas = respuestas_correctas
            sesion.total_preguntas = total_preguntas
            sesion.fecha_fin = timezone.now()
            sesion.completado = True
            
            # Calcular velocidades
            sesion.calcular_velocidades()
            
            # Finalizar sesión (esto actualiza automáticamente ProgresoTests)
            sesion.finalizar_sesion()
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('test_lectura:resultado', kwargs={'sesion_id': sesion.id})  # ✅ Uso de reverse
            })
            
    except SesionTest.DoesNotExist:
        return JsonResponse({'error': 'Sesión no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def resultado_test_view(request, sesion_id):
    """
    Vista para mostrar los resultados detallados de un test.
    """
    sesion = get_object_or_404(
        SesionTest, 
        id=sesion_id, 
        usuario=request.user, 
        completado=True
    )
    
    # Obtener respuestas del usuario
    respuestas = RespuestaUsuario.objects.filter(sesion=sesion).select_related(
        'pregunta', 'opcion_seleccionada'
    )
    
    # Preparar datos de respuestas
    respuestas_detalle = []
    for idx, respuesta in enumerate(respuestas, 1):
        # Obtener todas las opciones de la pregunta
        opciones_pregunta = []
        for opcion in respuesta.pregunta.opciones.all():
            opciones_pregunta.append({
                'letra': chr(64 + opcion.orden + 1),  # A, B, C, D
                'texto': opcion.texto,
                'es_correcta': opcion.es_correcta,
                'fue_seleccionada': opcion.id == respuesta.opcion_seleccionada.id
            })
        
        respuestas_detalle.append({
            'pregunta_numero': idx,
            'pregunta_texto': respuesta.pregunta.pregunta,
            'opciones': opciones_pregunta,
            'es_correcta': respuesta.es_correcta
        })
    
    # Calcular estadísticas
    porcentaje_aciertos = round((sesion.respuestas_correctas / sesion.total_preguntas * 100), 1)
    
    # Evaluaciones
    evaluaciones = _generar_evaluaciones(sesion)
    
    context = {
        'sesion': sesion,
        'respuestas_detalle': respuestas_detalle,
        'comprension_porcentaje': porcentaje_aciertos,
        'respuestas_correctas': sesion.respuestas_correctas,
        'total_preguntas': sesion.total_preguntas,
        'velocidad_lectura': sesion.velocidad_lectura,
        'velocidad_memorizacion': sesion.velocidad_memorizacion,
        'tiempo_lectura_formateado': _formatear_tiempo(sesion.tiempo_lectura),
        'evaluacion_velocidad': evaluaciones['velocidad'],
        'evaluacion_vm': evaluaciones['vm'],
        'evaluacion_comprension': evaluaciones['comprension'],
        'mensaje_motivacional': evaluaciones['mensaje']
    }
    
    return render(request, 'test_lectura/resultado.html', context)


def _formatear_tiempo(duracion):
    """Formatea un timedelta a formato legible"""
    if not duracion:
        return "N/A"
    total_segundos = int(duracion.total_seconds())
    minutos = total_segundos // 60
    segundos = total_segundos % 60
    return f"{minutos}:{segundos:02d}"


def _generar_evaluaciones(sesion):
    """Genera evaluaciones personalizadas según resultados"""
    v = sesion.velocidad_lectura
    vm = sesion.velocidad_memorizacion
    comprension = (sesion.respuestas_correctas / sesion.total_preguntas) * 100
    
    # Evaluación velocidad
    if v < 200:
        eval_v = {
            'nivel': 'Lento',
            'descripcion': 'Tu velocidad de lectura está por debajo del promedio. Con práctica constante usando los ejercicios del método Campayo, mejorarás significativamente.'
        }
    elif v < 400:
        eval_v = {
            'nivel': 'Promedio',
            'descripcion': 'Tienes una velocidad de lectura normal. Los ejercicios de entrenamiento te ayudarán a duplicar o triplicar esta velocidad.'
        }
    elif v < 700:
        eval_v = {
            'nivel': 'Rápido',
            'descripcion': '¡Excelente! Lees más rápido que el promedio. Continúa practicando para alcanzar la lectura fotográfica.'
        }
    else:
        eval_v = {
            'nivel': 'Avanzado',
            'descripcion': '¡Impresionante! Estás en el camino hacia la lectura fotográfica. Sigue entrenando para perfeccionar tu técnica.'
        }
    
    # Evaluación Vm
    if vm < v * 0.5:
        eval_vm = {
            'nivel': 'Mejorable',
            'descripcion': 'Tu comprensión puede mejorar. Enfócate en entender lo que lees en lugar de solo ver las palabras.'
        }
    elif vm < v * 0.7:
        eval_vm = {
            'nivel': 'Bueno',
            'descripcion': 'Buen balance entre velocidad y comprensión. Continúa practicando para aumentar ambas.'
        }
    else:
        eval_vm = {
            'nivel': 'Excelente',
            'descripcion': '¡Perfecto! Mantienes excelente comprensión a alta velocidad. Este es el objetivo del método Campayo.'
        }
    
    # Evaluación comprensión
    if comprension < 60:
        eval_comp = {
            'nivel': 'Bajo',
            'descripcion': 'Menos del 60% de comprensión. Intenta leer más despacio y enfócate en entender el contenido.'
        }
    elif comprension < 75:
        eval_comp = {
            'nivel': 'Aceptable',
            'descripcion': 'Comprensión aceptable. Con práctica podrás mantener esta comprensión a mayor velocidad.'
        }
    else:
        eval_comp = {
            'nivel': 'Excelente',
            'descripcion': '¡Muy bien! Excelente nivel de comprensión. Este es el nivel que debes mantener.'
        }
    
    # Mensaje motivacional
    if v >= 700 and comprension >= 75:
        mensaje = '¡Extraordinario! Estás dominando el método Campayo. Sigue así.'
    elif v >= 400 and comprension >= 70:
        mensaje = '¡Muy bien! Estás progresando excelentemente. Continúa con los ejercicios.'
    elif v < 300 and comprension < 60:
        mensaje = 'No te desanimes. La práctica diaria con los ejercicios te llevará al siguiente nivel.'
    else:
        mensaje = 'Buen trabajo. Sigue practicando los ejercicios para mejorar cada día.'
    
    return {
        'velocidad': eval_v,
        'vm': eval_vm,
        'comprension': eval_comp,
        'mensaje': mensaje
    }
# management/commands/preparar_datos.py
import json
import os
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from ejercicios.models import CategoriaEjercicio, Ejercicio, BloquePrevio
from test_lectura.models import TestLectura, PreguntaTest, OpcionRespuesta


class Command(BaseCommand):
    help = 'Carga los datos del método Campayo según el libro original'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de datos del método Campayo...'))
        
        # Crear categorías de ejercicios
        self._create_exercise_categories()
        
        # Crear ejercicios según el método Campayo
        self._create_campayo_exercises()
        
        # Crear bloques previos (requisitos)
        self._create_block_requirements()
        
        # Cargar tests de lectura
        self._load_reading_tests()
        
        self.stdout.write(self.style.SUCCESS('¡Datos del método Campayo cargados exitosamente!'))
    
    def _create_exercise_categories(self):
        """Crear las categorías de ejercicios según Campayo"""
        self.stdout.write('Creando categorías de ejercicios...')
        
        categories_data = [
            {
                'codigo': 'EL',
                'nombre': 'Entrenamiento de Lectura',
                'descripcion': 'Ejercicios para mejorar la velocidad y fluidez de lectura mediante reconocimiento de dígitos, sílabas, palabras y lectura guiada.',
                'orden': 1
            },
            {
                'codigo': 'EO',
                'nombre': 'Entrenamiento del Ojo', 
                'descripcion': 'Ejercicios para desarrollar agilidad y precisión ocular mediante seguimiento visual.',
                'orden': 2
            },
            {
                'codigo': 'EPM',
                'nombre': 'Entrenamiento de Procesamiento Mental',
                'descripcion': 'Ejercicios para mejorar la velocidad de procesamiento mental mediante verificación gramatical.',
                'orden': 3
            },
            {
                'codigo': 'EVM',
                'nombre': 'Entrenamiento de Velocidad de Memorización',
                'descripcion': 'Ejercicios para mejorar la velocidad de memorización con secuencias de elementos.',
                'orden': 4
            },
            {
                'codigo': 'EMD',
                'nombre': 'Entrenamiento de Memoria Eidética',
                'descripcion': 'Ejercicios para desarrollar la memoria fotográfica mediante visualización de números.',
                'orden': 5
            }
        ]
        
        for cat_data in categories_data:
            categoria, created = CategoriaEjercicio.objects.get_or_create(
                codigo=cat_data['codigo'],
                defaults=cat_data
            )
            action = "creada" if created else "ya existe"
            self.stdout.write(f'  - Categoría {cat_data["codigo"]} {action}')
    
    def _create_campayo_exercises(self):
        """Crear ejercicios exactos según el método Campayo"""
        self.stdout.write('Creando ejercicios del método Campayo...')
        
        # Definición exacta de ejercicios según el libro
        campayo_exercises = {
            # BLOQUE 1 (Niveles 1-3)
            'EL': [
                {
                    'codigo_base': 'EL1',
                    'nombre': 'Reconocimiento de pares de dígitos',
                    'descripcion': 'Visualiza y pronuncia pares de dígitos separados para formar números.',
                    'instrucciones': 'Observa los dos dígitos que aparecen separados y pronuncia el número resultante en voz alta. Ejemplo: "6 7" = "sesenta y siete". Trata de ver ambos dígitos simultáneamente.',
                    'configuracion_base': {
                        'tipo_contenido': 'digitos',
                        'elementos_por_pantalla': 2,
                        'espaciado': 3,
                        'tiempo_display': 1000
                    }
                },
                {
                    'codigo_base': 'EL2', 
                    'nombre': 'Reconocimiento de sílabas',
                    'descripcion': 'Visualiza y pronuncia sílabas formadas por pares de letras.',
                    'instrucciones': 'Observa las dos letras que aparecen separadas y pronuncia la sílaba resultante en voz alta. Ejemplo: "P E" = "pe". Trata de ver ambas letras simultáneamente.',
                    'configuracion_base': {
                        'tipo_contenido': 'silabas',
                        'elementos_por_pantalla': 2,
                        'espaciado': 3,
                        'tiempo_display': 1200
                    }
                },
                {
                    'codigo_base': 'EL3',
                    'nombre': 'Lectura de 2 palabras',
                    'descripcion': 'Lee frases simples compuestas por 2 palabras.',
                    'instrucciones': 'Lee las frases de 2 palabras que aparecen en pantalla. Mantén un campo de visión amplio para captar ambas palabras simultáneamente.',
                    'configuracion_base': {
                        'tipo_contenido': 'frases_2_palabras',
                        'elementos_por_pantalla': 2,
                        'columnas': 1,
                        'tiempo_display': 1500
                    }
                },
                {
                    'codigo_base': 'EL4',
                    'nombre': 'Lectura de 3 palabras', 
                    'descripcion': 'Lee frases compuestas por 3 palabras.',
                    'instrucciones': 'Lee las frases de 3 palabras que aparecen en pantalla. Amplía tu campo de visión periférica para abarcar toda la frase.',
                    'configuracion_base': {
                        'tipo_contenido': 'frases_3_palabras',
                        'elementos_por_pantalla': 3,
                        'columnas': 1,
                        'tiempo_display': 1800
                    }
                },
                {
                    'codigo_base': 'EL5',
                    'nombre': 'Lectura en columnas',
                    'descripcion': 'Lee columnas con múltiples frases para ampliar el campo visual.',
                    'instrucciones': 'Lee las columnas de frases que aparecen en pantalla. Practica la lectura vertical y la ampliación del campo visual periférico.',
                    'configuracion_base': {
                        'tipo_contenido': 'columnas',
                        'elementos_por_pantalla': 2,
                        'columnas': 2,
                        'tiempo_display': 2000
                    }
                },
                {
                    'codigo_base': 'EL6',
                    'nombre': 'Lectura en columnas con frases de 3 palabras',
                    'descripcion': 'Lee columnas verticales de frases compuestas por 3 palabras, mejorando la lectura vertical.',
                    'instrucciones': 'Lee las frases de 3 palabras que aparecen en formato columna vertical. Amplía tu campo de visión para captar toda la columna de una vez.',
                    'configuracion_base': {
                        'tipo_contenido': 'columnas_3_palabras',
                        'elementos_por_pantalla': 10,
                        'columnas': 1,
                        'tiempo_display': 1500
                    }
                },
                {
                    'codigo_base': 'EL7',
                    'nombre': 'Lectura guiada en 3 fotos por renglón',
                    'descripcion': 'Practica la lectura con metronomo destacando 3 puntos de fijación por línea.',
                    'instrucciones': 'Lee el texto siguiendo el metronomo que destacará 3 zonas por cada línea. Concentra tu atención en cada zona destacada y amplía tu campo visual periférico.',
                    'configuracion_base': {
                        'tipo_contenido': 'texto_guiado_3_fotos',
                        'puntos_fijacion': 3,
                        'tiempo_fijacion': 800,
                        'usar_metronomo': True
                    }
                },
                {
                    'codigo_base': 'EL8',
                    'nombre': 'Lectura guiada en 2 fotos por renglón',
                    'descripcion': 'Practica la lectura con metronomo destacando 2 puntos de fijación por línea para máxima velocidad.',
                    'instrucciones': 'Lee el texto siguiendo el metronomo que destacará 2 zonas por cada línea. Este es el objetivo final: leer cada línea en solo 2 fijaciones visuales.',
                    'configuracion_base': {
                        'tipo_contenido': 'texto_guiado_2_fotos',
                        'puntos_fijacion': 2,
                        'tiempo_fijacion': 600,
                        'usar_metronomo': True
                    }
                }
            ],
            'EO': [
                {
                    'codigo_base': 'EO1',
                    'nombre': 'Seguimiento de círculos',
                    'descripcion': 'Sigue con la vista círculos que aparecen en diferentes posiciones.',
                    'instrucciones': 'Mira fijamente el centro del círculo hasta que desaparezca. Localízalo inmediatamente cuando aparezca en otra posición. Mueve solo los ojos, no la cabeza.',
                    'configuracion_base': {
                        'tipo_objeto': 'circle',
                        'posiciones_aleatorias': True,
                        'duracion_total': 40000,
                        'tiempo_display': 800
                    }
                },
                {
                    'codigo_base': 'EO2',
                    'nombre': 'Seguimiento de números con memoria',
                    'descripcion': 'Sigue números que aparecen en posiciones aleatorias y memoriza cuál se repite.',
                    'instrucciones': 'Observa la secuencia de números que aparecen en diferentes posiciones. Al final responde qué número se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_objeto': 'number',
                        'elementos': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                        'con_memoria': True,
                        'duracion_total': 10000,
                        'tiempo_display': 800
                    }
                },
                {
                    'codigo_base': 'EO3',
                    'nombre': 'Seguimiento de palabras con memoria',
                    'descripcion': 'Sigue palabras que aparecen en posiciones aleatorias y memoriza cuál se repite.',
                    'instrucciones': 'Observa la secuencia de palabras que aparecen en diferentes posiciones. Al final responde qué palabra se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_objeto': 'word',
                        'elementos': ['casa', 'perro', 'gato', 'mesa', 'silla', 'libro', 'agua', 'fuego', 'tierra', 'aire', 'luz'],
                        'con_memoria': True,
                        'duracion_total': 12000,
                        'tiempo_display': 900
                    }
                },
                {
                    'codigo_base': 'EO4',
                    'nombre': 'Seguimiento de pares de palabras con memoria',
                    'descripcion': 'Sigue pares de palabras que aparecen en posiciones aleatorias y memoriza cuál se repite.',
                    'instrucciones': 'Observa la secuencia de pares de palabras que aparecen en diferentes posiciones. Al final responde qué par se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_objeto': 'word_pair',
                        'elementos': ['casa blanca', 'perro negro', 'gato pequeño', 'mesa grande', 'silla cómoda', 'libro nuevo', 'agua fría', 'fuego caliente', 'tierra húmeda', 'aire puro'],
                        'con_memoria': True,
                        'duracion_total': 15000,
                        'tiempo_display': 1000
                    }
                }
            ],
            'EPM': [
                {
                    'codigo_base': 'EPM1',
                    'nombre': 'Verificación de artículo-sustantivo',
                    'descripcion': 'Determina si la concordancia entre artículo y sustantivo es correcta.',
                    'instrucciones': 'Lee cada frase y determina si la concordancia entre el artículo y el sustantivo es gramaticalmente correcta.',
                    'configuracion_base': {
                        'tipo_verificacion': 'articulo_sustantivo',
                        'frases_correctas': 10,
                        'frases_incorrectas': 10,
                        'tiempo_limite': 2000
                    }
                },
                {
                    'codigo_base': 'EPM2',
                    'nombre': 'Verificación de sujeto-verbo',
                    'descripcion': 'Determina si la concordancia entre sujeto y verbo es correcta.',
                    'instrucciones': 'Lee cada frase y determina si la concordancia entre el sujeto y el verbo es gramaticalmente correcta.',
                    'configuracion_base': {
                        'tipo_verificacion': 'sujeto_verbo',
                        'frases_correctas': 10,
                        'frases_incorrectas': 10,
                        'tiempo_limite': 2500
                    }
                },
                {
                    'codigo_base': 'EPM3',
                    'nombre': 'Verificación gramatical completa',
                    'descripcion': 'Determina si la oración completa es gramaticalmente correcta.',
                    'instrucciones': 'Lee cada oración completa y determina si es gramaticalmente correcta en todos sus aspectos.',
                    'configuracion_base': {
                        'tipo_verificacion': 'gramatical_completa',
                        'frases_correctas': 10,
                        'frases_incorrectas': 10,
                        'tiempo_limite': 3000
                    }
                }
            ],
            'EVM': [
                {
                    'codigo_base': 'EVM1',
                    'nombre': 'Secuencias de frutas',
                    'descripcion': 'Memoriza secuencias de frutas para identificar repeticiones y elementos faltantes.',
                    'instrucciones': 'Observa la secuencia de frutas que aparecerá. Al final deberás responder qué fruta se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_secuencia': 'frutas',
                        'elementos': ['manzana', 'pera', 'plátano', 'naranja', 'uva', 'fresa', 'melocotón', 'sandía', 'melón', 'piña', 'kiwi'],
                        'longitud_secuencia': 10,
                        'tiempo_display': 1000,
                        'preguntas': 2
                    }
                },
                {
                    'codigo_base': 'EVM2',
                    'nombre': 'Secuencias de meses',
                    'descripcion': 'Memoriza secuencias de meses para identificar repeticiones y elementos faltantes.',
                    'instrucciones': 'Observa la secuencia de meses que aparecerá. Al final deberás responder qué mes se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_secuencia': 'meses',
                        'elementos': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
                        'longitud_secuencia': 10,
                        'tiempo_display': 1200,
                        'preguntas': 2
                    }
                },
                {
                    'codigo_base': 'EVM3',
                    'nombre': 'Secuencias de países',
                    'descripcion': 'Memoriza secuencias de países para identificar repeticiones y elementos faltantes.',
                    'instrucciones': 'Observa la secuencia de países que aparecerá. Al final deberás responder qué país se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_secuencia': 'paises',
                        'elementos': ['España', 'Francia', 'Italia', 'Alemania', 'Portugal', 'Inglaterra', 'Suiza', 'Austria', 'Holanda', 'Bélgica', 'Suecia'],
                        'longitud_secuencia': 10,
                        'tiempo_display': 1400,
                        'preguntas': 2
                    }
                },
                {
                    'codigo_base': 'EVM4',
                    'nombre': 'Secuencias de nombres',
                    'descripcion': 'Memoriza secuencias de nombres para identificar repeticiones y elementos faltantes.',
                    'instrucciones': 'Observa la secuencia de nombres que aparecerá. Al final deberás responder qué nombre se ha repetido y cuál no ha aparecido.',
                    'configuracion_base': {
                        'tipo_secuencia': 'nombres',
                        'elementos': ['Juan', 'María', 'Pedro', 'Ana', 'Luis', 'Carmen', 'José', 'Isabel', 'Antonio', 'Pilar', 'Francisco'],
                        'longitud_secuencia': 10,
                        'tiempo_display': 1000,
                        'preguntas': 2
                    }
                }
            ],
            'EMD': [
                {
                    'codigo_base': 'EMD1',
                    'nombre': 'Memorización de 2 dígitos',
                    'descripcion': 'Memoriza y reproduce secuencias de 2 dígitos.',
                    'instrucciones': 'Observa los 2 dígitos que aparecerán brevemente y luego introdúcelos en el mismo orden.',
                    'configuracion_base': {
                        'digitos': 2,
                        'tiempo_display': 1000,
                        'intentos': 10
                    }
                },
                {
                    'codigo_base': 'EMD2',
                    'nombre': 'Memorización de 4 dígitos',
                    'descripcion': 'Memoriza y reproduce secuencias de 4 dígitos.',
                    'instrucciones': 'Observa los 4 dígitos que aparecerán brevemente y luego introdúcelos en el mismo orden.',
                    'configuracion_base': {
                        'digitos': 4,
                        'tiempo_display': 1500,
                        'intentos': 10
                    }
                },
                {
                    'codigo_base': 'EMD3',
                    'nombre': 'Memorización de 6 dígitos',
                    'descripcion': 'Memoriza y reproduce secuencias de 6 dígitos.',
                    'instrucciones': 'Observa los 6 dígitos que aparecerán brevemente y luego introdúcelos en el mismo orden.',
                    'configuracion_base': {
                        'digitos': 6,
                        'tiempo_display': 2000,
                        'intentos': 10
                    }
                }
            ]
        }
        
        # Configuraciones específicas por nivel
        nivel_configs = {
            1: {'velocidad_factor': 1.0, 'dificultad_factor': 1.0},
            2: {'velocidad_factor': 0.8, 'dificultad_factor': 1.2},
            3: {'velocidad_factor': 0.6, 'dificultad_factor': 1.5},
            4: {'velocidad_factor': 0.5, 'dificultad_factor': 1.8},
            5: {'velocidad_factor': 0.4, 'dificultad_factor': 2.0},
            6: {'velocidad_factor': 0.35, 'dificultad_factor': 2.3},
            7: {'velocidad_factor': 0.3, 'dificultad_factor': 2.5},
            8: {'velocidad_factor': 0.25, 'dificultad_factor': 2.8},
            9: {'velocidad_factor': 0.2, 'dificultad_factor': 3.0}
        }
        
        # Crear ejercicios
        for categoria_codigo, ejercicios_categoria in campayo_exercises.items():
            categoria = CategoriaEjercicio.objects.get(codigo=categoria_codigo)
            
            for ejercicio_base in ejercicios_categoria:
                # Determinar niveles según el bloque
                for nivel in range(1, 10):  # Niveles 1-9
                    # Determinar bloque según nivel
                    if nivel <= 3:
                        bloque = 1
                    elif nivel <= 6:
                        bloque = 2
                    else:
                        bloque = 3
                    
                    # Crear configuración específica para este nivel
                    config = ejercicio_base['configuracion_base'].copy()
                    nivel_config = nivel_configs[nivel]
                    
                    # Ajustar configuración según el nivel
                    if 'tiempo_display' in config:
                        config['tiempo_display'] = int(config['tiempo_display'] * nivel_config['velocidad_factor'])
                    if 'tiempo_fijacion' in config:
                        config['tiempo_fijacion'] = int(config['tiempo_fijacion'] * nivel_config['velocidad_factor'])
                    if 'tiempo_limite' in config:
                        config['tiempo_limite'] = int(config['tiempo_limite'] * nivel_config['velocidad_factor'])
                    
                    config['nivel'] = nivel
                    config['bloque'] = bloque
                    
                    # Crear código del ejercicio
                    codigo_ejercicio = f"{ejercicio_base['codigo_base']}_N{nivel}"
                    
                    # Determinar orden en bloque
                    ejercicios_en_bloque = Ejercicio.objects.filter(
                        categoria=categoria,
                        bloque=bloque
                    ).count()
                    orden_en_bloque = ejercicios_en_bloque + 1
                    
                    # Crear ejercicio
                    ejercicio, created = Ejercicio.objects.get_or_create(
                        codigo=codigo_ejercicio,
                        defaults={
                            'categoria': categoria,
                            'nombre': ejercicio_base['nombre'],
                            'descripcion': ejercicio_base['descripcion'],
                            'instrucciones': ejercicio_base['instrucciones'],
                            'nivel': nivel,
                            'bloque': bloque,
                            'orden_en_bloque': orden_en_bloque,
                            'configuracion': config,
                            'activo': True,
                            'requiere_pro': nivel > 3  # Niveles 4+ requieren Pro
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'  - Ejercicio {codigo_ejercicio} creado (Bloque {bloque})')
    
    def _create_block_requirements(self):
        """Crear requisitos entre bloques según método Campayo"""
        self.stdout.write('Creando requisitos de bloques...')
        
        # Requisitos según el método original de Campayo
        requisitos = [
            {
                'bloque_actual': 2,
                'bloques_requeridos': '1',
                'test_requerido': 'test_1'
            },
            {
                'bloque_actual': 3,
                'bloques_requeridos': '1,2',
                'test_requerido': 'test_2'
            }
        ]
        
        for req_data in requisitos:
            requisito, created = BloquePrevio.objects.get_or_create(
                bloque_actual=req_data['bloque_actual'],
                defaults=req_data
            )
            action = "creado" if created else "ya existe"
            self.stdout.write(f'  - Requisito para bloque {req_data["bloque_actual"]} {action}')
    
    def _load_reading_tests(self):
        """Cargar tests de lectura desde archivos JSON"""
        self.stdout.write('Cargando tests de lectura...')
        
        # Buscar archivos JSON en management/commands/tests_lectura/
        tests_dir = os.path.join(settings.BASE_DIR, 'usuarios', 'management', 'commands', 'tests_lectura')
        
        if not os.path.exists(tests_dir):
            os.makedirs(tests_dir, exist_ok=True)
            self.stdout.write(self.style.WARNING(f'Directorio creado: {tests_dir}'))
            self.stdout.write(self.style.WARNING('Coloca los archivos JSON de tests en esta carpeta'))
            return
        
        # Buscar archivos JSON
        json_files = [f for f in os.listdir(tests_dir) if f.endswith('.json')]
        
        if not json_files:
            self.stdout.write(self.style.WARNING(f'No se encontraron archivos JSON en {tests_dir}'))
            return
        
        # Procesar cada archivo JSON
        for json_file in json_files:
            file_path = os.path.join(tests_dir, json_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                
                # Crear o actualizar el test
                test, created = TestLectura.objects.get_or_create(
                    nombre=test_data["nombre"],
                    defaults={
                        "titulo": test_data.get("titulo", test_data["nombre"]),
                        "descripcion": test_data.get("descripcion", ""),
                        "instrucciones": test_data.get("instrucciones", ""),
                        "texto_titulo": test_data.get("texto_titulo", ""),
                        "texto_contenido": test_data.get("texto_contenido", ""),
                        "texto_autor": test_data.get("texto_autor", ""),
                        "dificultad": test_data.get("dificultad", "inicial"),
                        "numero_test": test_data.get("numero_test", 1),
                        "requiere_password": test_data.get("requiere_password", False),
                        "password_acceso": test_data.get("password_acceso", ""),
                        "requiere_pro": test_data.get("requiere_pro", False),
                        "test_previo_requerido": test_data.get("test_previo_requerido", ""),
                        "bloque_requerido": test_data.get("bloque_requerido"),
                        "activo": test_data.get("activo", True)
                    }
                )
                
                action = "creado" if created else "actualizado"
                self.stdout.write(f'  - Test "{test_data["nombre"]}" {action} desde {json_file}')
                
                # Si el test ya existe, eliminar preguntas anteriores
                if not created:
                    PreguntaTest.objects.filter(test=test).delete()
                
                # Crear preguntas y opciones
                if "preguntas" in test_data:
                    for orden, pregunta_data in enumerate(test_data["preguntas"]):
                        pregunta = PreguntaTest.objects.create(
                            test=test,
                            pregunta=pregunta_data["pregunta"],
                            orden=orden
                        )
                        
                        # Crear opciones
                        for opt_orden, opcion_data in enumerate(pregunta_data["opciones"]):
                            OpcionRespuesta.objects.create(
                                pregunta=pregunta,
                                texto=opcion_data["texto"],
                                es_correcta=opcion_data.get("es_correcta", False),
                                orden=opt_orden
                            )
                    
                    self.stdout.write(f'    - {len(test_data["preguntas"])} preguntas creadas')
                
                # Calcular número de palabras automáticamente si no está especificado
                if test.texto_contenido and not test.numero_palabras:
                    test.numero_palabras = len(test.texto_contenido.split())
                    test.save()
                    self.stdout.write(f'    - Calculadas {test.numero_palabras} palabras')
                
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'Error JSON en {json_file}: {str(e)}'))
            except KeyError as e:
                self.stdout.write(self.style.ERROR(f'Campo requerido faltante en {json_file}: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error procesando {json_file}: {str(e)}'))

    def _display_summary(self):
        """Mostrar resumen de ejercicios creados"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE EJERCICIOS MÉTODO CAMPAYO'))
        self.stdout.write('='*60)
        
        for bloque in [1, 2, 3]:
            ejercicios_bloque = Ejercicio.objects.filter(bloque=bloque).count()
            self.stdout.write(f'Bloque {bloque} (Niveles {(bloque-1)*3+1}-{bloque*3}): {ejercicios_bloque} ejercicios')
            
            for categoria in ['EL', 'EO', 'EPM', 'EVM', 'EMD']:
                count = Ejercicio.objects.filter(bloque=bloque, categoria__codigo=categoria).count()
                if count > 0:
                    self.stdout.write(f'  - {categoria}: {count} ejercicios')
        
        total_ejercicios = Ejercicio.objects.count()
        self.stdout.write(f'\nTOTAL: {total_ejercicios} ejercicios creados')
        self.stdout.write('='*60)

    def _get_random_text_fragment(self, word_count=50):
        """
        Obtiene un fragmento aleatorio de texto de cualquier test de lectura disponible
        para usar en los ejercicios EL7 y EL8
        """
        try:
            # Obtener todos los tests disponibles
            tests = TestLectura.objects.filter(activo=True)
            if not tests.exists():
                # Texto por defecto si no hay tests
                return """La lectura rápida es una habilidad fundamental para el desarrollo personal y profesional.
Mediante la técnica fotográfica podemos incrementar significativamente nuestra velocidad de lectura.
El entrenamiento constante y la práctica diaria son elementos clave para el éxito.
Los ejercicios de Campayo han demostrado ser extraordinariamente efectivos para miles de estudiantes.
La concentración y la relajación mental facilitan enormemente el proceso de aprendizaje."""
            
            # Seleccionar un test aleatorio
            test = random.choice(tests)
            if test.texto_contenido:
                # Dividir en palabras y tomar un fragmento
                words = test.texto_contenido.split()
                if len(words) >= word_count:
                    start_index = random.randint(0, len(words) - word_count)
                    fragment_words = words[start_index:start_index + word_count]
                    return ' '.join(fragment_words)
                else:
                    return test.texto_contenido
            
            # Si no hay contenido, devolver texto por defecto
            return """La lectura rápida es una habilidad fundamental para el desarrollo personal y profesional.
Mediante la técnica fotográfica podemos incrementar significativamente nuestra velocidad de lectura."""
        
        except Exception:
            # En caso de error, devolver texto por defecto
            return """La lectura rápida es una habilidad fundamental para el desarrollo personal y profesional.
Mediante la técnica fotográfica podemos incrementar significativamente nuestra velocidad de lectura."""
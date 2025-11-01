/**
 * ELExercises - Ejercicios de Entrenamiento de Lectura (VERSIÓN MEJORADA)
 * EL1: Reconocimiento de pares de dígitos
 * EL2: Reconocimiento de sílabas  
 * EL3: Lectura de 2 palabras
 * EL4: Lectura de 3 palabras
 * EL5: Lectura línea por línea en columnas (2 palabras por línea) con metrónomo
 * EL6: Lectura línea por línea en columnas (3 palabras por línea) con metrónomo
 * EL7: Lectura guiada en 3 fotos por renglón con metrónomo
 * EL8: Lectura guiada en 2 fotos por renglón con metrónomo
 */

window.ELExercises = (function() {
    
    // Datos específicos para ejercicios EL
    const DATA = {
        // EL2 - Consonantes y vocales para formar sílabas
        CONSONANTS: ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z'],
        VOWELS: ['A', 'E', 'I', 'O', 'U'],
        
        // EL3 - Frases de 2 palabras
        PHRASES_2: [
            'Casa grande', 'Perro negro', 'Mesa redonda', 'Libro nuevo', 'Agua fría',
            'Sol brillante', 'Luna llena', 'Mar azul', 'Montaña alta', 'Río claro',
            'Flor bonita', 'Árbol verde', 'Puerta abierta', 'Ventana limpia', 'Calle larga',
            'Cielo despejado', 'Noche oscura', 'Día soleado', 'Viento fuerte', 'Lluvia suave'
        ],
        
        // EL4 - Frases de 3 palabras
        PHRASES_3: [
            'El perro ladra', 'La casa está', 'Un libro interesante', 'Mi madre cocina',
            'Tu hermano estudia', 'Los niños juegan', 'Las flores crecen', 'Este coche corre',
            'Aquella montaña alta', 'Algunos gatos duermen', 'Muchas personas trabajan', 'Todos estudiantes aprenden',
            'Su padre lee', 'Nuestro jardín florece', 'Vuestros amigos vienen', 'Estos pájaros cantan'
        ]
    };

    // Variables globales para los ejercicios con metrónomo
    let metronome = null;

    // Inicializar el contenedor de ejercicio
    function initContainer() {
        const container = ExerciseCore.getElements().exerciseContainer;
        if (!container) return null;

        const codigo = window.EXERCISE_CONFIG.codigo;
        let html = '';

        if (codigo.includes('EL7') || codigo.includes('EL8')) {
            // Para ejercicios de lectura guiada
            html = `
                <!-- Modal de orientación -->
                <div id="orientation-modal" class="orientation-modal" style="display: none;">
                    <div class="orientation-modal-content">
                        <div class="orientation-modal-icon">📱</div>
                        <h3>Recomendación</h3>
                        <p>
                            Para una mejor experiencia en este ejercicio de lectura, 
                            <strong>gira tu dispositivo a posición horizontal</strong>.
                        </p>
                        <button id="orientation-understood" class="btn-exercise btn-exercise-lg">
                            Entendido
                        </button>
                    </div>
                </div>
                
                <div class="text-center py-4">
                    <h6 class="text-muted mb-3">
                        ${codigo.includes('EL7') ? 'Lectura guiada con 3 fotos por línea' : 'Lectura guiada con 2 fotos por línea'}
                    </h6>
                    <div id="guided-reading-container" style="max-width: 700px; margin: 0 auto;">
                        <div id="guided-text" style="font-size: 18px; line-height: 2.0; text-align: left; padding: 20px; border-radius: 8px; min-height: 400px;">
                            <!-- El texto se cargará aquí -->
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">Línea <span id="line-counter">0</span> de <span id="total-lines">0</span></small>
                        </div>
                        <!-- Indicador de metrónomo -->
                        <div class="mt-3">
                            <div id="metronome-indicator" class="metronome-indicator"></div>
                        </div>
                    </div>
                </div>
            `;
        } else if (codigo.includes('EL5') || codigo.includes('EL6')) {
            // Para ejercicios de lectura línea por línea en columnas
            html = `
                <div class="text-center py-4">
                    <h6 class="text-muted mb-3">
                        ${codigo.includes('EL5') ? 'Lectura en columnas (2 palabras por línea)' : 'Lectura en columnas (3 palabras por línea)'}
                    </h6>
                    <div id="column-reading-container" style="max-width: 800px; margin: 0 auto;">
                        <div id="column-text" style="font-size: 16px; line-height: 2.2; text-align: left; padding: 30px; border-radius: 8px; min-height: 500px; background: #f8f9fa; border: 2px solid #e9ecef;">
                            <!-- El texto completo se mostrará aquí -->
                        </div>
                        <div class="mt-3 d-flex justify-content-between align-items-center">
                            <small class="text-muted">Columna <span id="column-counter">0</span> de <span id="total-columns">0</span></small>
                            <!-- Indicador de metrónomo -->
                            <div id="metronome-indicator" class="metronome-indicator"></div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Para otros ejercicios EL
            let instruction = '';
            if (codigo.includes('EL1')) instruction = 'Pronuncia el número resultante';
            else if (codigo.includes('EL2')) instruction = 'Pronuncia la sílaba resultante';
            else instruction = 'Lee las palabras';

            html = `
                <div class="text-center py-4">
                    <h6 class="text-muted mb-3">${instruction}</h6>
                    <div id="el-display" class="display-4 fw-bold text-primary mb-4" style="font-family: monospace; font-size:35px !important; letter-spacing: 0.3em; min-height: 120px; display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                        
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
        return container;
    }

    // Función para obtener texto aleatorio de tests de lectura
    function getRandomTestText() {
        if (window.availableTests && Array.isArray(window.availableTests) && window.availableTests.length > 0) {
            const randomIndex = Math.floor(Math.random() * window.availableTests.length);
            const selectedTest = window.availableTests[randomIndex];
            
            console.log(`Usando texto del test: "${selectedTest.name}"`);
            
            // Dividir en párrafos y tomar solo un fragmento aleatorio
            const paragraphs = selectedTest.text_content.split('\n').filter(p => p.trim() !== '');
            
            if (paragraphs.length > 3) {
                // Seleccionar aleatoriamente un fragmento de 4-8 párrafos para tener aproximadamente 20 líneas
                const fragmentSize = Math.min(8, Math.max(4, Math.floor(paragraphs.length / 2)));
                const startIndex = Math.floor(Math.random() * (paragraphs.length - fragmentSize));
                const selectedParagraphs = paragraphs.slice(startIndex, startIndex + fragmentSize);
                
                return selectedParagraphs.join('\n\n');
            }
            
            return selectedTest.text_content;
        } else {
            // Texto por defecto si no hay tests disponibles
            return `La lectura rápida es una habilidad fundamental para el desarrollo personal y profesional. Mediante la técnica fotográfica podemos incrementar significativamente nuestra velocidad de lectura.

El entrenamiento constante y la práctica diaria son elementos clave para el éxito. Los ejercicios de Campayo han demostrado ser extraordinariamente efectivos para miles de estudiantes.

La concentración y la relajación mental facilitan enormemente el proceso de aprendizaje. El campo de visión periférica se puede desarrollar mediante ejercicios específicos.

La técnica de lectura en columnas permite entrenar el movimiento ocular de forma sistemática. Los ojos aprenden a realizar movimientos más eficientes y precisos.`;
        }
    }

    // Función para procesar texto en líneas para lectura en columnas
    function processTextIntoColumns(text, wordsPerLine) {
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        const lines = [];
        
        sentences.forEach(sentence => {
            const words = sentence.trim().split(/\s+/);
            for (let i = 0; i < words.length; i += wordsPerLine) {
                const lineWords = words.slice(i, i + wordsPerLine);
                if (lineWords.length > 0) {
                    lines.push(lineWords.join(' '));
                }
            }
        });
        
        return lines;
    }

    // Función para procesar texto para lectura guiada (EL7/EL8)
    function processTextForGuidedReading(text) {
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        const lines = [];
        
        sentences.forEach(sentence => {
            const words = sentence.trim().split(/\s+/);
            // Aproximadamente 10-12 palabras por línea para lectura guiada
            const wordsPerLine = 11;
            
            for (let i = 0; i < words.length; i += wordsPerLine) {
                const lineWords = words.slice(i, i + wordsPerLine);
                if (lineWords.length > 0) {
                    lines.push(lineWords.join(' '));
                }
            }
        });
        
        return lines;
    }

    // Función para crear metrónomo con indicador visual
    function createMetronome(callback) {
        if (typeof Metronome !== 'undefined') {
            const visualCallback = (beat, isAccented) => {
                // Actualizar indicador visual
                const indicator = document.getElementById('metronome-indicator');
                if (indicator) {
                    if (isAccented) {
                        indicator.style.background = '#ff4444';
                        indicator.style.transform = 'scale(1.3)';
                    } else {
                        indicator.style.background = '#4444ff';
                        indicator.style.transform = 'scale(1.1)';
                    }
                    
                    setTimeout(() => {
                        indicator.style.background = '#ccc';
                        indicator.style.transform = 'scale(1)';
                    }, 100);
                }
                
                // Ejecutar callback del ejercicio
                if (callback) callback();
            };

            return new Metronome({
                tempo: 60,
                soundEnabled: true,
                volume: 0.7,
                visualCallback: visualCallback
            });
        }
        return null;
    }

    // Función para mostrar modal de orientación y esperar confirmación
    function showOrientationModalAndWait(callback) {
        const orientationModal = document.getElementById('orientation-modal');
        const understoodBtn = document.getElementById('orientation-understood');
        
        if (orientationModal && understoodBtn) {
            // Detectar si es dispositivo móvil o tablet
            const isMobile = /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            const isTablet = /iPad|Android(?=.*Mobile)|Tablet/i.test(navigator.userAgent) || 
                           (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); // iPad con iPadOS
            
            if (isMobile || isTablet) {
                // Mostrar modal
                orientationModal.style.display = 'flex';
                
                // Configurar botón
                const handleUnderstood = () => {
                    orientationModal.style.display = 'none';
                    understoodBtn.removeEventListener('click', handleUnderstood);
                    // Continuar con el ejercicio
                    if (callback) callback();
                };
                
                understoodBtn.addEventListener('click', handleUnderstood);
            } else {
                // En desktop, continuar directamente
                if (callback) callback();
            }
        } else {
            // Si no se encuentra el modal, continuar directamente
            if (callback) callback();
        }
    }

    // Función principal de inicio
    function start() {
        console.log('Iniciando ejercicio EL:', window.EXERCISE_CONFIG.codigo);
        
        const container = initContainer();
        if (!container) {
            console.error('No se pudo inicializar el contenedor');
            return;
        }

        const codigo = window.EXERCISE_CONFIG.codigo;
        const configuracion = window.EXERCISE_CONFIG.configuracion || {};

        if (codigo.includes('EL1')) {
            startEL1(configuracion);
        } else if (codigo.includes('EL2')) {
            startEL2(configuracion);
        } else if (codigo.includes('EL3')) {
            startEL3(configuracion);
        } else if (codigo.includes('EL4')) {
            startEL4(configuracion);
        } else if (codigo.includes('EL5')) {
            startEL5(configuracion);
        } else if (codigo.includes('EL6')) {
            startEL6(configuracion);
        } else if (codigo.includes('EL7')) {
            startEL7(configuracion);
        } else if (codigo.includes('EL8')) {
            startEL8(configuracion);
        }
    }

    // EL1: Reconocimiento de pares de dígitos
    function startEL1(config) {
        const display = document.getElementById('el-display');
        const state = ExerciseCore.getState();
        
        state.totalSteps = config.repeticiones || 20;
        state.currentStep = 0;
        
        const showNextDigits = () => {
            if (state.currentStep >= state.totalSteps) {
                ExerciseCore.completeExercise();
                return;
            }
            
            const digit1 = Math.floor(Math.random() * 10);
            const digit2 = Math.floor(Math.random() * 10);
            display.textContent = `${digit1} + ${digit2}`;
            
            state.currentStep++;
            ExerciseCore.updateProgress();
            
            setTimeout(showNextDigits, config.intervalo || 2000);
        };
        
        setTimeout(showNextDigits, 1000);
    }

    // EL2: Reconocimiento de sílabas
    function startEL2(config) {
        const display = document.getElementById('el-display');
        const state = ExerciseCore.getState();
        
        state.totalSteps = config.repeticiones || 20;
        state.currentStep = 0;
        
        const showNextSyllable = () => {
            if (state.currentStep >= state.totalSteps) {
                ExerciseCore.completeExercise();
                return;
            }
            
            const consonant = DATA.CONSONANTS[Math.floor(Math.random() * DATA.CONSONANTS.length)];
            const vowel = DATA.VOWELS[Math.floor(Math.random() * DATA.VOWELS.length)];
            display.textContent = consonant + vowel;
            
            state.currentStep++;
            ExerciseCore.updateProgress();
            
            setTimeout(showNextSyllable, config.intervalo || 2000);
        };
        
        setTimeout(showNextSyllable, 1000);
    }

    // EL3: Lectura de 2 palabras
    function startEL3(config) {
        const display = document.getElementById('el-display');
        const state = ExerciseCore.getState();
        
        state.totalSteps = config.repeticiones || 15;
        state.currentStep = 0;
        
        const showNextPhrase = () => {
            if (state.currentStep >= state.totalSteps) {
                ExerciseCore.completeExercise();
                return;
            }
            
            const phrase = DATA.PHRASES_2[Math.floor(Math.random() * DATA.PHRASES_2.length)];
            display.textContent = phrase;
            
            state.currentStep++;
            ExerciseCore.updateProgress();
            
            setTimeout(showNextPhrase, config.intervalo || 2500);
        };
        
        setTimeout(showNextPhrase, 1000);
    }

    // EL4: Lectura de 3 palabras
    function startEL4(config) {
        const display = document.getElementById('el-display');
        const state = ExerciseCore.getState();
        
        state.totalSteps = config.repeticiones || 15;
        state.currentStep = 0;
        
        const showNextPhrase = () => {
            if (state.currentStep >= state.totalSteps) {
                ExerciseCore.completeExercise();
                return;
            }
            
            const phrase = DATA.PHRASES_3[Math.floor(Math.random() * DATA.PHRASES_3.length)];
            display.textContent = phrase;
            
            state.currentStep++;
            ExerciseCore.updateProgress();
            
            setTimeout(showNextPhrase, config.intervalo || 3000);
        };
        
        setTimeout(showNextPhrase, 1000);
    }

    // EL5: Lectura en columnas (2 palabras por línea) con metrónomo
    function startEL5(config) {
        const text = getRandomTestText();
        const wordsPerLine = 2;
        const lines = processTextIntoColumns(text, wordsPerLine);
        
        startColumnReading(lines, wordsPerLine, config);
    }

    // EL6: Lectura en columnas (3 palabras por línea) con metrónomo
    function startEL6(config) {
        const text = getRandomTestText();
        const wordsPerLine = 3;
        const lines = processTextIntoColumns(text, wordsPerLine);
        
        startColumnReading(lines, wordsPerLine, config);
    }

    // Función común para lectura en columnas
    function startColumnReading(lines, wordsPerLine, config) {
        const textContainer = document.getElementById('column-text');
        const columnCounter = document.getElementById('column-counter');
        const totalColumns = document.getElementById('total-columns');
        
        const state = ExerciseCore.getState();
        state.textLines = lines;
        state.currentColumn = 0;
        state.totalSteps = lines.length;
        state.currentStep = 0;
        
        // Mostrar estadísticas
        columnCounter.textContent = 0;
        totalColumns.textContent = lines.length;
        
        // Crear el texto completo con líneas numeradas
        let fullTextHTML = '';
        lines.forEach((line, index) => {
            fullTextHTML += `<div id="column-line-${index}" style="margin-bottom: 8px; padding: 4px 8px; border-radius: 4px; transition: all 0.2s ease;">${line}</div>`;
        });
        textContainer.innerHTML = fullTextHTML;
        
        // Configurar metrónomo
        const intervalMs = config.intervalo || (wordsPerLine === 2 ? 1500 : 2000);
        
        const metronomeCallback = () => {
            // Limpiar resaltados anteriores
            document.querySelectorAll('[id^="column-line-"]').forEach(line => {
                line.style.backgroundColor = 'transparent';
                line.style.color = '#333';
                line.style.transform = 'scale(1)';
                line.style.borderLeft = 'none';
                line.style.fontWeight = 'normal';
            });
            
            // Verificar si terminamos
            if (state.currentColumn >= state.textLines.length) {
                if (metronome) metronome.stop();
                setTimeout(() => ExerciseCore.completeExercise(), 1000);
                return;
            }
            
            // Resaltar línea actual
            const currentLineElement = document.getElementById(`column-line-${state.currentColumn}`);
            if (currentLineElement) {
                currentLineElement.style.backgroundColor = '#e3f2fd';
                currentLineElement.style.color = '#1976d2';
                currentLineElement.style.transform = 'scale(1.05)';
                currentLineElement.style.borderLeft = '6px solid #1976d2';
                currentLineElement.style.fontWeight = 'bold';
                
                // Hacer scroll suave hacia la línea actual
                currentLineElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
            
            // Actualizar contadores
            state.currentColumn++;
            state.currentStep++;
            columnCounter.textContent = state.currentColumn;
            ExerciseCore.updateProgress();
        };

        metronome = createMetronome(metronomeCallback);
        
        if (metronome) {
            const beatsPerMinute = Math.round(60000 / intervalMs);
            metronome.setTempo(beatsPerMinute);
            
            // Comenzar el metrónomo después de un breve delay
            setTimeout(() => {
                metronome.start();
            }, 2000);
        } else {
            // Fallback sin metrónomo
            setTimeout(() => {
                startColumnReadingFallback(intervalMs);
            }, 2000);
        }
    }

    // Fallback para lectura en columnas sin metrónomo
    function startColumnReadingFallback(intervalMs) {
        const state = ExerciseCore.getState();
        const columnCounter = document.getElementById('column-counter');
        
        state.interval = setInterval(() => {
            if (state.currentColumn >= state.textLines.length) {
                clearInterval(state.interval);
                ExerciseCore.completeExercise();
                return;
            }
            
            // Limpiar resaltados anteriores
            document.querySelectorAll('[id^="column-line-"]').forEach(line => {
                line.style.backgroundColor = 'transparent';
                line.style.color = '#333';
                line.style.transform = 'scale(1)';
                line.style.borderLeft = 'none';
                line.style.fontWeight = 'normal';
            });
            
            // Resaltar línea actual
            const currentLineElement = document.getElementById(`column-line-${state.currentColumn}`);
            if (currentLineElement) {
                currentLineElement.style.backgroundColor = '#e3f2fd';
                currentLineElement.style.color = '#1976d2';
                currentLineElement.style.transform = 'scale(1.05)';
                currentLineElement.style.borderLeft = '6px solid #1976d2';
                currentLineElement.style.fontWeight = 'bold';
                
                // Hacer scroll suave hacia la línea actual
                currentLineElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
            
            // Actualizar contadores
            state.currentColumn++;
            state.currentStep++;
            columnCounter.textContent = state.currentColumn;
            ExerciseCore.updateProgress();
        }, intervalMs);
    }

    // EL7: Lectura guiada en 3 fotos por renglón con metrónomo
    function startEL7(config) {
        const text = getRandomTestText();
        const lines = processTextForGuidedReading(text);
        const sectionsPerLine = 3;
        
        startGuidedReading(lines, sectionsPerLine, config);
    }

    // EL8: Lectura guiada en 2 fotos por renglón con metrónomo
    function startEL8(config) {
        const text = getRandomTestText();
        const lines = processTextForGuidedReading(text);
        const sectionsPerLine = 2;
        
        startGuidedReading(lines, sectionsPerLine, config);
    }

    // Función para dividir una línea en segmentos equitativos
    function splitLineIntoSegments(line, numSegments) {
        const words = line.split(' ').filter(w => w.trim() !== '');
        const segments = [];
        const wordsPerSegment = Math.ceil(words.length / numSegments);
        
        for (let i = 0; i < numSegments; i++) {
            const start = i * wordsPerSegment;
            const end = Math.min(start + wordsPerSegment, words.length);
            
            if (start < words.length) {
                segments.push({ start, end });
            }
        }
        
        return segments;
    }

    // Función común para lectura guiada
    function startGuidedReading(lines, sectionsPerLine, config) {
        const textContainer = document.getElementById('guided-text');
        const lineCounter = document.getElementById('line-counter');
        const totalLines = document.getElementById('total-lines');
        
        const state = ExerciseCore.getState();
        state.textLines = lines;
        state.currentLine = 0;
        state.currentSection = 0;
        state.totalSteps = lines.length * sectionsPerLine;
        state.currentStep = 0;
        
        // Mostrar estadísticas
        lineCounter.textContent = 1; // Comenzar en 1 para el usuario
        totalLines.textContent = lines.length;
        
        // Crear el texto completo con líneas numeradas (PREPARAR TODO PRIMERO)
        let fullTextHTML = '';
        lines.forEach((line, index) => {
            fullTextHTML += `<div id="line-${index}" style="margin-bottom: 12px; padding: 8px; border-radius: 4px; transition: all 0.3s ease;">${line}</div>`;
        });
        textContainer.innerHTML = fullTextHTML;
        
        // Configurar velocidad según el número de secciones
        const baseInterval = config.intervalo || 1200;
        const intervalMs = sectionsPerLine === 2 ? baseInterval : Math.round(baseInterval * 0.8);
        
        // Función para detectar móvil o tablet
        function isMobileOrTablet() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
                || (window.innerWidth <= 1024);
        }
        
        // Definir las funciones de lectura primero
        function highlightCurrentSection() {
            // Limpiar TODOS los resaltados anteriores
            document.querySelectorAll('[id^="line-"]').forEach(line => {
                const lineIndex = parseInt(line.id.replace('line-', ''));
                if (lineIndex < state.textLines.length) {
                    line.innerHTML = state.textLines[lineIndex];
                }
                line.style.backgroundColor = 'transparent';
                line.style.color = '#333';
                line.style.transform = 'scale(1)';
                line.style.borderLeft = 'none';
            });
            
            // Verificar si terminamos
            if (state.currentLine >= state.textLines.length) {
                if (metronome) metronome.stop();
                setTimeout(() => ExerciseCore.completeExercise(), 1000);
                return;
            }
            
            // Obtener línea actual
            const currentLineElement = document.getElementById(`line-${state.currentLine}`);
            if (currentLineElement) {
                const text = state.textLines[state.currentLine];
                
                // Dividir la línea en segmentos equitativos
                const segments = splitLineIntoSegments(text, sectionsPerLine);
                
                // Verificar si la sección actual existe
                if (state.currentSection >= segments.length) {
                    // Si no hay suficientes segmentos, pasar a la siguiente línea
                    state.currentLine++;
                    state.currentSection = 0; // IMPORTANTE: Siempre reiniciar a 0 al cambiar de línea
                    lineCounter.textContent = state.currentLine + 1;
                    ExerciseCore.updateProgress();
                    state.currentStep++;
                    
                    // Si terminamos todas las líneas
                    if (state.currentLine >= state.textLines.length) {
                        if (metronome) metronome.stop();
                        setTimeout(() => ExerciseCore.completeExercise(), 1000);
                    }
                    return;
                }
                
                // Resaltar línea
                currentLineElement.style.backgroundColor = '#e3f2fd';
                currentLineElement.style.color = '#1976d2';
                currentLineElement.style.transform = 'scale(1.02)';
                currentLineElement.style.borderLeft = '4px solid #1976d2';
                
                // Obtener el segmento actual
                const currentSegment = segments[state.currentSection];
                const words = text.split(' ').filter(w => w.trim() !== '');
                
                // Crear texto con el GRUPO COMPLETO resaltado (no palabra por palabra)
                let highlightedText = '';
                let segmentText = words.slice(currentSegment.start, currentSegment.end).join(' ');
                let beforeSegment = words.slice(0, currentSegment.start).join(' ');
                let afterSegment = words.slice(currentSegment.end).join(' ');
                
                if (beforeSegment) highlightedText += beforeSegment + ' ';
                highlightedText += `<span style="background-color: #ffeb3b; color: #1976d2; font-weight: bold; padding: 2px 4px; border-radius: 3px;">${segmentText}</span>`;
                if (afterSegment) highlightedText += ' ' + afterSegment;
                
                currentLineElement.innerHTML = highlightedText.trim();
                
                // Hacer scroll suave hacia la línea actual
                currentLineElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
        
        const metronomeCallback = () => {
            // Si es la primera vez, resaltar inmediatamente la primera sección
            if (state.currentStep === 0) {
                state.currentStep = 1;
                highlightCurrentSection();
                return;
            }
            
            // Avanzar sección
            state.currentSection++;
            
            if (state.currentSection >= sectionsPerLine) {
                // Pasar a la siguiente línea y REINICIAR a la primera sección
                state.currentLine++;
                state.currentSection = 0; // IMPORTANTE: Siempre reiniciar a 0 al cambiar de línea
                
                lineCounter.textContent = state.currentLine + 1;
                ExerciseCore.updateProgress();
                state.currentStep++;
                
                // Si hemos terminado todas las líneas, salir
                if (state.currentLine >= state.textLines.length) {
                    if (metronome) metronome.stop();
                    setTimeout(() => ExerciseCore.completeExercise(), 1000);
                    return;
                }
            }
            
            highlightCurrentSection();
        };
        
        function startReadingProcess() {
            metronome = createMetronome(metronomeCallback);
            
            if (metronome) {
                const beatsPerMinute = Math.round(60000 / intervalMs);
                metronome.setTempo(beatsPerMinute);
                
                // Comenzar el metrónomo inmediatamente
                setTimeout(() => {
                    metronome.start();
                }, 500);
            } else {
                // Fallback sin metrónomo
                setTimeout(() => {
                    startGuidedReadingFallback(sectionsPerLine, intervalMs);
                }, 500);
            }
        }
        
        // AHORA mostrar modal de orientación en dispositivos móviles/tablets (UNA SOLA VEZ)
        const orientationModal = document.getElementById('orientation-modal');
        const orientationBtn = document.getElementById('orientation-understood');
        
        // Verificar si ya se mostró el modal antes
        if (!window.orientationModalShown && isMobileOrTablet() && orientationModal) {
            window.orientationModalShown = true; // Marcar que ya se mostró
            orientationModal.style.display = 'flex';
            
            // Remover listeners previos clonando el botón
            const newBtn = orientationBtn.cloneNode(true);
            orientationBtn.parentNode.replaceChild(newBtn, orientationBtn);
            
            newBtn.addEventListener('click', function() {
                orientationModal.style.display = 'none';
                startReadingProcess();
            });
        } else {
            // Si no es móvil o ya se mostró, iniciar directamente
            startReadingProcess();
        }
    }

    // Fallback para lectura guiada sin metrónomo
    function startGuidedReadingFallback(sectionsPerLine, intervalMs) {
        const state = ExerciseCore.getState();
        const lineCounter = document.getElementById('line-counter');
        
        state.interval = setInterval(() => {
            if (state.currentLine >= state.textLines.length) {
                clearInterval(state.interval);
                ExerciseCore.completeExercise();
                return;
            }
            
            // Avanzar sección primero
            state.currentSection++;
            
            if (state.currentSection >= sectionsPerLine) {
                // Pasar a la siguiente línea y REINICIAR a la primera sección
                state.currentLine++;
                state.currentSection = 0; // IMPORTANTE: Siempre reiniciar a 0 al cambiar de línea
                
                lineCounter.textContent = state.currentLine + 1;
                ExerciseCore.updateProgress();
                state.currentStep++;
                
                // Si hemos terminado todas las líneas, salir
                if (state.currentLine >= state.textLines.length) {
                    clearInterval(state.interval);
                    ExerciseCore.completeExercise();
                    return;
                }
            }
            
            // Limpiar TODOS los resaltados anteriores
            document.querySelectorAll('[id^="line-"]').forEach(line => {
                // Restaurar el texto original sin resaltados
                const lineIndex = parseInt(line.id.replace('line-', ''));
                if (lineIndex < state.textLines.length) {
                    line.innerHTML = state.textLines[lineIndex];
                }
                line.style.backgroundColor = 'transparent';
                line.style.color = '#333';
                line.style.transform = 'scale(1)';
                line.style.borderLeft = 'none';
            });
            
            // Resaltar la línea y sección actual
            const currentLineElement = document.getElementById(`line-${state.currentLine}`);
            if (currentLineElement) {
                currentLineElement.style.backgroundColor = '#e3f2fd';
                currentLineElement.style.color = '#1976d2';
                currentLineElement.style.transform = 'scale(1.02)';
                currentLineElement.style.borderLeft = '4px solid #1976d2';
                
                // Dividir la línea en segmentos equitativos
                const text = state.textLines[state.currentLine];
                const segments = splitLineIntoSegments(text, sectionsPerLine);
                
                // Verificar si la sección actual existe
                if (state.currentSection >= segments.length) {
                    return;
                }
                
                // Obtener el segmento actual
                const currentSegment = segments[state.currentSection];
                const words = text.split(' ').filter(w => w.trim() !== '');
                
                // Crear texto con el GRUPO COMPLETO resaltado (no palabra por palabra)
                let highlightedText = '';
                let segmentText = words.slice(currentSegment.start, currentSegment.end).join(' ');
                let beforeSegment = words.slice(0, currentSegment.start).join(' ');
                let afterSegment = words.slice(currentSegment.end).join(' ');
                
                if (beforeSegment) highlightedText += beforeSegment + ' ';
                highlightedText += `<span style="background-color: #ffeb3b; color: #1976d2; font-weight: bold; padding: 2px 4px; border-radius: 3px;">${segmentText}</span>`;
                if (afterSegment) highlightedText += ' ' + afterSegment;
                
                currentLineElement.innerHTML = highlightedText.trim();
                
                // Hacer scroll suave hacia la línea actual
                currentLineElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }, intervalMs);
    }

    // Cleanup function
    function cleanup() {
        if (metronome) {
            metronome.destroy();
            metronome = null;
        }
        
        const state = ExerciseCore.getState();
        if (state.interval) {
            clearInterval(state.interval);
            state.interval = null;
        }
    }

    // API pública
    return {
        start: start,
        cleanup: cleanup
    };

})();
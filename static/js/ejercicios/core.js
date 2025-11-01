/**
 * ExerciseCore - Funcionalidad común para todos los ejercicios
 * Maneja la navegación entre pantallas, progreso, resultados y comunicación con el servidor
 */

window.ExerciseCore = (function() {
    
    // Estado global del ejercicio
    let state = {
        currentStep: 0,
        totalSteps: 40,
        isRunning: false,
        interval: null,
        correctAnswers: 0,
        totalQuestions: 20,
        totalAttempts: 10,
        currentAttempt: 0,
        waitingForInput: false,
        currentQuestionIndex: 0,
        
        // Variables para tiempo de respuesta EPM
        questionStartTime: 0,
        totalResponseTime: 0,
        
        // Elementos específicos para ejercicios de memoria
        repeatedItem: null,
        missingItem: null,
        
        // Para EMD
        numberOfDigits: 2,
        currentNumbers: [],
        showingNumbers: false,
        
        // Para ejercicios guiados (EL7, EL8)
        currentLine: 0,
        currentSection: -1,
        textLines: [],
        sectionsPerLine: 3
    };

    // Referencias a elementos del DOM
    const elements = {
        startScreen: null,
        displayArea: null,
        resultsScreen: null,
        completionScreen: null,
        progressBar: null,
        progressText: null,
        startButton: null,
        continueButton: null,
        exerciseContainer: null
    };

    // Inicialización
    function init() {
        console.log('Inicializando ExerciseCore...');
        
        // Obtener referencias a elementos del DOM
        elements.startScreen = document.getElementById('start-screen');
        elements.displayArea = document.getElementById('display-area');
        elements.resultsScreen = document.getElementById('results-screen');
        elements.completionScreen = document.getElementById('completion-screen');
        elements.progressBar = document.getElementById('progress-bar');
        elements.progressText = document.getElementById('progress-text');
        elements.startButton = document.getElementById('start-exercise');
        elements.continueButton = document.getElementById('continue-to-completion');
        elements.exerciseContainer = document.getElementById('exercise-display-container');
        
        // Configurar eventos
        if (elements.startButton) {
            elements.startButton.addEventListener('click', startExercise);
        }
        
        if (elements.continueButton) {
            elements.continueButton.addEventListener('click', completeExercise);
        }
        
        console.log('ExerciseCore inicializado correctamente');
    }

    // Iniciar ejercicio
    function startExercise() {
        console.log('Iniciando ejercicio desde Core');
        
        // Ocultar pantalla de inicio
        if (elements.startScreen) elements.startScreen.style.display = 'none';
        
        // Mostrar área de ejercicio
        if (elements.displayArea) elements.displayArea.style.display = 'block';
        
        // Resetear estado
        resetState();
        
        // Delegar a la categoría específica
        const categoria = window.EXERCISE_CONFIG.categoria;
        console.log('Delegando a categoría:', categoria);
        
        switch(categoria) {
            case 'EL':
                if (typeof ELExercises !== 'undefined') {
                    ELExercises.start();
                } else {
                    console.error('Módulo EL no encontrado');
                }
                break;
            case 'EO':
                if (typeof EOExercises !== 'undefined') {
                    EOExercises.start();
                } else {
                    console.error('Módulo EO no encontrado');
                }
                break;
            case 'EPM':
                if (typeof EPMExercises !== 'undefined') {
                    EPMExercises.start();
                } else {
                    console.error('Módulo EPM no encontrado');
                }
                break;
            case 'EVM':
                if (typeof EVMExercises !== 'undefined') {
                    EVMExercises.start();
                } else {
                    console.error('Módulo EVM no encontrado');
                }
                break;
            case 'EMD':
                if (typeof EMDExercises !== 'undefined') {
                    EMDExercises.start();
                } else {
                    console.error('Módulo EMD no encontrado');
                }
                break;
            default:
                console.error('Categoría desconocida:', categoria);
        }
    }

    // Resetear estado
    function resetState() {
        state.currentStep = 0;
        state.correctAnswers = 0;
        state.currentAttempt = 0;
        state.isRunning = true;
        state.waitingForInput = false;
        state.currentQuestionIndex = 0;
        
        // Limpiar cualquier intervalo anterior
        if (state.interval) {
            clearInterval(state.interval);
            state.interval = null;
        }
    }

    // Obtener velocidad según nivel
    function getSpeedByLevel() {
        const baseSpeed = window.EXERCISE_CONFIG.configuracion.tiempo_display || 
                         window.EXERCISE_CONFIG.configuracion.tiempo_fijacion || 
                         1000;
        return Math.max(200, baseSpeed);
    }

    // Actualizar progreso
    function updateProgress() {
        let percentage;
        let text = '';
        
        if (window.EXERCISE_CONFIG.categoria === 'EMD') {
            percentage = (state.currentAttempt / state.totalAttempts) * 100;
            text = `Intento ${state.currentAttempt} de ${state.totalAttempts}`;
        } else if (window.EXERCISE_CONFIG.categoria === 'EVM' || window.EXERCISE_CONFIG.categoria === 'EO') {
            if (state.currentStep < state.totalSteps) {
                percentage = (state.currentStep / state.totalSteps) * 100;
                text = `Elemento ${state.currentStep} de ${state.totalSteps}`;
            } else {
                percentage = 100;
                text = 'Respondiendo preguntas...';
            }
        } else {
            percentage = (state.currentStep / state.totalSteps) * 100;
            text = `Paso ${state.currentStep} de ${state.totalSteps}`;
        }
        
        if (elements.progressBar) {
            elements.progressBar.style.width = percentage + '%';
        }
        
        if (elements.progressText) {
            elements.progressText.textContent = text;
        }
    }

    // Mostrar resultados
    function showResults() {
        console.log('Mostrando resultados desde Core');
        
        // Limpiar intervalo si existe
        if (state.interval) {
            clearInterval(state.interval);
            state.interval = null;
        }
        
        // Ocultar área de ejercicio
        if (elements.displayArea) elements.displayArea.style.display = 'none';
        
        // Mostrar pantalla de resultados
        if (elements.resultsScreen) {
            elements.resultsScreen.style.display = 'block';
            
            // Actualizar contadores
            const totalQuestions = state.totalQuestions || state.totalAttempts;
            const incorrectAnswers = totalQuestions - state.correctAnswers;
            
            const correctCountEl = document.getElementById('correct-count');
            const incorrectCountEl = document.getElementById('incorrect-count');
            
            if (correctCountEl) correctCountEl.textContent = state.correctAnswers;
            if (incorrectCountEl) incorrectCountEl.textContent = incorrectAnswers;
            
            // Mostrar mensaje de tiempo para ejercicios EPM
            if (window.EXERCISE_CONFIG && window.EXERCISE_CONFIG.categoria === "EPM") {
                showEPMTimeMessage();
            }
        }
    }

    // Completar ejercicio
    function completeExercise() {
        console.log('Completando ejercicio desde Core');
        
        // Limpiar intervalo si existe
        if (state.interval) {
            clearInterval(state.interval);
            state.interval = null;
        }
        
        state.isRunning = false;
        
        // Ocultar pantallas anteriores
        if (elements.displayArea) elements.displayArea.style.display = 'none';
        if (elements.resultsScreen) elements.resultsScreen.style.display = 'none';
        
        // Mostrar pantalla de finalización
        if (elements.completionScreen) elements.completionScreen.style.display = 'block';
        
        // Marcar como completado en el servidor
        markAsCompleted();
    }

    // Marcar como completado en el servidor
    function markAsCompleted() {
        const csrfToken = getCsrfToken();
        
        if (!csrfToken) {
            console.error('No se pudo obtener el token CSRF');
            return;
        }
        
        fetch(window.EXERCISE_CONFIG.completarUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({
                'ejercicio_id': window.EXERCISE_CONFIG.ejercicio_id,
                'tiempo_ms': '0'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Ejercicio marcado como completado');
                if (data.desbloqueado) {
                    setTimeout(() => alert('¡' + data.desbloqueado + '!'), 1000);
                }
            } else {
                console.error('Error al marcar ejercicio como completado:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    // Obtener token CSRF
    function getCsrfToken() {
        let token = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (token) return token.value;
        
        token = document.querySelector('meta[name="csrf-token"]');
        if (token) return token.content;
        
        const name = 'csrftoken=';
        const cookies = decodeURIComponent(document.cookie).split(';');
        
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length);
            }
        }
        
        console.warn('CSRF token no encontrado');
        return '';
    }

    // Generar secuencia de memoria (para EO y EVM)
    function generateMemorySequence(items) {
        const sequence = [];
        const usedItems = [];
        
        // Elegir 9 elementos aleatorios
        for (let i = 0; i < 9; i++) {
            let item;
            do {
                item = items[Math.floor(Math.random() * items.length)];
            } while (usedItems.includes(item));
            usedItems.push(item);
            sequence.push(item);
        }
        
        // Repetir uno aleatorio
        const repeatedItem = usedItems[Math.floor(Math.random() * usedItems.length)];
        sequence.push(repeatedItem);
        
        // Mezclar secuencia
        for (let i = sequence.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [sequence[i], sequence[j]] = [sequence[j], sequence[i]];
        }
        
        // Guardar información para preguntas
        state.repeatedItem = repeatedItem;
        state.missingItem = items.find(item => !usedItems.includes(item));
        
        return sequence;
    }

    // Mover objeto aleatoriamente (para EO)
    function moveObjectRandomly(container, object) {
        const objectSize = 20; // Tamaño del objeto
        
        const maxX = container.offsetWidth - objectSize;
        const maxY = container.offsetHeight - objectSize;
        
        const x = Math.random() * maxX;
        const y = Math.random() * maxY;
        
        object.style.left = x + 'px';
        object.style.top = y + 'px';
    }

    // Crear opciones de respuesta
    function createAnswerOptions(allItems, correctAnswer, container, onSelect) {
        container.innerHTML = '';
        
        // Crear 4 opciones aleatorias incluyendo la correcta
        const options = [correctAnswer];
        while (options.length < 4) {
            const randomItem = allItems[Math.floor(Math.random() * allItems.length)];
            if (!options.includes(randomItem)) {
                options.push(randomItem);
            }
        }
        
        // Mezclar opciones
        for (let i = options.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [options[i], options[j]] = [options[j], options[i]];
        }
        
        // Crear contenedor grid 2x2
        const gridContainer = document.createElement('div');
        gridContainer.className = 'answer-options-grid';
        gridContainer.style.cssText = 'display: grid; grid-template-columns: 1fr; gap: 0; max-width: 500px; margin: 0 auto; width: 100%; place-items: center;';
        
        // Crear botones
        options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary';
            button.textContent = option;
            button.style.cssText = 'min-height: 60px; width: 100%; font-size: 1rem;';
            button.onclick = () => onSelect(option, correctAnswer, button);
            
            gridContainer.appendChild(button);
        });
        
        container.appendChild(gridContainer);
    }

    // Mostrar feedback de respuesta
    function showAnswerFeedback(selectedButton, isCorrect, feedbackContainer) {
        // Desmarcar otros botones - buscar el contenedor grid
        const container = selectedButton.closest('.answer-options-grid');
        if (container) {
            container.querySelectorAll('.btn').forEach(btn => {
                btn.classList.remove('btn-primary', 'btn-success', 'btn-danger');
                btn.classList.add('btn-outline-primary');
                btn.disabled = true;
            });
        }
        
        // Marcar respuesta seleccionada
        selectedButton.classList.remove('btn-outline-primary');
        selectedButton.classList.add(isCorrect ? 'btn-success' : 'btn-danger');
        
        // Actualizar contador de respuestas correctas
        if (isCorrect) state.correctAnswers++;
        
        // Mostrar feedback
        if (feedbackContainer) {
            feedbackContainer.innerHTML = `<div class="alert ${isCorrect ? 'alert-success' : 'alert-danger'}">${isCorrect ? '¡Correcto!' : '¡Incorrecto!'}</div>`;
            feedbackContainer.style.display = 'block';
        }
    }

    // Resetear botones para siguiente pregunta
    function resetAnswerButtons(container) {
        container.querySelectorAll('.btn').forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('btn-success', 'btn-danger');
            btn.classList.add('btn-outline-primary');
        });
    }


    // Iniciar cronómetro para pregunta EPM
    function startQuestionTimer() {
        state.questionStartTime = Date.now();
    }
    
    // Finalizar cronómetro y registrar tiempo de respuesta EPM
    function endQuestionTimer() {
        if (state.questionStartTime > 0) {
            const responseTime = Date.now() - state.questionStartTime;
            state.totalResponseTime += responseTime;
            state.questionStartTime = 0;
            return responseTime;
        }
        return 0;
    }
    
    // Mostrar mensaje de tiempo EPM
    function showEPMTimeMessage() {
        console.log('=== EPM Time Message Debug ===');
        console.log('Total response time:', state.totalResponseTime);
        console.log('Total questions:', state.totalQuestions);
        console.log('Current step:', state.currentStep);
        
        // Usar currentStep como fallback si totalQuestions no está definido
        const totalQuestions = state.totalQuestions || state.currentStep || 20;
        const avgTime = state.totalResponseTime > 0 ? (state.totalResponseTime / totalQuestions) : 0;
        
        console.log('Calculated average time:', avgTime, 'ms');
        
        let message = '';
        let color = '#E76F51'; // Color por defecto
        
        if (avgTime <= 0) {
            message = 'No se pudo calcular el tiempo';
            color = '#6B7280';
        } else if (avgTime > 2500) {
            message = '¿Pero a qué juegas?';
            color = '#DC2626';
        } else if (avgTime > 2000) {
            message = 'Tortuga coja';
            color = '#EA580C';
        } else if (avgTime > 1500) {
            message = 'Tortuga';
            color = '#F59E0B';
        } else if (avgTime > 1200) {
            message = 'Tranquilón';
            color = '#F4A261';
        } else if (avgTime > 1000) {
            message = 'Pasable';
            color = '#84CC16';
        } else if (avgTime > 900) {
            message = 'Normal';
            color = '#22C55E';
        } else if (avgTime > 800) {
            message = 'Bien';
            color = '#10B981';
        } else if (avgTime > 700) {
            message = 'Bastante bien';
            color = '#06B6D4';
        } else if (avgTime > 600) {
            message = 'Muy bien';
            color = '#3B82F6';
        } else if (avgTime > 500) {
            message = 'Excelente';
            color = '#8B5CF6';
        } else {
            message = '¿Eres Ramón Campayo?';
            color = '#EC4899';
        }
        
        console.log('Selected message:', message);
        console.log('Color:', color);
        
        // Crear y mostrar el mensaje
        const timeMessageEl = document.createElement('div');
        timeMessageEl.className = 'epm-time-message';
        timeMessageEl.style.background = `linear-gradient(135deg, ${color}, ${color}dd)`;
        timeMessageEl.innerHTML = `
            <div style="font-size: 1.5rem; margin-bottom: 8px; font-weight: 700;">${message}</div>
            <div style="font-size: 1rem; opacity: 0.9;">Tiempo promedio: ${Math.round(avgTime)}ms</div>
            <div style="font-size: 0.875rem; opacity: 0.7; margin-top: 4px;">Respuestas totales: ${totalQuestions}</div>
        `;
        
        // Buscar el contenedor de resultados
        let targetContainer = null;
        
        if (elements.resultsScreen) {
            // Intentar diferentes selectores para encontrar el contenedor adecuado
            targetContainer = elements.resultsScreen.querySelector('.text-center') ||
                            elements.resultsScreen.querySelector('.container') ||
                            elements.resultsScreen.querySelector('div') ||
                            elements.resultsScreen;
        }
        
        if (targetContainer) {
            targetContainer.appendChild(timeMessageEl);
            console.log('✓ Message element added to results screen');
            
            // Agregar animación de entrada
            timeMessageEl.style.opacity = '0';
            timeMessageEl.style.transform = 'translateY(20px)';
            timeMessageEl.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                timeMessageEl.style.opacity = '1';
                timeMessageEl.style.transform = 'translateY(0)';
            }, 100);
            
        } else {
            console.error('✗ No se pudo encontrar contenedor para el mensaje');
            console.log('Available elements:', elements);
            
            // Como fallback, intentar agregar al body
            document.body.appendChild(timeMessageEl);
            console.log('Message added to body as fallback');
        }
    }

    // API pública
    return {
        init: init,
        getState: () => state,
        setState: (newState) => Object.assign(state, newState),
        getElements: () => elements,
        getSpeedByLevel: getSpeedByLevel,
        updateProgress: updateProgress,
        showResults: showResults,
        completeExercise: completeExercise,
        generateMemorySequence: generateMemorySequence,
        moveObjectRandomly: moveObjectRandomly,
        createAnswerOptions: createAnswerOptions,
        showAnswerFeedback: showAnswerFeedback,
        resetAnswerButtons: resetAnswerButtons,
        startQuestionTimer: startQuestionTimer,
        endQuestionTimer: endQuestionTimer,
        showEPMTimeMessage: showEPMTimeMessage
    };

})();
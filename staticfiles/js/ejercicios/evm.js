/**
 * EVMExercises - Ejercicios de Entrenamiento de Velocidad de Memorización
 * EVM1: Secuencias de frutas
 * EVM2: Secuencias de meses
 * EVM3: Secuencias de países
 * EVM4: Secuencias de nombres
 */

window.EVMExercises = (function() {
    
    // Datos específicos para ejercicios EVM
    const DATA = {
        EVM1_ITEMS: ['manzana', 'pera', 'plátano', 'naranja', 'uva', 'fresa', 'melocotón', 'sandía', 'melón', 'piña', 'kiwi'],
        EVM2_ITEMS: ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
        EVM3_ITEMS: ['España', 'Francia', 'Italia', 'Alemania', 'Portugal', 'Inglaterra', 'Suiza', 'Austria', 'Holanda', 'Bélgica', 'Suecia'],
        EVM4_ITEMS: ['Juan', 'María', 'Pedro', 'Ana', 'Luis', 'Carmen', 'José', 'Isabel', 'Antonio', 'Pilar', 'Francisco']
    };

    // Variables para el estado específico de EVM
    let currentQuestionNumber = 1;
    let itemType = '';
    let allItems = [];
    let answerSubmitted = false; // Flag para prevenir respuestas múltiples
    let questionsShown = false; // Flag para prevenir múltiples llamadas a showQuestions
    let currentQuestionShown = 0; // Número de pregunta actualmente mostrada
    let isTransitioning = false; // Flag para prevenir transiciones múltiples
    let sequenceCompleted = false; // Flag para marcar cuando la secuencia terminó
    let intervalCleared = false; // Flag para asegurar que el intervalo solo se limpia una vez

    // Inicializar el contenedor de ejercicio
    function initContainer() {
        const container = ExerciseCore.getElements().exerciseContainer;
        if (!container) return null;

        container.innerHTML = `
            <div class="text-center py-4">
                <!-- Contenedor para mostrar la secuencia -->
                <div id="evm-display-container">
                    <h6 class="text-muted mb-3">Memoriza la secuencia</h6>
                    <div id="evm-display" class="display-4 fw-bold text-primary mb-4" style="min-height: 120px; display: flex; align-items: center; justify-content: center;  border-radius: 8px;  font-family: Arial, sans-serif;">
                        
                    </div>
                    <div class="mt-3">
                        <small class="text-muted">Elemento <span id="evm-counter">0</span>/10</small>
                    </div>
                </div>
                
                <!-- Contenedor para las preguntas -->
                <div id="evm-questions" style="display: none;">
                    <div class="mt-4">
                        <h5 class="mb-3">Pregunta <span id="evm-question-number">1</span>/2</h5>
                        <p id="evm-question-text" class="mb-4 h6"></p>
                        <div id="evm-options" class="row g-3 justify-content-center mb-4"></div>
                        <div id="evm-feedback" class="mb-3" style="display: none;"></div>
                    </div>
                </div>
            </div>
        `;

        return container;
    }

    // Función principal de inicio
    function start() {
        console.log('Iniciando ejercicio EVM:', window.EXERCISE_CONFIG.codigo);
        
        // Resetear TODOS los flags
        answerSubmitted = false;
        questionsShown = false;
        currentQuestionShown = 0;
        isTransitioning = false;
        sequenceCompleted = false;
        intervalCleared = false;
        
        const container = initContainer();
        if (!container) {
            console.error('No se pudo inicializar el contenedor EVM');
            return;
        }

        // Determinar tipo de ejercicio y elementos
        const codigo = window.EXERCISE_CONFIG.codigo;
        if (codigo.includes('EVM1')) {
            allItems = DATA.EVM1_ITEMS;
            itemType = 'fruta';
        } else if (codigo.includes('EVM2')) {
            allItems = DATA.EVM2_ITEMS;
            itemType = 'mes';
        } else if (codigo.includes('EVM3')) {
            allItems = DATA.EVM3_ITEMS;
            itemType = 'país';
        } else if (codigo.includes('EVM4')) {
            allItems = DATA.EVM4_ITEMS;
            itemType = 'nombre';
        } else {
            console.error('Ejercicio EVM desconocido:', codigo);
            return;
        }

        // Resetear variables específicas
        currentQuestionNumber = 1;
        
        // Esperar un momento y comenzar
        setTimeout(() => {
            startSequence();
        }, 500);
    }

    // Iniciar la secuencia de elementos
    function startSequence() {
        const display = document.getElementById('evm-display');
        const counter = document.getElementById('evm-counter');
        const speed = ExerciseCore.getSpeedByLevel();
        const state = ExerciseCore.getState();
        
        // Generar secuencia con repetición y elemento faltante
        const sequence = ExerciseCore.generateMemorySequence(allItems);
        state.totalSteps = sequence.length;
        state.currentStep = 0;
        
        console.log('Secuencia generada:', sequence);
        console.log('Elemento repetido:', state.repeatedItem);
        console.log('Elemento faltante:', state.missingItem);
        
        display.textContent = 'Comenzando...';
        
        state.interval = setInterval(() => {
            if (state.currentStep >= state.totalSteps) {
                // CRÍTICO: Prevenir múltiples ejecuciones de esta sección
                if (sequenceCompleted) {
                    return;
                }
                sequenceCompleted = true;
                
                // IMPORTANTE: Detener el intervalo INMEDIATAMENTE
                if (state.interval && !intervalCleared) {
                    clearInterval(state.interval);
                    intervalCleared = true;
                    state.interval = null;
                    console.log('Intervalo detenido correctamente');
                }
                
                // Terminar secuencia y mostrar preguntas
                setTimeout(() => {
                    showQuestions();
                }, 500);
                return;
            }
            
            const item = sequence[state.currentStep];
            display.textContent = item;
            counter.textContent = state.currentStep + 1;
            
            ExerciseCore.updateProgress();
            state.currentStep++;
        }, speed);
    }

    // Mostrar las preguntas
    function showQuestions() {
        // Prevenir múltiples llamadas
        if (questionsShown) {
            console.log('Preguntas ya mostradas, ignorando llamada adicional');
            return;
        }
        
        questionsShown = true;
        console.log('Mostrando preguntas EVM');
        
        // Ocultar secuencia y mostrar preguntas
        document.getElementById('evm-display-container').style.display = 'none';
        document.getElementById('evm-questions').style.display = 'block';
        
        const state = ExerciseCore.getState();
        state.totalQuestions = 2;
        currentQuestionNumber = 1;
        
        // Resetear flag de respuesta
        answerSubmitted = false;
        
        // Mostrar primera pregunta
        showQuestion(1, `¿Qué ${itemType} ha salido 2 veces?`, state.repeatedItem);
    }

    // Mostrar una pregunta específica
    function showQuestion(questionNum, questionText, correctAnswer) {
        // Prevenir que la misma pregunta se muestre múltiples veces
        if (currentQuestionShown === questionNum) {
            console.log(`Pregunta ${questionNum} ya está siendo mostrada, ignorando llamada adicional`);
            return;
        }
        
        // Prevenir si estamos en transición
        if (isTransitioning) {
            console.log('En transición, ignorando llamada a showQuestion');
            return;
        }
        
        currentQuestionShown = questionNum;
        console.log(`Mostrando pregunta ${questionNum}:`, questionText, 'Respuesta correcta:', correctAnswer);
        
        // Resetear flag de respuesta para nueva pregunta
        answerSubmitted = false;
        
        document.getElementById('evm-question-number').textContent = questionNum;
        document.getElementById('evm-question-text').textContent = questionText;
        
        const optionsContainer = document.getElementById('evm-options');
        const feedbackContainer = document.getElementById('evm-feedback');
        
        // Ocultar feedback anterior
        feedbackContainer.style.display = 'none';
        feedbackContainer.innerHTML = '';
        
        // Limpiar opciones anteriores completamente
        optionsContainer.innerHTML = '';
        
        // CRÍTICO: Esperar un momento antes de crear las nuevas opciones
        // Esto previene que se ejecute createAnswerOptions mientras hay opciones antiguas
        setTimeout(() => {
            // Verificar nuevamente que no estamos en transición
            if (isTransitioning) {
                console.log('En transición durante creación de opciones, abortando');
                return;
            }
            
            // Crear opciones de respuesta UNA SOLA VEZ
            ExerciseCore.createAnswerOptions(
                allItems, 
                correctAnswer, 
                optionsContainer, 
                (selectedAnswer, correctAnswer, selectedButton) => {
                    handleAnswer(selectedAnswer, correctAnswer, selectedButton, questionNum);
                }
            );
        }, 100);
    }

    // Manejar respuesta del usuario
    function handleAnswer(selectedAnswer, correctAnswer, selectedButton, questionNum) {
        // Prevenir respuestas múltiples
        if (answerSubmitted) {
            console.log('Respuesta ya enviada, ignorando clic adicional');
            return;
        }
        
        // Prevenir si estamos en transición
        if (isTransitioning) {
            console.log('En transición, ignorando respuesta');
            return;
        }
        
        answerSubmitted = true;
        isTransitioning = true;
        console.log(`Respuesta para pregunta ${questionNum}:`, selectedAnswer, 'vs', correctAnswer);
        
        // Deshabilitar todos los botones inmediatamente
        const optionsContainer = document.getElementById('evm-options');
        const allButtons = optionsContainer.querySelectorAll('button');
        allButtons.forEach(btn => {
            btn.disabled = true;
            btn.style.cursor = 'not-allowed';
            btn.style.pointerEvents = 'none'; // Prevenir cualquier interacción
        });
        
        const isCorrect = selectedAnswer === correctAnswer;
        const feedbackContainer = document.getElementById('evm-feedback');
        
        // Mostrar feedback visual
        ExerciseCore.showAnswerFeedback(selectedButton, isCorrect, feedbackContainer);
        
        // Continuar después del feedback
        setTimeout(() => {
            isTransitioning = false; // Permitir transiciones nuevamente
            
            if (questionNum === 1) {
                // Mostrar segunda pregunta
                prepareSecondQuestion();
            } else {
                // Terminar ejercicio
                ExerciseCore.showResults();
            }
        }, 2000);
    }

    // Preparar segunda pregunta
    function prepareSecondQuestion() {
        console.log('Preparando segunda pregunta');
        
        // Prevenir si ya estamos en transición
        if (isTransitioning) {
            console.log('Ya en transición, ignorando prepareSecondQuestion');
            return;
        }
        
        const optionsContainer = document.getElementById('evm-options');
        const feedbackContainer = document.getElementById('evm-feedback');
        const state = ExerciseCore.getState();
        
        // Ocultar feedback
        feedbackContainer.style.display = 'none';
        feedbackContainer.innerHTML = '';
        
        // Limpiar completamente las opciones anteriores
        optionsContainer.innerHTML = '';
        
        // Resetear el flag de pregunta mostrada para permitir pregunta 2
        currentQuestionShown = 0;
        
        // Resetear flags
        answerSubmitted = false;
        
        // Mostrar segunda pregunta
        currentQuestionNumber = 2;
        showQuestion(2, `¿Qué ${itemType} no ha salido?`, state.missingItem);
    }

    // API pública
    return {
        start: start
    };

})();
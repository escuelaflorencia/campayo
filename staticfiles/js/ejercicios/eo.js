/**
 * EOExercises - Ejercicios de Entrenamiento del Ojo
 * EO1: Seguimiento de círculos
 * EO2: Seguimiento de números con memoria
 * EO3: Seguimiento de palabras con memoria
 * EO4: Seguimiento de pares de palabras con memoria
 */

window.EOExercises = (function() {
    
    // Datos específicos para ejercicios EO
    const DATA = {
        EO2_NUMBERS: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        EO3_WORDS: ['casa', 'perro', 'gato', 'mesa', 'silla', 'libro', 'agua', 'fuego', 'tierra', 'aire', 'luz'],
        EO4_WORD_PAIRS: [
            'casa blanca', 'perro negro', 'gato pequeño', 'mesa grande', 'silla cómoda',
            'libro nuevo', 'agua fría', 'fuego caliente', 'tierra húmeda', 'aire puro'
        ]
    };

    // Variables para el estado específico de EO
    let currentQuestionNumber = 1;
    let questionType = '';
    let allItems = [];
    let answerSubmitted = false; // Flag para prevenir respuestas múltiples

    // Inicializar el contenedor de ejercicio
    function initContainer() {
        const container = ExerciseCore.getElements().exerciseContainer;
        if (!container) return null;

        const codigo = window.EXERCISE_CONFIG.codigo;
        let html = '';

        if (codigo.includes('EO1')) {
            html = `
                <div class="text-center py-4">
                    <h6 class="text-muted mb-3">Sigue el círculo con la vista</h6>
                    <div id="eo-container" style="position: relative; height: 350px;  border-radius: 8px;  margin: 20px auto; max-width: 600px;">
                        <div id="moving-object" style="position: absolute; width: 20px; height: 20px; background: #007bff; border-radius: 50%; display: none; transition: all 0.1s ease;"></div>
                    </div>
                </div>
            `;
        } else {
            html = `
                <div class="text-center py-4">
                    <h6 class="text-muted mb-3">Memoriza qué elementos aparecen</h6>
                    
                    <!-- Contenedor para la secuencia -->
                    <div id="eo-sequence-container">
                        <div id="eo-container" style="position: relative; height: 350px;  border-radius: 8px;  margin: 20px auto; max-width: 600px;">
                            <div id="moving-element" style="position: absolute; font-size: 24px; font-weight: bold; color: #007bff; display: none; user-select: none;"></div>
                        </div>
                    </div>
                    
                    <!-- Contenedor para las preguntas -->
                    <div id="eo-questions" style="display: none;">
                        <div class="mt-4">
                            <h5 class="mb-3">Pregunta <span id="eo-question-number">1</span>/2</h5>
                            <p id="eo-question-text" class="mb-4 h6"></p>
                            <div id="eo-options" class="d-flex flex-wrap justify-content-center gap-3 mb-4" style="max-width: 400px; margin: 40px auto; padding: 30px;"></div>
                            <div id="eo-feedback" class="mb-3" style="display: none;"></div>
                        </div>
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
        return container;
    }

    // Función principal de inicio
    function start() {
        console.log('Iniciando ejercicio EO:', window.EXERCISE_CONFIG.codigo);
        
        // Resetear flag de respuesta
        answerSubmitted = false;
        
        const container = initContainer();
        if (!container) {
            console.error('No se pudo inicializar el contenedor EO');
            return;
        }

        const codigo = window.EXERCISE_CONFIG.codigo;
        
        setTimeout(() => {
            if (codigo.includes('EO1')) {
                startEO1();
            } else if (codigo.includes('EO2')) {
                startEOWithMemory(DATA.EO2_NUMBERS, '¿Qué número se ha repetido?', '¿Qué número no ha salido?');
            } else if (codigo.includes('EO3')) {
                startEOWithMemory(DATA.EO3_WORDS, '¿Qué palabra se ha repetido?', '¿Qué palabra no ha salido?');
            } else if (codigo.includes('EO4')) {
                startEOWithMemory(DATA.EO4_WORD_PAIRS, '¿Qué par de palabras se ha repetido?', '¿Qué par de palabras no ha salido?');
            } else {
                console.error('Ejercicio EO desconocido:', codigo);
            }
        }, 100);
    }

    // EO1: Seguimiento de círculos
    function startEO1() {
        const container = document.getElementById('eo-container');
        const movingObject = document.getElementById('moving-object');
        const speed = ExerciseCore.getSpeedByLevel();
        const state = ExerciseCore.getState();
        
        if (!container || !movingObject) {
            console.error('Elementos EO1 no encontrados');
            return;
        }

        movingObject.style.display = 'block';
        
        // Posicionar inicialmente
        ExerciseCore.moveObjectRandomly(container, movingObject);
        
        state.interval = setInterval(() => {
            if (state.currentStep >= state.totalSteps) {
                clearInterval(state.interval);
                state.interval = null;
                ExerciseCore.completeExercise();
                return;
            }
            
            ExerciseCore.moveObjectRandomly(container, movingObject);
            ExerciseCore.updateProgress();
            state.currentStep++;
        }, speed);
    }

    // EO2, EO3, EO4: Ejercicios con memoria
    function startEOWithMemory(items, question1, question2) {
        allItems = items;
        questionType = question1;
        currentQuestionNumber = 1;
        
        const container = document.getElementById('eo-container');
        const movingElement = document.getElementById('moving-element');
        const speed = ExerciseCore.getSpeedByLevel();
        const state = ExerciseCore.getState();
        
        if (!container || !movingElement) {
            console.error('Elementos EO con memoria no encontrados');
            return;
        }

        // Generar secuencia: 10 elementos, uno repetido, uno faltante
        const sequence = ExerciseCore.generateMemorySequence(items);
        state.totalSteps = sequence.length;
        movingElement.style.display = 'block';
        
        console.log('Secuencia EO generada:', sequence);
        console.log('Elemento repetido:', state.repeatedItem);
        console.log('Elemento faltante:', state.missingItem);
        
        state.interval = setInterval(() => {
            if (state.currentStep >= state.totalSteps) {
                // IMPORTANTE: Detener el intervalo
                clearInterval(state.interval);
                state.interval = null;
                
                setTimeout(() => {
                    showQuestions(question1, question2);
                }, 500);
                return;
            }
            
            const item = sequence[state.currentStep];
            movingElement.textContent = item;
            ExerciseCore.moveObjectRandomly(container, movingElement);
            
            ExerciseCore.updateProgress();
            state.currentStep++;
        }, speed);
    }

    // Mostrar las preguntas
    function showQuestions(question1, question2) {
        console.log('Mostrando preguntas EO');
        
        // Ocultar contenedor de secuencia
        document.getElementById('eo-sequence-container').style.display = 'none';
        document.getElementById('eo-questions').style.display = 'block';
        
        const state = ExerciseCore.getState();
        state.totalQuestions = 2;
        currentQuestionNumber = 1;
        
        // Resetear flag de respuesta
        answerSubmitted = false;
        
        // Mostrar primera pregunta
        showQuestion(1, question1, state.repeatedItem);
    }

    // Mostrar una pregunta específica
    function showQuestion(questionNum, questionText, correctAnswer) {
        console.log(`Mostrando pregunta EO ${questionNum}:`, questionText, 'Respuesta correcta:', correctAnswer);
        
        // Resetear flag de respuesta para nueva pregunta
        answerSubmitted = false;
        
        document.getElementById('eo-question-number').textContent = questionNum;
        document.getElementById('eo-question-text').textContent = questionText;
        
        const optionsContainer = document.getElementById('eo-options');
        const feedbackContainer = document.getElementById('eo-feedback');
        
        // Ocultar feedback anterior
        feedbackContainer.style.display = 'none';
        feedbackContainer.innerHTML = '';
        
        // Limpiar opciones anteriores completamente
        optionsContainer.innerHTML = '';
        
        // Crear opciones de respuesta
        ExerciseCore.createAnswerOptions(
            allItems, 
            correctAnswer, 
            optionsContainer, 
            (selectedAnswer, correctAnswer, selectedButton) => {
                handleAnswer(selectedAnswer, correctAnswer, selectedButton, questionNum);
            }
        );
        
        // Aplicar estilos flexbox para layout 2x2
        setTimeout(() => {
            const optionsContainer = document.getElementById('eo-options');
            if (optionsContainer) {
                const buttons = optionsContainer.querySelectorAll('button');
                buttons.forEach(button => {
                    button.style.width = '100%';
                    button.style.margin = '8px';
                    button.style.flexBasis = 'calc(50% - 16px)';
                });
            }
        }, 10);
    }

    // Manejar respuesta del usuario
    function handleAnswer(selectedAnswer, correctAnswer, selectedButton, questionNum) {
        // Prevenir respuestas múltiples
        if (answerSubmitted) {
            console.log('Respuesta ya enviada, ignorando clic adicional');
            return;
        }
        
        answerSubmitted = true;
        console.log(`Respuesta EO para pregunta ${questionNum}:`, selectedAnswer, 'vs', correctAnswer);
        
        // Deshabilitar todos los botones
        const optionsContainer = document.getElementById('eo-options');
        const allButtons = optionsContainer.querySelectorAll('button');
        allButtons.forEach(btn => {
            btn.disabled = true;
            btn.style.cursor = 'not-allowed';
        });
        
        const isCorrect = selectedAnswer === correctAnswer;
        const feedbackContainer = document.getElementById('eo-feedback');
        
        // Mostrar feedback visual
        ExerciseCore.showAnswerFeedback(selectedButton, isCorrect, feedbackContainer);
        
        // Continuar después del feedback
        setTimeout(() => {
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
        console.log('Preparando segunda pregunta EO');
        
        const optionsContainer = document.getElementById('eo-options');
        const feedbackContainer = document.getElementById('eo-feedback');
        const state = ExerciseCore.getState();
        
        // Ocultar feedback
        feedbackContainer.style.display = 'none';
        
        // Limpiar completamente las opciones anteriores
        optionsContainer.innerHTML = '';
        
        // Resetear botones si existe la función
        if (typeof ExerciseCore.resetAnswerButtons === 'function') {
            ExerciseCore.resetAnswerButtons(optionsContainer);
        }
        
        // Mostrar segunda pregunta
        currentQuestionNumber = 2;
        showQuestion(2, '¿Qué elemento no ha salido?', state.missingItem);
    }

    // API pública
    return {
        start: start
    };

})();
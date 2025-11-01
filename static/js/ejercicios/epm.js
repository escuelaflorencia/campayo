/**
 * EPMExercises - Ejercicios de Entrenamiento de Procesamiento Mental
 * EPM1: Verificación de artículo-sustantivo
 * EPM2: Verificación de sujeto-verbo
 * EPM3: Verificación gramatical completa
 */

window.EPMExercises = (function() {
    
    // Datos específicos para ejercicios EPM
    const DATA = {
        // EPM1 - Artículo + Sustantivo
        EPM1_PHRASES: [
            {text: 'el casa', correct: false},
            {text: 'la mesa', correct: true},
            {text: 'un perro', correct: true},
            {text: 'una problema', correct: false},
            {text: 'los niños', correct: true},
            {text: 'las arboles', correct: false},
            {text: 'el agua', correct: true},
            {text: 'la mano', correct: true},
            {text: 'un mujer', correct: false},
            {text: 'una persona', correct: true},
            {text: 'los libros', correct: true},
            {text: 'las casas', correct: true},
            {text: 'el mapa', correct: true},
            {text: 'la problema', correct: false},
            {text: 'un día', correct: true},
            {text: 'una tiempo', correct: false},
            {text: 'los flores', correct: false},
            {text: 'las manos', correct: true},
            {text: 'el radio', correct: true},
            {text: 'la radio', correct: true}
        ],
        
        // EPM2 - Sujeto + Verbo
        EPM2_PHRASES: [
            {text: 'Él corre', correct: true},
            {text: 'Ellos corre', correct: false},
            {text: 'Nosotros corremos', correct: true},
            {text: 'Tú corren', correct: false},
            {text: 'Yo como', correct: true},
            {text: 'Ella comen', correct: false},
            {text: 'Vosotros coméis', correct: true},
            {text: 'Usted corren', correct: false},
            {text: 'María estudia', correct: true},
            {text: 'Los niños estudia', correct: false},
            {text: 'El perro ladra', correct: true},
            {text: 'Los perros ladra', correct: false},
            {text: 'Mis amigos vienen', correct: true},
            {text: 'Tu hermano vienen', correct: false},
            {text: 'Las flores crecen', correct: true},
            {text: 'La flor crecen', correct: false},
            {text: 'Usted tiene', correct: true},
            {text: 'Ustedes tiene', correct: false},
            {text: 'Ellas cantan', correct: true},
            {text: 'Ella cantan', correct: false}
        ],
        
        // EPM3 - Frases completas
        EPM3_PHRASES: [
            {text: 'El niño come manzanas rojas', correct: true},
            {text: 'La niños come manzanas rojas', correct: false},
            {text: 'Los estudiantes estudian mucho', correct: true},
            {text: 'El estudiantes estudian mucho', correct: false},
            {text: 'Mi hermana tiene un gato', correct: true},
            {text: 'Mi hermana tienen un gato', correct: false},
            {text: 'Las flores del jardín son hermosas', correct: true},
            {text: 'Las flores del jardín es hermosas', correct: false},
            {text: 'El profesor explica la lección', correct: true},
            {text: 'El profesor explican la lección', correct: false},
            {text: 'Nosotros vivimos en Madrid', correct: true},
            {text: 'Nosotros vive en Madrid', correct: false},
            {text: 'Tú escribes cartas importantes', correct: true},
            {text: 'Tú escriben cartas importantes', correct: false},
            {text: 'Ellos trabajan en la oficina', correct: true},
            {text: 'Ellos trabaja en la oficina', correct: false},
            {text: 'La música suena muy alta', correct: true},
            {text: 'La música suenan muy alta', correct: false},
            {text: 'Mis padres viajan frecuentemente', correct: true},
            {text: 'Mis padres viaja frecuentemente', correct: false}
        ]
    };

    // Inicializar el contenedor de ejercicio
    function initContainer() {
        const container = ExerciseCore.getElements().exerciseContainer;
        if (!container) return null;

        container.innerHTML = `
            <div class="text-center py-4">
                <h6 class="text-muted mb-4">¿Es gramaticalmente correcta?</h6>
                
                <div id="epm-display" class="display-5 fw-bold text-dark mb-4" style="min-height: 120px; display: flex; align-items: center; justify-content: center;  border-radius: 8px;  padding: 20px; line-height: 1.2;">
                    
                </div>
                
                <div id="epm-buttons" style="display: none;">
                    <button id="correct-btn" class="btn-exercise btn-exercise-lg me-4" style="min-width: 150px;">
                        <i class="bi bi-check-circle"></i> Correcto
                    </button>
                    <button id="incorrect-btn" class="btn-exercise-secondary btn-exercise-lg" style="min-width: 150px;">
                        <i class="bi bi-x-circle"></i> Incorrecto
                    </button>
                </div>
                
                <div class="mt-4">
                    <small class="text-muted">Frase <span id="epm-counter">0</span>/20</small>
                </div>
                
                <div id="epm-feedback" style="display: none; margin-top: 20px;">
                    <div id="epm-feedback-message" class="alert"></div>
                </div>
            </div>
        `;

        return container;
    }

    // Función principal de inicio
    function start() {
        console.log('Iniciando ejercicio EPM:', window.EXERCISE_CONFIG.codigo);
        
        const container = initContainer();
        if (!container) {
            console.error('No se pudo inicializar el contenedor EPM');
            return;
        }

        // Configurar estado inicial
        const state = ExerciseCore.getState();
        state.totalSteps = 20;
        state.currentStep = 0;
        state.totalQuestions = 20;  // Necesario para el cálculo de tiempo promedio
        state.totalResponseTime = 0;  // Acumulador de tiempo de respuestas
        state.correctAnswers = 0;  // Resetear respuestas correctas
        
        console.log('Estado inicial configurado:', {
            totalSteps: state.totalSteps,
            totalQuestions: state.totalQuestions,
            totalResponseTime: state.totalResponseTime
        });
        
        // Esperar un momento y comenzar
        setTimeout(() => {
            startEPM();
        }, 500);
    }

    // Iniciar ejercicio EPM
    function startEPM() {
        const display = document.getElementById('epm-display');
        const buttons = document.getElementById('epm-buttons');
        const correctBtn = document.getElementById('correct-btn');
        const incorrectBtn = document.getElementById('incorrect-btn');
        const counter = document.getElementById('epm-counter');
        
        if (!display || !buttons || !correctBtn || !incorrectBtn) {
            console.error('Elementos EPM no encontrados');
            return;
        }

        buttons.style.display = 'block';
        
        // Determinar qué tipo de frases usar
        let phrases;
        const codigo = window.EXERCISE_CONFIG.codigo;
        if (codigo.includes('EPM1')) {
            phrases = DATA.EPM1_PHRASES;
        } else if (codigo.includes('EPM2')) {
            phrases = DATA.EPM2_PHRASES;
        } else {
            phrases = DATA.EPM3_PHRASES;
        }
        
        function showNextPhrase() {
            const state = ExerciseCore.getState();
            
            if (state.currentStep >= state.totalSteps) {
                ExerciseCore.showResults();
                return;
            }
            
            const phrase = phrases[state.currentStep % phrases.length];
            display.textContent = phrase.text;
            counter.textContent = state.currentStep + 1;
            state.waitingForInput = true;
            
            
            // Iniciar cronómetro para medir tiempo de respuesta
            ExerciseCore.startQuestionTimer();
            // Habilitar botones
            correctBtn.disabled = false;
            incorrectBtn.disabled = false;
            
            const handleAnswer = (userAnswer) => {
                if (!state.waitingForInput) return;
                
                state.waitingForInput = false;
                
                // Registrar tiempo de respuesta
                ExerciseCore.endQuestionTimer();
                const isCorrect = userAnswer === phrase.correct;
                
                // Deshabilitar botones
                correctBtn.disabled = true;
                incorrectBtn.disabled = true;
                
                if (isCorrect) {
                    state.correctAnswers++;
                }
                
                showEPMFeedback(isCorrect);
                ExerciseCore.updateProgress();
                state.currentStep++;
                
                setTimeout(showNextPhrase, 1200);
            };
            
            // Configurar eventos (remover anteriores primero)
            correctBtn.onclick = null;
            incorrectBtn.onclick = null;
            
            correctBtn.onclick = () => handleAnswer(true);
            incorrectBtn.onclick = () => handleAnswer(false);
        }
        
        // Comenzar con la primera frase
        showNextPhrase();
    }

    // Mostrar feedback de respuesta
    function showEPMFeedback(isCorrect) {
        const feedback = document.getElementById('epm-feedback');
        const message = document.getElementById('epm-feedback-message');
        
        if (!feedback || !message) return;
        
        message.textContent = isCorrect ? '¡Correcto!' : '¡Incorrecto!';
        message.className = isCorrect ? 'alert alert-success' : 'alert alert-danger';
        feedback.style.display = 'block';
        
        setTimeout(() => {
            feedback.style.display = 'none';
        }, 1000);
    }

    // API pública
    return {
        start: start
    };

})();
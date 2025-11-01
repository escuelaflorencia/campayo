/**
 * EMDExercises - Ejercicios de Entrenamiento de Memoria Eidética
 * EMD1: Memorización de 2 dígitos
 * EMD2: Memorización de 4 dígitos
 * EMD3: Memorización de 6 dígitos
 */

window.EMDExercises = (function() {
    
    // Variables específicas para EMD
    let numberOfDigits = 2;
    let currentNumbers = [];
    let showingNumbers = false;

    // Inicializar el contenedor de ejercicio
    function initContainer() {
        const container = ExerciseCore.getElements().exerciseContainer;
        if (!container) return null;

        container.innerHTML = `
            <div class="text-center py-4">
                <!-- Contenedor para mostrar números -->
                <div id="emd-display-container">
                    <h6 class="text-muted mb-4">Memoriza los números</h6>
                    <div id="emd-display" class="display-3 fw-bold text-primary mb-4" style="font-family: 'Courier New', monospace; letter-spacing: 0.8em; min-height: 120px; display: flex; align-items: center; justify-content: center;  border-radius: 8px; ">
                        
                    </div>
                </div>
                
                <!-- Contenedor para introducir números -->
                <div id="emd-input-container" style="display: none;">
                    <h6 class="text-muted mb-4">Introduce los números</h6>
                    <div id="emd-inputs" class="d-flex gap-3 mb-4" style="justify-content:center !important">
                        <!-- Los inputs se generarán dinámicamente -->
                    </div>
                    <button id="emd-submit" class="btn-exercise btn-exercise-lg" style="min-width: 150px;margin-top:15px">
                        <i class="bi bi-check"></i> Verificar
                    </button>
                </div>
                
                <div class="mt-4">
                    <small class="text-muted">Intento <span id="emd-counter">0</span>/10</small>
                </div>
                
                <div id="emd-feedback" style="display: none; margin-top: 20px;">
                    <div id="emd-feedback-message" class="alert"></div>
                </div>
            </div>
        `;

        return container;
    }

    // Función principal de inicio
    function start() {
        console.log('Iniciando ejercicio EMD:', window.EXERCISE_CONFIG.codigo);
        
        const container = initContainer();
        if (!container) {
            console.error('No se pudo inicializar el contenedor EMD');
            return;
        }

        // Determinar número de dígitos según el ejercicio
        const codigo = window.EXERCISE_CONFIG.codigo;
        if (codigo.includes('EMD1')) {
            numberOfDigits = 2;
        } else if (codigo.includes('EMD2')) {
            numberOfDigits = 4;
        } else if (codigo.includes('EMD3')) {
            numberOfDigits = 6;
        } else {
            console.error('Ejercicio EMD desconocido:', codigo);
            return;
        }

        // Configurar estado inicial
        const state = ExerciseCore.getState();
        state.numberOfDigits = numberOfDigits;
        state.totalAttempts = 10;
        state.currentAttempt = 0;
        
        // Esperar un momento y comenzar
        setTimeout(() => {
            startNextAttempt();
        }, 500);
    }

    // Iniciar siguiente intento
    function startNextAttempt() {
        const state = ExerciseCore.getState();
        
        if (state.currentAttempt >= state.totalAttempts) {
            ExerciseCore.showResults();
            return;
        }
        
        // Actualizar contador
        document.getElementById('emd-counter').textContent = state.currentAttempt + 1;
        
        // Generar números aleatorios
        currentNumbers = [];
        for (let i = 0; i < numberOfDigits; i++) {
            currentNumbers.push(Math.floor(Math.random() * 10));
        }
        
        state.currentNumbers = currentNumbers;
        
        console.log('Números generados para intento', state.currentAttempt + 1, ':', currentNumbers);
        
        // Mostrar números
        showNumbers();
    }

    // Mostrar números
    function showNumbers() {
        const displayContainer = document.getElementById('emd-display-container');
        const display = document.getElementById('emd-display');
        const inputContainer = document.getElementById('emd-input-container');
        const feedbackContainer = document.getElementById('emd-feedback');
        
        if (!displayContainer || !display || !inputContainer) {
            console.error('Elementos EMD no encontrados');
            return;
        }

        // Ocultar feedback anterior
        if (feedbackContainer) {
            feedbackContainer.style.display = 'none';
        }
        
        // Mostrar los números
        display.textContent = currentNumbers.join(' ');
        displayContainer.style.display = 'block';
        inputContainer.style.display = 'none';
        showingNumbers = true;
        
        // Ocultar después del tiempo configurado
        const displayTime = ExerciseCore.getSpeedByLevel();
        setTimeout(() => {
            hideNumbers();
        }, displayTime);
    }

    // Ocultar números y mostrar inputs
    function hideNumbers() {
        const displayContainer = document.getElementById('emd-display-container');
        const inputContainer = document.getElementById('emd-input-container');
        const inputsDiv = document.getElementById('emd-inputs');
        const submitBtn = document.getElementById('emd-submit');
        
        if (!displayContainer || !inputContainer || !inputsDiv) {
            console.error('Elementos EMD para inputs no encontrados');
            return;
        }

        // Ocultar números y mostrar inputs
        displayContainer.style.display = 'none';
        inputContainer.style.display = 'block';
        showingNumbers = false;
        
        // Habilitar el botón de submit para la nueva ronda
        if (submitBtn) {
            submitBtn.disabled = false;
        }
        
        // Crear UN SOLO input para todos los dígitos
        inputsDiv.innerHTML = '';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'exercise-input';
        input.style.width = `${Math.max(120, numberOfDigits * 30)}px`; // Ancho dinámico según número de dígitos
        input.style.fontSize = '1.5rem';
        input.style.textAlign = 'center';
        input.style.letterSpacing = '0.5em';
        input.maxLength = numberOfDigits;
        input.pattern = '[0-9]*';
        input.inputmode = 'numeric';
        input.id = 'digits-input';
        input.placeholder = '0'.repeat(numberOfDigits); // Placeholder visual
        
        // Validar que solo se introduzcan números
        input.addEventListener('input', (e) => {
            let value = e.target.value;
            
            // Filtrar solo números
            value = value.replace(/[^0-9]/g, '');
            
            // Limitar a la cantidad de dígitos necesarios
            if (value.length > numberOfDigits) {
                value = value.substring(0, numberOfDigits);
            }
            
            e.target.value = value;
            
            // Auto-submit cuando se complete
            if (value.length === numberOfDigits) {
                setTimeout(() => {
                    checkAnswer();
                }, 300); // Pequeña pausa para que el usuario vea el número completo
            }
        });
        
        // Permitir Enter para verificar
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                checkAnswer();
            }
        });
        
        inputsDiv.appendChild(input);
        
        // Focus en el input
        input.focus();
        
        // Configurar botón de submit
        if (submitBtn) {
            submitBtn.onclick = checkAnswer;
        }
    }

    // Verificar respuesta
    function checkAnswer() {
        const state = ExerciseCore.getState();
        const input = document.getElementById('digits-input');
        
        if (!input) {
            console.error('Input de dígitos no encontrado');
            return;
        }
        
        const userInput = input.value.padStart(numberOfDigits, '0'); // Rellenar con ceros si es necesario
        const userAnswers = userInput.split('').map(digit => parseInt(digit));
        
        console.log('Respuesta del usuario:', userAnswers, 'vs', currentNumbers);
        
        // Verificar si es correcta
        let isCorrect = true;
        for (let i = 0; i < currentNumbers.length; i++) {
            if (userAnswers[i] !== currentNumbers[i]) {
                isCorrect = false;
                break;
            }
        }
        
        if (isCorrect) {
            state.correctAnswers++;
        }
        
        state.currentAttempt++;
        ExerciseCore.updateProgress();
        
        // Mostrar feedback
        showEMDFeedback(isCorrect, userAnswers);
        
        // Continuar al siguiente intento después del feedback
        setTimeout(() => {
            startNextAttempt();
        }, 1500);
    }

    // Mostrar feedback
    function showEMDFeedback(isCorrect, userAnswers) {
        const feedbackContainer = document.getElementById('emd-feedback');
        const feedbackMessage = document.getElementById('emd-feedback-message');
        
        if (!feedbackContainer || !feedbackMessage) return;
        
        feedbackMessage.textContent = isCorrect ? '¡Correcto!' : 
            `Incorrecto. Los números eran: ${currentNumbers.join(' ')}`;
        feedbackMessage.className = isCorrect ? 'alert alert-success' : 'alert alert-danger';
        feedbackContainer.style.display = 'block';
        
        // Deshabilitar inputs y botón
        const inputs = document.querySelectorAll('#emd-inputs input');
        const submitBtn = document.getElementById('emd-submit');
        
        inputs.forEach(input => input.disabled = true);
        if (submitBtn) submitBtn.disabled = true;
    }

    // API pública
    return {
        start: start
    };

})();
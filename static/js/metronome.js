/**
 * static/js/metronome.js
 * Componente de metrónomo para marcar ritmo de lectura
 */

class Metronome {
    constructor(options = {}) {
        // Opciones configurables
        this.options = {
            tempo: options.tempo || 60,             // Beats por minuto (BPM)
            beatsPerMeasure: options.beatsPerMeasure || 4, // Beats por compás
            autoStart: options.autoStart || false,  // Iniciar automáticamente
            accentFirst: options.accentFirst || true, // Acentuar el primer beat de cada compás
            visualCallback: options.visualCallback || null, // Callback para visualización
            soundEnabled: options.soundEnabled !== undefined ? options.soundEnabled : true, // Sonidos habilitados
            volume: options.volume || 0.5,          // Volumen (0-1)
        };
        
        // Estado interno
        this.audioContext = null;     // Contexto de audio
        this.nextNoteTime = 0;        // Tiempo para el próximo beat
        this.timerWorker = null;      // Worker para timing preciso
        this.currentBeat = 0;         // Beat actual dentro del compás
        this.running = false;         // Estado de ejecución
        
        // Inicializar
        this._init();
    }
    
    /**
     * Inicializa el metrónomo
     */
    _init() {
        // Crear Web Audio API context
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioContext();
        
        // Crear worker para timing preciso
        this._createWorker();
        
        // Auto-inicio si está configurado
        if (this.options.autoStart) {
            this.start();
        }
    }
    
    /**
     * Crea el worker para timing preciso
     */
    _createWorker() {
        // Crear un blob con el código del worker
        const workerBlob = new Blob([
            `
            let timerID = null;
            let interval = 25;
            
            self.onmessage = function(e) {
                if (e.data === "start") {
                    timerID = setInterval(() => { self.postMessage("tick"); }, interval);
                } else if (e.data === "stop") {
                    clearInterval(timerID);
                    timerID = null;
                } else if (e.data.interval) {
                    interval = e.data.interval;
                    if (timerID) {
                        clearInterval(timerID);
                        timerID = setInterval(() => { self.postMessage("tick"); }, interval);
                    }
                }
            };
            `
        ], { type: "application/javascript" });
        
        // Crear URL para el blob
        const workerURL = URL.createObjectURL(workerBlob);
        
        // Crear worker
        this.timerWorker = new Worker(workerURL);
        
        // Configurar callback del worker
        this.timerWorker.onmessage = (e) => {
            if (e.data === "tick") {
                this._scheduler();
            }
        };
        
        // Configurar intervalo
        this.timerWorker.postMessage({ interval: 25 });
    }
    
    /**
     * Programador de notas
     * Se encarga de programar los sonidos con anticipación
     */
    _scheduler() {
        // Anticipación de 100ms
        const scheduleAheadTime = 0.1;
        
        // Programar notas hasta la anticipación
        while (this.nextNoteTime < this.audioContext.currentTime + scheduleAheadTime) {
            this._scheduleNote(this.currentBeat, this.nextNoteTime);
            this._advanceNote();
        }
    }
    
    /**
     * Programa un sonido para un tiempo específico
     */
    _scheduleNote(beat, time) {
        // Disparar callback visual si existe
        if (typeof this.options.visualCallback === 'function') {
            // Convertir de tiempo absoluto a relativo
            const currentTime = this.audioContext.currentTime;
            // Enviar tiempo en ms hasta que suene esta nota
            const timeUntilNote = (time - currentTime) * 1000;
            const isAccented = beat === 0 && this.options.accentFirst;
            
            // Programar visualización
            setTimeout(() => {
                this.options.visualCallback(beat, isAccented);
            }, timeUntilNote);
        }
        
        // Reproducir sonido si está habilitado
        if (this.options.soundEnabled) {
            // Crear oscilador para el beep
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Configurar tipo de oscilador
            oscillator.type = 'sine';
            
            // Acentuar primer beat si está configurado
            if (beat === 0 && this.options.accentFirst) {
                oscillator.frequency.value = 880; // Nota más alta para el acento
                gainNode.gain.value = this.options.volume;
            } else {
                oscillator.frequency.value = 440; // Nota normal
                gainNode.gain.value = this.options.volume * 0.8; // Ligeramente más bajo
            }
            
            // Programar inicio y fin del sonido
            oscillator.start(time);
            oscillator.stop(time + 0.05); // Duración de 50ms
        }
    }
    
    /**
     * Avanza al siguiente beat
     */
    _advanceNote() {
        // Incrementar beat en el compás
        this.currentBeat = (this.currentBeat + 1) % this.options.beatsPerMeasure;
        
        // Calcular tiempo para el siguiente beat
        const secondsPerBeat = 60.0 / this.options.tempo;
        this.nextNoteTime += secondsPerBeat;
    }
    
    /**
     * Inicia el metrónomo
     */
    start() {
        if (this.running) return;
        
        // Asegurar que el contexto de audio está en estado running
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        this.running = true;
        
        // Resetear contador de beat y tiempo
        this.currentBeat = 0;
        this.nextNoteTime = this.audioContext.currentTime;
        
        // Iniciar worker
        this.timerWorker.postMessage("start");
        
        // Disparar evento
        this._dispatchEvent('metronome-start');
    }
    
    /**
     * Detiene el metrónomo
     */
    stop() {
        if (!this.running) return;
        
        this.running = false;
        this.timerWorker.postMessage("stop");
        
        // Disparar evento
        this._dispatchEvent('metronome-stop');
    }
    
    /**
     * Cambia el tempo (BPM)
     */
    setTempo(tempo) {
        if (tempo < 30) tempo = 30;
        if (tempo > 300) tempo = 300;
        
        this.options.tempo = tempo;
        
        // Disparar evento
        this._dispatchEvent('metronome-tempo-change', { tempo });
    }
    
    /**
     * Cambia el número de beats por compás
     */
    setBeatsPerMeasure(beats) {
        if (beats < 1) beats = 1;
        if (beats > 12) beats = 12;
        
        this.options.beatsPerMeasure = beats;
        this.currentBeat = 0; // Resetear beat para evitar problemas
        
        // Disparar evento
        this._dispatchEvent('metronome-beats-change', { beatsPerMeasure: beats });
    }
    
    /**
     * Cambia el volumen
     */
    setVolume(volume) {
        if (volume < 0) volume = 0;
        if (volume > 1) volume = 1;
        
        this.options.volume = volume;
        
        // Disparar evento
        this._dispatchEvent('metronome-volume-change', { volume });
    }
    
    /**
     * Activa/desactiva los sonidos
     */
    setSoundEnabled(enabled) {
        this.options.soundEnabled = enabled;
        
        // Disparar evento
        this._dispatchEvent('metronome-sound-toggle', { soundEnabled: enabled });
    }
    
    /**
     * Activa/desactiva el acento en el primer beat
     */
    setAccentFirst(accent) {
        this.options.accentFirst = accent;
        
        // Disparar evento
        this._dispatchEvent('metronome-accent-toggle', { accentFirst: accent });
    }
    
    /**
     * Obtiene el tempo actual
     */
    getTempo() {
        return this.options.tempo;
    }
    
    /**
     * Verifica si el metrónomo está en ejecución
     */
    isRunning() {
        return this.running;
    }
    
    /**
     * Dispara un evento personalizado
     */
    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail: {
                metronome: this,
                ...detail
            },
            bubbles: true
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * Libera recursos al destruir
     */
    destroy() {
        if (this.running) {
            this.stop();
        }
        
        if (this.timerWorker) {
            this.timerWorker.terminate();
            this.timerWorker = null;
        }
        
        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.close();
        }
    }
}

// Exponer al ámbito global
window.Metronome = Metronome;
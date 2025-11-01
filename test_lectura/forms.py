# test_lectura/forms.py
from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from .models import TestLectura, PreguntaTest, OpcionRespuesta


class PasswordTestForm(forms.Form):
    """
    Formulario para ingresar contraseña de acceso a un test.
    """
    password = forms.CharField(
        label='Contraseña de acceso',
        max_length=20,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ingresa la contraseña del test',
            'class': 'form-control'
        })
    )
    
    def __init__(self, test=None, *args, **kwargs):
        self.test = test
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML(f'<div class="alert alert-info">'),
            HTML(f'<h5>{self.test.titulo if self.test else "Test"}</h5>'),
            HTML(f'<p>Este test requiere una contraseña de acceso.</p>'),
            HTML(f'</div>'),
            Field('password', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Acceder al Test', css_class='btn btn-primary btn-lg w-100')
            )
        )
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if self.test and password != self.test.password_acceso:
            raise ValidationError('Contraseña incorrecta.')
        return password


class FiltroTestsForm(forms.Form):
    """
    Formulario para filtrar tests en la vista de lista.
    """
    DIFICULTAD_CHOICES = [
        ('', 'Todas las dificultades'),
        ('inicial', 'Test Inicial'),
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('disponible', 'Disponibles'),
        ('completado', 'Completados'),
        ('bloqueado', 'Bloqueados'),
    ]
    
    dificultad = forms.ChoiceField(
        choices=DIFICULTAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    buscar = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre o descripción...',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        self.helper.layout = Layout(
            Field('buscar', wrapper_class='col-md-6'),
            Field('dificultad', wrapper_class='col-md-3'),
            Field('estado', wrapper_class='col-md-3'),
        )


class ComparacionResultadosForm(forms.Form):
    """
    Formulario para seleccionar tests a comparar (HTMX).
    """
    test_nombre = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '/tests/comparar-resultados/',
            'hx-target': '#grafico-comparacion',
            'hx-trigger': 'change'
        })
    )
    
    def __init__(self, usuario=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if usuario:
            # Obtener tests que el usuario ha completado
            from usuarios.models import ProgresoTests
            tests_completados = ProgresoTests.objects.filter(
                usuario=usuario,
                completado=True
            ).values_list('test_nombre', flat=True).distinct()
            
            choices = [(test, test.replace('_', ' ').title()) for test in tests_completados]
            self.fields['test_nombre'].widget.choices = choices


# Forms para administración (Django Admin)
class TestLecturaAdminForm(forms.ModelForm):
    """
    Formulario personalizado para el admin de TestLectura.
    """
    class Meta:
        model = TestLectura
        fields = '__all__'
        widgets = {
            'texto_contenido': forms.Textarea(attrs={'rows': 10, 'cols': 80}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'instrucciones': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_numero_palabras(self):
        numero_palabras = self.cleaned_data.get('numero_palabras')
        texto_contenido = self.cleaned_data.get('texto_contenido')
        
        if texto_contenido and numero_palabras:
            palabras_reales = len(texto_contenido.split())
            if abs(numero_palabras - palabras_reales) > 10:  # Tolerancia de 10 palabras
                self.cleaned_data['numero_palabras'] = palabras_reales
                
        return self.cleaned_data.get('numero_palabras')
    
    def clean(self):
        cleaned_data = super().clean()
        requiere_password = cleaned_data.get('requiere_password')
        password_acceso = cleaned_data.get('password_acceso')
        
        if requiere_password and not password_acceso:
            raise ValidationError('Si requiere contraseña, debe especificar una.')
        
        return cleaned_data


class PreguntaTestAdminForm(forms.ModelForm):
    """
    Formulario personalizado para el admin de PreguntaTest.
    """
    class Meta:
        model = PreguntaTest
        fields = '__all__'
        widgets = {
            'pregunta_text': forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        }


class OpcionRespuestaAdminForm(forms.ModelForm):
    """
    Formulario personalizado para el admin de OpcionRespuesta.
    """
    class Meta:
        model = OpcionRespuesta
        fields = '__all__'
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 2, 'cols': 50}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar que hay al menos una opción correcta por pregunta
        # Esta validación se hace a nivel de admin con JavaScript o signals
        
        return cleaned_data


class CrearTestPersonalizadoForm(forms.ModelForm):
    """
    Formulario para que los usuarios Pro/Opositor creen tests personalizados.
    """
    class Meta:
        model = TestLectura
        fields = [
            'nombre', 'titulo', 'descripcion', 'instrucciones',
            'texto_titulo', 'texto_contenido', 'texto_autor'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre único para tu test',
                'class': 'form-control'
            }),
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Título del test',
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'placeholder': 'Descripción breve del test',
                'rows': 3,
                'class': 'form-control'
            }),
            'instrucciones': forms.Textarea(attrs={
                'placeholder': 'Instrucciones para el usuario',
                'rows': 3,
                'class': 'form-control'
            }),
            'texto_titulo': forms.TextInput(attrs={
                'placeholder': 'Título del texto a leer',
                'class': 'form-control'
            }),
            'texto_contenido': forms.Textarea(attrs={
                'placeholder': 'Contenido del texto para leer (mínimo 100 palabras)',
                'rows': 10,
                'class': 'form-control'
            }),
            'texto_autor': forms.TextInput(attrs={
                'placeholder': 'Autor del texto (opcional)',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, usuario=None, *args, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h4>Información del Test</h4>'),
            Field('nombre', css_class='form-group mb-3'),
            Field('titulo', css_class='form-group mb-3'),
            Field('descripcion', css_class='form-group mb-3'),
            Field('instrucciones', css_class='form-group mb-3'),
            HTML('<hr><h4>Contenido del Texto</h4>'),
            Field('texto_titulo', css_class='form-group mb-3'),
            Field('texto_contenido', css_class='form-group mb-3'),
            Field('texto_autor', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Crear Test Personalizado', css_class='btn btn-primary')
            )
        )
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if TestLectura.objects.filter(nombre=nombre).exists():
            raise ValidationError('Ya existe un test con ese nombre.')
        return nombre
    
    def clean_texto_contenido(self):
        texto = self.cleaned_data.get('texto_contenido')
        if texto:
            palabras = len(texto.split())
            if palabras < 100:
                raise ValidationError('El texto debe tener al menos 100 palabras.')
            if palabras > 2000:
                raise ValidationError('El texto no debe superar las 2000 palabras.')
        return texto
    
    def save(self, commit=True):
        test = super().save(commit=False)
        test.is_custom = True
        test.created_by = self.usuario
        test.dificultad = 'principiante'  # Por defecto
        test.activo = True
        
        # Calcular número de palabras
        if test.texto_contenido:
            test.numero_palabras = len(test.texto_contenido.split())
        
        if commit:
            test.save()
        return test


class EstadisticasForm(forms.Form):
    """
    Formulario para filtrar estadísticas (solo gestores).
    """
    PERIODO_CHOICES = [
        ('7', 'Últimos 7 días'),
        ('30', 'Último mes'),
        ('90', 'Últimos 3 meses'),
        ('365', 'Último año'),
        ('todos', 'Todos los datos'),
    ]
    
    periodo = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        initial='30',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    test_especifico = forms.ModelChoiceField(
        queryset=TestLectura.objects.filter(activo=True),
        required=False,
        empty_label="Todos los tests",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        self.helper.layout = Layout(
            Field('periodo', wrapper_class='col-md-6'),
            Field('test_especifico', wrapper_class='col-md-6'),
        )
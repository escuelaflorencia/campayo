# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from crispy_forms.bootstrap import FormActions
from .models import Usuario


class RegistroForm(UserCreationForm):
    """
    Formulario de registro simplificado con solo campos esenciales.
    """
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu nombre',
            'class': 'form-control'
        })
    )
    apellidos = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tus apellidos',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@email.com',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellidos', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar labels y help texts
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Contraseña',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirmar contraseña',
            'class': 'form-control'
        })
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-6 mb-3'),
                Column('apellidos', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('email', css_class='form-group mb-3'),
            Field('password1', css_class='form-group mb-3'),
            Field('password2', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Crear Cuenta', css_class='btn btn-primary btn-lg w-100')
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este email.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Usar email como username
        user.nombre = self.cleaned_data['nombre']
        user.apellidos = self.cleaned_data['apellidos']
        # Por defecto, todos los usuarios nuevos son tipo 'usuario' y plan 'gratuito'
        user.tipo_usuario = 'usuario'
        user.plan = 'gratuito'
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Formulario de login personalizado usando email en lugar de username.
    """
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@email.com',
            'class': 'form-control',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Tu contraseña',
            'class': 'form-control'
        })
    )
    
    def __init__(self, request=None, *args, **kwargs):
        """
        El parámetro request es necesario para mantener compatibilidad con AuthenticationForm
        aunque no lo usemos directamente aquí.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='form-group mb-3'),
            Field('password', css_class='form-group mb-3'),
            HTML('<div class="d-grid gap-2 mb-3">'),
            Submit('submit', 'Iniciar Sesión', css_class='btn btn-primary btn-lg'),
            HTML('</div>'),
            HTML('<div class="text-center">'),
            HTML('<a href="{% url \'usuarios:password_reset\' %}" class="text-decoration-none">¿Olvidaste tu contraseña?</a>'),
            HTML('</div>')
        )
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            # Buscar usuario por email
            try:
                usuario = Usuario.objects.get(email=email)
                # Autenticar usando el username del usuario
                from django.contrib.auth import authenticate
                self.user_cache = authenticate(
                    self.request,
                    username=usuario.username,
                    password=password
                )
                
                if self.user_cache is None:
                    raise ValidationError(
                        'Por favor, introduzca un email y contraseña correctos.',
                        code='invalid_login'
                    )
                    
            except Usuario.DoesNotExist:
                raise ValidationError(
                    'No existe un usuario con este email.',
                    code='invalid_login'
                )
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class EditarPerfilForm(forms.ModelForm):
    """
    Formulario para editar información personal del usuario.
    """
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellidos', 'email')
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Tu nombre',
                'class': 'form-control'
            }),
            'apellidos': forms.TextInput(attrs={
                'placeholder': 'Tus apellidos',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'tu@email.com',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-6 mb-3'),
                Column('apellidos', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('email', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Guardar Cambios', css_class='btn btn-primary')
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Verificar que el email no esté en uso por otro usuario
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe otro usuario con este email.')
        return email


class CambiarPasswordForm(PasswordChangeForm):
    """
    Formulario para cambiar contraseña.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets
        self.fields['old_password'].widget.attrs.update({
            'placeholder': 'Contraseña actual',
            'class': 'form-control'
        })
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': 'Nueva contraseña',
            'class': 'form-control'
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': 'Confirmar nueva contraseña',
            'class': 'form-control'
        })
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('old_password', css_class='form-group mb-3'),
            Field('new_password1', css_class='form-group mb-3'),
            Field('new_password2', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Cambiar Contraseña', css_class='btn btn-primary')
            )
        )


class RecuperarPasswordForm(forms.Form):
    """
    Formulario para solicitar recuperación de contraseña.
    """
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@email.com',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='form-group mb-3'),
            HTML('<p class="text-muted small">Te enviaremos un enlace para restablecer tu contraseña.</p>'),
            FormActions(
                Submit('submit', 'Enviar Enlace', css_class='btn btn-primary btn-lg w-100')
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            Usuario.objects.get(email=email)
            return email
        except Usuario.DoesNotExist:
            raise ValidationError('No existe un usuario registrado con este email.')


class BuscarUsuarioForm(forms.Form):
    """
    Formulario para búsqueda dinámica de usuarios (solo para gestores).
    """
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre, apellidos o email...',
            'class': 'form-control',
            'hx-post': '/usuarios/buscar/',
            'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#resultados-usuarios',
            'hx-indicator': '#loading-usuarios'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'form-buscar-usuarios'
        self.helper.layout = Layout(
            Field('busqueda', css_class='form-group mb-3'),
        )


class CambiarPlanForm(forms.Form):
    """
    Formulario para cambiar plan de usuario (HTMX).
    """
    usuario_id = forms.IntegerField(widget=forms.HiddenInput())
    nuevo_plan = forms.ChoiceField(
        choices=[('gratuito', 'Gratuito'), ('pro', 'Pro')],
        widget=forms.HiddenInput()
    )
    
    def clean_usuario_id(self):
        usuario_id = self.cleaned_data.get('usuario_id')
        try:
            return Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            raise ValidationError('Usuario no encontrado.')
from django.contrib.auth.forms import \
        AuthenticationForm as AuthenticationFormBase

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class AuthenticationForm(AuthenticationFormBase):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        # self.helper.layout = Layout(
        #         'username',
        #         'password',
        #         )

        self.helper.add_input(
                Submit("submit", "Sign in"))
        super(AuthenticationForm, self).__init__(*args, **kwargs)


def login(request):
    from django.contrib.auth.views import LoginView
    return LoginView.as_view(template_name="login.html",
            authentication_form=AuthenticationForm)(request)

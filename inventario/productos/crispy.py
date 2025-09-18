from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class BaseFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = "post"
        self.form_class = "form-horizontal"
        self.label_class = "col-md-3 col-form-label"
        self.field_class = "col-md-9"
        self.render_required_fields = "True"
from django import forms

class BootstrapFormMixin:
    # A mapping of widget classes to the Bootstrap classes they should receive
    BOOTSTRAP_WIDGET_CLASSES = {
        forms.TextInput: "form-control",
        forms.NumberInput: "form-control",
        forms.EmailInput: "form-control",
        forms.URLInput: "form-control",
        forms.PasswordInput: "form-control",
        forms.Textarea: "form-control",
        forms.Select: "form-select",
        forms.SelectMultiple: "form-select",
        forms.CheckboxInput: "form-check-input",
        forms.RadioSelect: "form-check-input",
        forms.FileInput: "form-control",
        forms.ClearableFileInput: "form-control",
        forms.DateInput: "form-control",
        forms.DateTimeInput: "form-control",
        forms.TimeInput: "form-control",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget
            css_class = self._bootstrap_class_for_widget(widget)

            # Merge with existing classes
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()

    def _bootstrap_class_for_widget(self, widget):
        """
        Find the correct Bootstrap class for a widget based on inheritance.
        """
        for widget_type, css_class in self.BOOTSTRAP_WIDGET_CLASSES.items():
            if isinstance(widget, widget_type):
                return css_class
        return "form-control"  # fallback for unknown widgets
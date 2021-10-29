from django import forms

class DateFieldFormat(forms.DateInput):
    # date = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'])
    input_type = 'date'

class DateForm(forms.Form):
    date_field = forms.DateField(widget=DateFieldFormat, required=False)
from django import forms

class BacktestForm(forms.Form):
    SYMBOL_CHOICES = [('NSE:NIFTY50', 'Nifty 50'), ('NSE:RELIANCE', 'Reliance')]
    INTERVAL_CHOICES = [('1', '1 Min'), ('5', '5 Min'), ('60', '1 Hour'), ('D', '1 Day')]
    CANDLE_CHOICES = [('normal', 'Normal'), ('heikin_ashi', 'Heikin Ashi')]

    symbol = forms.ChoiceField(choices=SYMBOL_CHOICES)
    interval = forms.ChoiceField(choices=INTERVAL_CHOICES)
    start_date = forms.DateField(widget=forms.SelectDateWidget)
    end_date = forms.DateField(widget=forms.SelectDateWidget)
    
    candle_type = forms.ChoiceField(choices=CANDLE_CHOICES)
    
    # Indicators
    enable_ema = forms.BooleanField(required=False)
    ema_color = forms.CharField(initial="#00FF00", widget=forms.TextInput(attrs={'type': 'color'}))
    
    enable_rsi = forms.BooleanField(required=False)
    rsi_color = forms.CharField(initial="#FF0000", widget=forms.TextInput(attrs={'type': 'color'}))

from django import forms

class TOTPLoginForm(forms.Form):
    # Only this field exists now
    totp_code = forms.CharField(
        max_length=6, 
        min_length=6, 
        label="Enter TOTP",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '6-digit code'
        })
    )
from django import forms

QUANTIDADE_CHOICES = [(i, str(i)) for i in range(1, 21)]

class FormAdicionarProdutoCarrinho(forms.Form):
    quantidade = forms.TypedChoiceField(
        choices=QUANTIDADE_CHOICES,
        coerce=int,
        initial=1
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )


# ====================
# 3. carrinho/context_processors.py
# ====================
from .cart import Carrinho

def carrinho_context(request):
    """Context processor para disponibilizar o carrinho em todos os templates"""
    return {'carrinho': Carrinho(request)}

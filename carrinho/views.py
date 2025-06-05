from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from produtos.models import Produto
from .cart import Carrinho
from .forms import FormAdicionarProdutoCarrinho


@require_POST
def adicionar_carrinho(request, produto_id):
    """View para adicionar produto ao carrinho"""
    carrinho = Carrinho(request)
    produto = get_object_or_404(Produto, id=produto_id)
    
    form = FormAdicionarProdutoCarrinho(request.POST)
    
    if form.is_valid():
        quantidade = form.cleaned_data['quantidade']
        override = form.cleaned_data.get('override', False)
    else:
        quantidade = 1
        override = False
    
    carrinho.adicionar(
        produto=produto, 
        quantidade=quantidade, 
        override_quantidade=override
    )
    
    return redirect('carrinho:detalhe')


@require_POST
def remover_carrinho(request, produto_id):
    """View para remover produto do carrinho"""
    carrinho = Carrinho(request)
    produto = get_object_or_404(Produto, id=produto_id)
    carrinho.remover(produto)
    
    return redirect('carrinho:detalhe')


def detalhe_carrinho(request):
    """View para exibir detalhes do carrinho"""
    carrinho = Carrinho(request)
    
    for item in carrinho:
        item['form_atualizacao'] = FormAdicionarProdutoCarrinho(initial={
            'quantidade': item['quantidade'],
            'override': True
        })
    
    return render(request, 'carrinho/detalhe.html', {'carrinho': carrinho})


@require_POST
def limpar_carrinho(request):
    """View para limpar todo o carrinho"""
    carrinho = Carrinho(request)
    carrinho.limpar()
    return redirect('carrinho:detalhe')


# Views AJAX (opcionais)
@require_POST
def adicionar_carrinho_ajax(request, produto_id):
    """View AJAX para adicionar produto ao carrinho"""
    try:
        carrinho = Carrinho(request)
        produto = get_object_or_404(Produto, id=produto_id)
        
        quantidade = int(request.POST.get('quantidade', 1))
        override = request.POST.get('override', 'false').lower() == 'true'
        
        if quantidade < 1 or quantidade > 20:
            return JsonResponse({
                'success': False,
                'error': 'Quantidade deve estar entre 1 e 20'
            })
        
        carrinho.adicionar(
            produto=produto, 
            quantidade=quantidade, 
            override_quantidade=override
        )
        
        return JsonResponse({
            'success': True,
            'total_items': len(carrinho),
            'total_price': str(carrinho.get_total_price()),
            'message': f'{produto.nome} adicionado ao carrinho'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
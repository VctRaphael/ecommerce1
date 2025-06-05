from decimal import Decimal
from django.conf import settings
from produtos.models import Produto


class Carrinho:
    def __init__(self, request):
        """
        Inicializa o carrinho com a sessão do usuário
        """
        self.session = request.session
        carrinho = self.session.get(settings.CARRINHO_SESSION_ID)
        if not carrinho:
            carrinho = self.session[settings.CARRINHO_SESSION_ID] = {}
        self.carrinho = carrinho
    
    def adicionar(self, produto, quantidade=1, override_quantidade=False):
        """
        Adiciona um produto ao carrinho ou atualiza sua quantidade
        """
        produto_id = str(produto.id)
        if produto_id not in self.carrinho:
            self.carrinho[produto_id] = {
                'quantidade': 0, 
                'preco': str(produto.preco)
            }
        
        if override_quantidade:
            self.carrinho[produto_id]['quantidade'] = quantidade
        else:
            self.carrinho[produto_id]['quantidade'] += quantidade
        
        self.salvar()
    
    def salvar(self):
        """Marca a sessão como modificada"""
        self.session.modified = True
    
    def remover(self, produto):
        """Remove um produto do carrinho"""
        produto_id = str(produto.id)
        if produto_id in self.carrinho:
            del self.carrinho[produto_id]
            self.salvar()
    
    def __iter__(self):
        """
        Itera sobre os itens do carrinho obtendo os produtos do banco
        """
        produto_ids = self.carrinho.keys()
        if not produto_ids:
            return iter([])
            
        produtos = Produto.objects.filter(id__in=produto_ids)
        carrinho = self.carrinho.copy()
        
        for produto in produtos:
            carrinho[str(produto.id)]['produto'] = produto
        
        for item in carrinho.values():
            if 'produto' in item:
                item['preco'] = Decimal(item['preco'])
                item['preco_total'] = item['preco'] * item['quantidade']
                yield item
    
    def __len__(self):
        """Retorna o número total de itens no carrinho"""
        return sum(item['quantidade'] for item in self.carrinho.values())
    
    def get_total_price(self):
        """Calcula o preço total do carrinho"""
        return sum(
            Decimal(item['preco']) * item['quantidade'] 
            for item in self.carrinho.values()
        )
    
    def limpar(self):
        """Remove todos os itens do carrinho"""
        if settings.CARRINHO_SESSION_ID in self.session:
            del self.session[settings.CARRINHO_SESSION_ID]
        self.salvar()
        
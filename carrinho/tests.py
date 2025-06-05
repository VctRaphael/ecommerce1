from decimal import Decimal
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from produtos.models import Produto, Categoria
from .cart import Carrinho
from .forms import FormAdicionarProdutoCarrinho
from .context_processors import carrinho_context


class BaseCarrinhoTestCase(TestCase):
    """Classe base para testes do carrinho"""
    
    def setUp(self):
        # Criar categoria (necessária para os produtos)
        self.categoria = Categoria.objects.create(
            nome="Categoria Teste",
            slug="categoria-teste"
        )
        
        # Criar produtos completos
        self.produto1 = Produto.objects.create(
            nome="Produto 1",
            slug="produto-1",
            descricao="Descrição do produto 1",
            preco=Decimal('10.50'),
            estoque=100,
            categoria=self.categoria
        )
        
        self.produto2 = Produto.objects.create(
            nome="Produto 2", 
            slug="produto-2",
            descricao="Descrição do produto 2",
            preco=Decimal('25.00'),
            estoque=50,
            categoria=self.categoria
        )
        
        self.client = Client()
        self.factory = RequestFactory()
    
    def criar_request_com_sessao(self, dados_sessao=None):
        """Helper para criar request com sessão configurada"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        if dados_sessao:
            for chave, valor in dados_sessao.items():
                request.session[chave] = valor
            request.session.save()
        
        return request


class CarrinhoClasseTest(BaseCarrinhoTestCase):
    """Testes para a classe Carrinho"""
    
    def test_inicializacao_carrinho_vazio(self):
        request = self.criar_request_com_sessao()
        carrinho = Carrinho(request)
        
        self.assertEqual(carrinho.carrinho, {})
        self.assertIn(settings.CARRINHO_SESSION_ID, request.session)
    
    def test_adicionar_produto_novo(self):
        request = self.criar_request_com_sessao()
        carrinho = Carrinho(request)
        
        carrinho.adicionar(self.produto1, quantidade=2)
        
        produto_id = str(self.produto1.id)
        self.assertIn(produto_id, carrinho.carrinho)
        self.assertEqual(carrinho.carrinho[produto_id]['quantidade'], 2)
    
    def test_len_carrinho(self):
        request = self.criar_request_com_sessao()
        carrinho = Carrinho(request)
        
        carrinho.adicionar(self.produto1, quantidade=2)
        carrinho.adicionar(self.produto2, quantidade=3)
        
        self.assertEqual(len(carrinho), 5)  # 2 + 3
    
    def test_get_total_price(self):
        request = self.criar_request_com_sessao()
        carrinho = Carrinho(request)
        
        carrinho.adicionar(self.produto1, quantidade=2)
        carrinho.adicionar(self.produto2, quantidade=1)
        
        total_esperado = (self.produto1.preco * 2) + (self.produto2.preco * 1)
        self.assertEqual(carrinho.get_total_price(), total_esperado)


class CarrinhoViewsTest(BaseCarrinhoTestCase):
    """Testes para as views do carrinho"""
    
    def test_detalhe_carrinho_get(self):
        response = self.client.get(reverse('carrinho:detalhe'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('carrinho', response.context)
    
    def test_adicionar_produto_post(self):
        response = self.client.post(
            reverse('carrinho:adicionar', kwargs={'produto_id': self.produto1.id})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('carrinho:detalhe'))
        
        # Verificar se produto foi adicionado
        session_data = self.client.session.get(settings.CARRINHO_SESSION_ID, {})
        self.assertIn(str(self.produto1.id), session_data)


class CarrinhoFormsTest(TestCase):
    """Testes para formulários do carrinho"""
    
    def test_form_valido(self):
        form_data = {'quantidade': 5, 'override': False}
        form = FormAdicionarProdutoCarrinho(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['quantidade'], 5)
    
    def test_form_quantidade_invalida(self):
        form_data = {'quantidade': 25, 'override': False}  # Fora do range
        form = FormAdicionarProdutoCarrinho(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('quantidade', form.errors)

class CarrinhoBranchesTest(TestCase):
    def setUp(self):
        # Crie produtos e categoria como no BaseCarrinhoTestCase
        self.categoria = Categoria.objects.create(
            nome="Categoria Teste",
            slug="categoria-teste"
        )
        self.produto = Produto.objects.create(
            nome="Produto 1",
            slug="produto-1",
            descricao="Descrição do produto 1",
            preco=Decimal('10.50'),
            estoque=100,
            categoria=self.categoria
        )

    def get_request_with_session(self, session_data=None):
        factory = RequestFactory()
        request = factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        if session_data:
            for k, v in session_data.items():
                request.session[k] = v
            request.session.save()
        return request

    def test_adicionar_produto_ja_existe_sem_override(self):
        """Testa adicionar produto já existente sem override"""
        session_data = {
            settings.CARRINHO_SESSION_ID: {
                str(self.produto.id): {'quantidade': 1, 'preco': str(self.produto.preco)}
            }
        }
        request = self.get_request_with_session(session_data)
        carrinho = Carrinho(request)
        carrinho.adicionar(self.produto, quantidade=2, override_quantidade=False)
        self.assertEqual(carrinho.carrinho[str(self.produto.id)]['quantidade'], 3)

    def test_adicionar_produto_ja_existe_com_override(self):
        """Testa adicionar produto já existente com override"""
        session_data = {
            settings.CARRINHO_SESSION_ID: {
                str(self.produto.id): {'quantidade': 1, 'preco': str(self.produto.preco)}
            }
        }
        request = self.get_request_with_session(session_data)
        carrinho = Carrinho(request)
        carrinho.adicionar(self.produto, quantidade=5, override_quantidade=True)
        self.assertEqual(carrinho.carrinho[str(self.produto.id)]['quantidade'], 5)

    def test_iter_sem_produtos(self):
        """Testa __iter__ com carrinho vazio"""
        request = self.get_request_with_session()
        carrinho = Carrinho(request)
        items = list(carrinho)
        self.assertEqual(items, [])

    def test_limpar_sem_carrinho_na_sessao(self):
        """Testa limpar quando não há carrinho na sessão"""
        request = self.get_request_with_session()
        carrinho = Carrinho(request)
        # Remove o carrinho da sessão manualmente
        if settings.CARRINHO_SESSION_ID in request.session:
            del request.session[settings.CARRINHO_SESSION_ID]
        carrinho.limpar()  # Não deve dar erro

class CarrinhoFormsLimiteTest(TestCase):
    def test_form_quantidade_minima(self):
        form = FormAdicionarProdutoCarrinho(data={'quantidade': 1, 'override': False})
        self.assertTrue(form.is_valid())

    def test_form_quantidade_maxima(self):
        form = FormAdicionarProdutoCarrinho(data={'quantidade': 20, 'override': False})
        self.assertTrue(form.is_valid())

class CarrinhoCoberturaExtraTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.categoria = Categoria.objects.create(nome="Teste", slug="teste")
        self.produto = Produto.objects.create(
            nome="Produto Teste",
            slug="produto-teste",
            descricao="desc",
            preco=Decimal('10.00'),
            estoque=10,
            categoria=self.categoria
        )

    def get_request_with_session(self, session_data=None):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        if session_data:
            for k, v in session_data.items():
                request.session[k] = v
            request.session.save()
        return request

    def test_iter_carrinho_vazio(self):
        """Cobre o branch if not produto_ids: return iter([])"""
        request = self.get_request_with_session({
            settings.CARRINHO_SESSION_ID: {}
        })
        carrinho = Carrinho(request)
        self.assertEqual(list(carrinho), [])

    def test_iter_item_sem_produto(self):
        """Cobre o branch if 'produto' in item: (não entra no if)"""
        # Simula item sem 'produto'
        request = self.get_request_with_session({
            settings.CARRINHO_SESSION_ID: {
                '9999': {'quantidade': 1, 'preco': '5.00'}
            }
        })
        carrinho = Carrinho(request)
        # Produto 9999 não existe, então não entra no if 'produto' in item
        self.assertEqual(list(carrinho), [])

    def test_limpar_chama_salvar(self):
        """Cobre o self.salvar() mesmo sem carrinho na sessão"""
        request = self.get_request_with_session()
        carrinho = Carrinho(request)
        # Remove o carrinho da sessão manualmente
        if settings.CARRINHO_SESSION_ID in request.session:
            del request.session[settings.CARRINHO_SESSION_ID]
        # Não deve dar erro, cobre o branch final do método
        carrinho.limpar()
        self.assertNotIn(settings.CARRINHO_SESSION_ID, request.session) # Verifica se o carrinho foi removido da sessão

from .forms import FormAdicionarProdutoCarrinho
from django.test import TestCase

class CarrinhoFormsLimiteTest(TestCase):
    def test_form_quantidade_minima(self):
        form = FormAdicionarProdutoCarrinho(data={'quantidade': 1, 'override': False})
        self.assertTrue(form.is_valid())

    def test_form_quantidade_maxima(self):
        form = FormAdicionarProdutoCarrinho(data={'quantidade': 20, 'override': False})
        self.assertTrue(form.is_valid())

    def test_form_quantidade_abaixo_minimo(self):
        form = FormAdicionarProdutoCarrinho(data={'quantidade': 0, 'override': False})
        self.assertFalse(form.is_valid())

    def test_form_quantidade_acima_maximo(self):
        form = FormAdicionarProdutoCarrinho(data={'quantidade': 21, 'override': False})
        self.assertFalse(form.is_valid())

class CarrinhoViewsBranchesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(nome="Cat", slug="cat")
        self.produto = Produto.objects.create(
            nome="Produto Teste",
            slug="produto-teste",
            descricao="desc",
            preco=10,
            estoque=10,
            categoria=self.categoria
        )

    def test_adicionar_produto_get(self):
        url = reverse('carrinho:adicionar', kwargs={'produto_id': self.produto.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_adicionar_produto_inexistente(self):
        url = reverse('carrinho:adicionar', kwargs={'produto_id': 9999})
        response = self.client.post(url, data={'quantidade': 1})
        self.assertEqual(response.status_code, 404)

    def test_remover_produto_get(self):
        url = reverse('carrinho:remover', kwargs={'produto_id': self.produto.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_remover_produto_inexistente(self):
        url = reverse('carrinho:remover', kwargs={'produto_id': 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
# produtos/tests.py
import os
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.contrib.auth.models import User
from .models import Categoria, Produto


class CategoriaModelTest(TestCase):

    def setUp(self):
        self.categoria = Categoria.objects.create(
            nome='Eletrônicos',
            slug='eletronicos'
        )

    def test_categoria_creation(self):
        self.assertEqual(self.categoria.nome, 'Eletrônicos')
        self.assertEqual(self.categoria.slug, 'eletronicos')
        self.assertEqual(str(self.categoria), 'Eletrônicos')

    def test_categoria_slug_unique(self):
        with self.assertRaises(IntegrityError):
            Categoria.objects.create(
                nome='Eletrônicos 2',
                slug='eletronicos'  # Mesmo slug
            )

    def test_categoria_max_length_nome(self):
        categoria = Categoria(
            nome='A' * 100,  # 100 caracteres (limite)
            slug='categoria-longa'
        )
        categoria.full_clean()  # Não deve gerar erro

    def test_categoria_nome_too_long(self):
        from django.core.exceptions import ValidationError
        categoria = Categoria(
            nome='A' * 101,  # 101 caracteres (acima do limite)
            slug='categoria-muito-longa'
        )
        with self.assertRaises(ValidationError):
            categoria.full_clean()


class ProdutoModelTest(TestCase):

    def setUp(self):
        self.categoria = Categoria.objects.create(
            nome='Smartphones',
            slug='smartphones'
        )

        # Criar imagem fake para testes
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )

        self.produto = Produto.objects.create(
            nome='iPhone 15',
            slug='iphone-15',
            descricao='Último modelo da Apple',
            preco=Decimal('2999.99'),
            estoque=10,
            disponivel=True,
            categoria=self.categoria,
            imagem=self.test_image
        )

    def tearDown(self):
        if self.produto.imagem:
            if os.path.isfile(self.produto.imagem.path):
                os.remove(self.produto.imagem.path)

    def test_produto_creation(self):
        self.assertEqual(self.produto.nome, 'iPhone 15')
        self.assertEqual(self.produto.slug, 'iphone-15')
        self.assertEqual(self.produto.descricao, 'Último modelo da Apple')
        self.assertEqual(self.produto.preco, Decimal('2999.99'))
        self.assertEqual(self.produto.estoque, 10)
        self.assertTrue(self.produto.disponivel)
        self.assertEqual(self.produto.categoria, self.categoria)
        self.assertIsNotNone(self.produto.data_criacao)
        self.assertIsNotNone(self.produto.data_atualizacao)

    def test_produto_slug_unique(self):
        with self.assertRaises(IntegrityError):
            Produto.objects.create(
                nome='iPhone 15 Pro',
                slug='iphone-15',  # Mesmo slug
                descricao='Versão Pro',
                preco=Decimal('3499.99'),
                estoque=5,
                categoria=self.categoria
            )

    def test_produto_estoque_positive(self):
        produto = Produto(
            nome='Produto Estoque',
            slug='produto-estoque',
            descricao='Teste estoque',
            preco=Decimal('50.00'),
            estoque=-1,  # Estoque negativo
            categoria=self.categoria
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            produto.full_clean()

    def test_produto_disponivel_default(self):
        produto = Produto.objects.create(
            nome='Produto Default',
            slug='produto-default',
            descricao='Teste default',
            preco=Decimal('100.00'),
            estoque=5,
            categoria=self.categoria
        )
        self.assertTrue(produto.disponivel)


class ProdutosViewsTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Criar categorias
        self.categoria1 = Categoria.objects.create(
            nome='Eletrônicos',
            slug='eletronicos'
        )
        self.categoria2 = Categoria.objects.create(
            nome='Roupas',
            slug='roupas'
        )

        # Criar produtos
        self.produto1 = Produto.objects.create(
            nome='Smartphone',
            slug='smartphone',
            descricao='Um ótimo smartphone',
            preco=Decimal('999.99'),
            estoque=5,
            disponivel=True,
            categoria=self.categoria1
        )

        self.produto2 = Produto.objects.create(
            nome='Camiseta',
            slug='camiseta',
            descricao='Camiseta confortável',
            preco=Decimal('49.99'),
            estoque=10,
            disponivel=True,
            categoria=self.categoria2
        )

        self.produto_indisponivel = Produto.objects.create(
            nome='Produto Indisponível',
            slug='produto-indisponivel',
            descricao='Este produto não está disponível',
            preco=Decimal('199.99'),
            estoque=0,
            disponivel=False,
            categoria=self.categoria1
        )

    def test_lista_produtos_view(self):
        url = reverse('produtos:lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smartphone')
        self.assertContains(response, 'Camiseta')
        self.assertNotContains(response, 'Produto Indisponível')  # Não deve aparecer

        # Verificar contexto
        self.assertIn('produtos', response.context)
        self.assertIn('categorias', response.context)
        self.assertIsNone(response.context['categoria'])
        
        produtos = response.context['produtos']
        self.assertEqual(produtos.count(), 2)
        self.assertIn(self.produto1, produtos)
        self.assertIn(self.produto2, produtos)
        self.assertNotIn(self.produto_indisponivel, produtos)

    def test_lista_produtos_por_categoria(self):
        """Testa a view de lista de produtos filtrada por categoria"""
        url = reverse('produtos:lista_por_categoria', args=[self.categoria1.slug])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smartphone')
        self.assertNotContains(response, 'Camiseta')  # Categoria diferente
        
        # Verificar contexto
        self.assertEqual(response.context['categoria'], self.categoria1)
        produtos = response.context['produtos']
        self.assertEqual(produtos.count(), 1)
        self.assertIn(self.produto1, produtos)

    def test_detalhe_produto_view(self):
        """Testa a view de detalhe de produto"""
        url = reverse('produtos:detalhe', args=[self.produto1.id, self.produto1.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smartphone')
        self.assertContains(response, 'Um ótimo smartphone')
        self.assertContains(response, '999.99')

        # Verificar contexto
        self.assertEqual(response.context['produto'], self.produto1)
        self.assertIn('categorias', response.context)

    def test_detalhe_produto_indisponivel(self):

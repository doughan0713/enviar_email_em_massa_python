# Sistema de Automação de E-mails com DKIM

Sistema automatizado para envio em massa de e-mails HTML com suporte a assinatura DKIM, controle de limites de envio e gerenciamento de múltiplas contas SMTP.

## 🎯 E-mails Segmentados Profissionais

**Maximize seus resultados com nossa base de dados premium!**

Oferecemos **listas de e-mails segmentadas e qualificadas**, 100% em conformidade com a LGPD (Lei Geral de Proteção de Dados). Nossas listas são:

- ✨ **Segmentadas por nicho**: Alcance exatamente o público que precisa da sua solução
- 🎯 **Validadas e atualizadas**: E-mails ativos e verificados para maximizar sua taxa de entrega
- ⚖️ **Conformidade LGPD**: Todos os contatos possuem consentimento adequado para recebimento de comunicações
- 📊 **Alta conversão**: Públicos qualificados que realmente têm interesse no seu segmento
- 🚀 **Pronto para usar**: Listas formatadas e prontas para importar no sistema

**Impulsione suas campanhas com dados confiáveis e legais!** Entre em contato para conhecer nossas listas segmentadas disponíveis e turbine seus resultados de marketing.

## 📋 Características

- ✉️ Envio de e-mails HTML personalizados
- 🔐 Assinatura DKIM automática via DNS
- 📊 Sistema de log detalhado (CSV)
- ⚡ Cache de chaves DKIM (24 horas)
- 🔄 Rotação automática entre múltiplas contas
- ⏱️ Controle de limites (diário e por hora)
- 🛡️ Tratamento robusto de exceções
- 📧 Suporte a cabeçalhos List-Unsubscribe

## 🚀 Requisitos

### Bibliotecas Python

```bash
pip install dnspython dkimpy
```

### Bibliotecas Nativas
- `smtplib`
- `email`
- `csv`
- `datetime`

## ⚙️ Configuração

### 1. Configurar Contas de E-mail

Edite a lista `ACCOUNTS` no script:

```python
ACCOUNTS = [
    {
        'email': 'seu-email@dominio.com',
        'password': 'sua-senha-aqui',
        'name': 'Nome do Remetente',
        'smtp_server': 'mail.dominio.com',
        'smtp_port': 465,
        'reply_to': 'resposta@dominio.com',
        'List-Unsubscribe': 'https://dominio.com/cancelar',
        'selector': 'cloudflare',  # Opcional, padrão: 'cloudflare'
        'emails_sent_today': 0,
        'emails_sent_this_hour': 0,
        'last_sent_time': datetime.now()
    }
]
```

### 2. Configurar Limites de Envio

```python
MAX_EMAILS_PER_DAY = 500    # Limite diário por conta
MAX_EMAILS_PER_HOUR = 80    # Limite por hora por conta
```

### 3. Configurar DKIM

O sistema busca automaticamente as chaves DKIM via DNS. Certifique-se de que:
- Seu domínio possui registros DKIM configurados
- O seletor DKIM está correto (padrão: `cloudflare`)
- O registro DNS está no formato: `selector._domainkey.dominio.com`

### 4. Preparar Lista de E-mails

Crie arquivos CSV na pasta especificada com os e-mails dos destinatários:

```
pasta/
├── lista1.csv
├── lista2.csv
└── lista3.csv
```

Formato do CSV:
```
email1@exemplo.com
email2@exemplo.com
email3@exemplo.com
```

### 5. Personalizar Conteúdo HTML

Edite a variável `html_content` com seu template HTML personalizado.

## 📁 Estrutura de Arquivos

```
projeto/
├── script.py
├── log_envios.csv              # Gerado automaticamente
├── limit_reached_timestamp.txt # Controle de limites
└── pasta_emails/               # Seus arquivos CSV
    ├── lista1.csv
    └── lista2.csv
```

## 🔧 Uso

### Execução Básica

```python
folder_path = '/caminho/para/seus/csvs'
html_content = """seu HTML aqui"""

process_emails(folder_path, html_content)
```

### Execução via Terminal

```bash
python script.py
```

## 📊 Sistema de Log

O sistema gera automaticamente o arquivo `log_envios.csv` com:

| Coluna   | Descrição                    |
|----------|------------------------------|
| Email    | Endereço do destinatário     |
| DataHora | Timestamp ISO do envio       |

## 🔄 Funcionamento

1. **Inicialização**: Cria arquivo de log se não existir
2. **Leitura**: Processa todos os arquivos CSV da pasta
3. **Validação**: Remove e-mails duplicados
4. **Envio**: Rotaciona entre contas respeitando limites
5. **DKIM**: Assina automaticamente cada e-mail
6. **Log**: Registra cada envio bem-sucedido
7. **Espera**: Aguarda 50 segundos entre envios
8. **Reset**: Reinicia contadores horários quando necessário

## ⏱️ Controle de Limites

### Limite Horário
- Quando uma conta atinge o limite horário, passa para a próxima
- Se todas as contas atingirem o limite, aguarda até a próxima hora
- Contadores são resetados automaticamente

### Limite Diário
- Contas que atingem o limite diário são puladas
- Sistema continua com contas disponíveis

## 🔐 Segurança DKIM

### Cache de Chaves
- Chaves DKIM são armazenadas em cache por 24 horas
- Reduz consultas DNS repetitivas
- Melhora performance do sistema

### Validação
- Verifica formato do registro DNS
- Trata erros de domínio não encontrado
- Log de erros de assinatura

## ⚠️ Tratamento de Erros

O sistema trata:
- ❌ Falhas de conexão SMTP
- ❌ Credenciais inválidas
- ❌ Registros DKIM não encontrados
- ❌ Erros de formatação de e-mail
- ❌ Problemas de leitura de arquivos

Todos os erros são logados no console com mensagens descritivas.

## 📝 Personalização do HTML

O template HTML inclui:
- Design responsivo
- Botão CTA (Call-to-Action)
- Link de descadastro automático
- Estilos inline para compatibilidade
- Estrutura semântica

## 🛠️ Manutenção

### Limpar Logs
```python
# Deletar manualmente ou implementar rotação de logs
os.remove('log_envios.csv')
```

### Limpar Cache DKIM
```python
dkim_cache.clear()
```

### Verificar Envios
```python
# Análise do log_envios.csv
import pandas as pd
df = pd.read_csv('log_envios.csv')
print(df.groupby('Email').count())
```

## ⚡ Performance

- **Delay entre envios**: 50 segundos
- **Cache DKIM**: Reduz 95% das consultas DNS
- **Rotação de contas**: Maximiza throughput
- **Limite horário**: Evita bloqueios de servidor

## 📧 Conformidade

O sistema inclui:
- ✅ Cabeçalho `List-Unsubscribe`
- ✅ Link de descadastro no rodapé
- ✅ Assinatura DKIM
- ✅ Cabeçalho `Reply-To`
- ✅ Formato HTML responsivo

## 🐛 Troubleshooting

### E-mails não estão sendo enviados
- Verifique credenciais SMTP
- Confirme porta e servidor SMTP
- Teste conexão com o servidor

### DKIM não está funcionando
- Verifique registros DNS do domínio
- Confirme o seletor DKIM correto
- Teste com ferramentas online de validação DKIM

### Limite atingido muito rápido
- Ajuste `MAX_EMAILS_PER_HOUR`
- Adicione mais contas em `ACCOUNTS`
- Verifique se os contadores estão resetando

## 📄 Licença

Este script é fornecido como está, sem garantias. Use por sua conta e risco, respeitando as leis de spam e privacidade do seu país.

## ⚠️ Aviso Legal

**Use este sistema de forma responsável e ética:**
- Obtenha consentimento dos destinatários
- Respeite leis anti-spam (CAN-SPAM, LGPD, GDPR)
- Forneça mecanismo de descadastro funcional
- Não envie conteúdo malicioso ou enganoso

---

**Versão**: 1.0  
**Última atualização**: 2024

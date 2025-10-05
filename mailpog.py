import os
import csv
import time
import smtplib
import dkim
import dns.resolver
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from email.utils import formataddr

# Cache para armazenar as chaves DKIM temporariamente
dkim_cache = {}

def get_dkim_key(domain, selector):
    """Obtém a chave privada DKIM do registro DNS TXT, com cache de chaves."""
    cache_key = f"{selector}.{domain}"
    
    # Verifica se a chave está no cache e é recente
    if cache_key in dkim_cache:
        key_data = dkim_cache[cache_key]
        # Valida se a chave em cache ainda é válida (definido como 24 horas)
        if datetime.now() - key_data['timestamp'] < timedelta(hours=24):
            return key_data['key']
    
    try:
        # Consulta DNS para o registro DKIM
        answers = dns.resolver.resolve(f'{selector}._domainkey.{domain}', 'TXT')
        for rdata in answers:
            txt_record = rdata.to_text().replace('"', '')
            if txt_record.startswith('v=DKIM1;'):
                private_key = txt_record.split('p=')[1].strip()
                
                # Armazena a chave no cache com timestamp
                dkim_cache[cache_key] = {'key': private_key, 'timestamp': datetime.now()}
                
                return private_key
    except dns.resolver.NXDOMAIN:
        print(f"Domínio não encontrado: {domain}")
    except dns.resolver.NoAnswer:
        print(f"Sem resposta para o registro DKIM de {domain}")
    except Exception as e:
        print(f"Erro ao obter chave DKIM para {domain}: {e}")

    return None

def add_dkim_signature(message, domain, selector):
    """Adiciona assinatura DKIM à mensagem usando chave do cache ou DNS."""
    private_key = get_dkim_key(domain, selector)
    if private_key:
        try:
            dkim_header = dkim.sign(
                message.as_bytes(),
                selector.encode(),
                domain.encode(),
                private_key.encode()
            )
            message['DKIM-Signature'] = dkim_header.decode()
        except Exception as e:
            print(f"Erro ao assinar DKIM para {domain}: {e}")

# Configurações de limite de envio
MAX_EMAILS_PER_DAY = 500
MAX_EMAILS_PER_HOUR = 80
LOG_FILE = 'log_envios.csv'
LIMIT_REACHED_FILE = 'limit_reached_timestamp.txt'

# Lista de contas de e-mail, com informações adicionais para cada domínio
ACCOUNTS = [
    {
        'email': 'shopping@softpog.com.br',
        'password': '',
        'name': 'Tudo para automação',
        'smtp_server': 'mail.softpog.com.br',
        'smtp_port': 465,
        'reply_to': 'contato@softpog.com.br',
        'List-Unsubscribe': 'https://softpog.com.br/confirmar',
        'emails_sent_today': 0,  # Contagem diária
        'emails_sent_this_hour': 0,  # Contagem por hora
        'last_sent_time': datetime.now()  # Controle do último envio
    }

    # ... outras contas
]

def send_email(account, to_address, html_content):
    """Envia o e-mail com assinatura DKIM, registra log e gerencia exceções."""
    try:
        message = MIMEMultipart()
        message['From'] = formataddr((account['name'], account['email']))
        message['To'] = to_address
        message['Subject'] = "Automação de chats"
        message['Reply-To'] = account.get('reply_to', account['email'])

        if 'List-Unsubscribe' in account:
            html_content += f"<br><br><a href='{account['List-Unsubscribe']}'>Cancel</a>"
        message.attach(MIMEText(html_content, 'html'))

        domain = account['email'].split('@')[1]
        selector = account.get('selector', 'cloudflare')
        add_dkim_signature(message, domain, selector)

        with smtplib.SMTP_SSL(account['smtp_server'], account['smtp_port']) as server:
            server.login(account['email'], account['password'])
            server.send_message(message)
        print(f"Email enviado para: {to_address}")

        # Atualiza contagem de envios da conta
        account['emails_sent_today'] += 1
        account['emails_sent_this_hour'] += 1
        account['last_sent_time'] = datetime.now()
        log_email_sent(to_address)

    except Exception as e:
        print(f"Erro ao enviar email para {to_address}: {e}")

def log_email_sent(to_address):
    """Registra o e-mail enviado no log."""
    with open(LOG_FILE, mode='a', newline='') as logfile:
        log_writer = csv.writer(logfile)
        log_writer.writerow([to_address, datetime.now().isoformat()])
    print(f"Log gravado para: {to_address}")

def reset_hourly_limits():
    """Reseta o limite horário para todas as contas."""
    for account in ACCOUNTS:
        account['emails_sent_this_hour'] = 0

def initialize_log_file():
    """Inicializa o arquivo de log se não existir."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='') as logfile:
            log_writer = csv.writer(logfile)
            log_writer.writerow(['Email', 'DataHora'])
        print("Arquivo de log criado.")

def process_emails(folder_path, html_content):
    """Processa os e-mails, respeitando os limites e intercalando contas."""
    initialize_log_file()
    emails_sent = set()

    for csv_file in os.listdir(folder_path):
        if not csv_file.endswith('.csv'):
            continue

        csv_path = os.path.join(folder_path, csv_file)
        with open(csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                email_address = row[0].strip()
                if email_address in emails_sent:
                    continue

                sent = False
                for account in ACCOUNTS:
                    if account['emails_sent_today'] >= MAX_EMAILS_PER_DAY:
                        print(f"Limite diário alcançado para {account['email']}.")
                        continue
                    if account['emails_sent_this_hour'] >= MAX_EMAILS_PER_HOUR:
                        print(f"Limite horário alcançado para {account['email']}.")
                        continue

                    send_email(account, email_address, html_content)
                    emails_sent.add(email_address)
                    time.sleep(50)
                    sent = True
                    break  # Interrompe o loop de contas, pois o e-mail foi enviado

                if not sent:
                    # Se todas as contas atingiram o limite horário, aguarda até a próxima hora
                    print("Todas as contas atingiram o limite horário. Aguardando próxima hora.")
                    time_until_next_hour = (datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1) - datetime.now()).seconds
                    time.sleep(time_until_next_hour)
                    reset_hourly_limits()
                elif account['emails_sent_this_hour'] >= MAX_EMAILS_PER_HOUR:
                    reset_hourly_limits()

folder_path = '/Semestre1/earnall'
html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solução Completa de Automação</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .header {
            background-color: #4CAF50;
            color: white;
            text-align: center;
            padding: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .content {
            padding: 20px;
            color: #333333;
            line-height: 1.6;
        }
        .content h2 {
            color: #4CAF50;
            margin-top: 0;
        }
        .cta {
            text-align: center;
            margin: 20px 0;
        }
        .cta a {
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            padding: 12px 20px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 16px;
        }
        .cta a:hover {
            background-color: #45a049;
        }
        .footer {
            background-color: #f4f4f4;
            color: #666666;
            text-align: center;
            padding: 10px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>Solução Completa de Automação</h1>
        </div>
        <div class="content">
            <h2>Transforme a forma como sua empresa trabalha</h2>
            <p>Imagine ter uma infraestrutura completa para automação, já configurada e pronta para uso. Chegou a hora de automatizar seus processos de forma prática e eficiente!</p>
            <ul>
                <li><strong>Servidor seguro e configurado:</strong> Inclui 1 ano de hospedagem com proteção Cloudflare.</li>
                <li><strong>Plataformas incríveis:</strong> Typebot, Chatwoot, Evolution e n8n prontas para atender suas demandas.</li>
                <li><strong>Praticidade total:</strong> Toda a infraestrutura para que você crie fluxos e automatizações sem precisar programar.</li>
            </ul>
            <p><strong>Investimento:</strong> primordial  <span style="color: #4CAF50;"> Veja só ;)</span>.</p>
            <div class="cta">
                <a href="https://go.hotmart.com/O97199128B?dp=1">Garanta sua Solução Agora</a>
            </div>
            <p>Não perca tempo! Entre na lista de espera e transforme o potencial da sua empresa com automação prática e eficiente.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 - Sua Empresa. Todos os direitos reservados.</p>
            <p>Este é um e-mail informativo. Caso não queira receber mais mensagens, clique aqui para <a href="#">cancelar a inscrição</a>.</p>
        </div>
    </div>
</body>
</html>

"""

process_emails(folder_path, html_content)

# 🎥🎵 Conversor Distribuído de Vídeo para Áudio

Sistema distribuído e assíncrono para conversão de arquivos de vídeo em áudio, construído como projeto prático para a disciplina de **Sistemas Distribuídos**.

A arquitetura utiliza o padrão **Claim Check** e **Competing Consumers** para garantir alto desempenho, escalabilidade horizontal e resiliência no processamento de mídias.

---

## 🛠️ Tecnologias Utilizadas

* **Frontend:** [Next.js](https://nextjs.org/) + [Bootstrap 5](https://getbootstrap.com/)
* **API de Ingestão:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
* **Workers de Processamento:** Python + [FFmpeg](https://ffmpeg.org/) + [Pika](https://pika.readthedocs.io/)
* **Message Broker:** [RabbitMQ](https://www.rabbitmq.com/) (AMQP)
* **Object Storage (S3):** [SeaweedFS](https://github.com/seaweedfs/seaweedfs)
* **Banco de Dados Relacional:** [PostgreSQL 15](https://www.postgresql.org/)
* **Serviço de Notificação:** Python (SMTP Client)
* **Simulador SMTP:** [Mailpit](https://mailpit.axllent.org/)
* **Orquestração:** [Docker Compose](https://docs.docker.com/compose/)

---

## 📐 Arquitetura da Solução

```text
Frontend (Next.js) ──HTTP/REST──> API Ingestão (FastAPI) ──Publish──> RabbitMQ
                                      │                                  │
                                 PUT Original                         Deliver
                                      ▼                                  ▼
[PostgreSQL] <──Persiste Job── [SeaweedFS S3] <──GET/PUT/DELETE── Worker (Python/FFmpeg)
                                                                         │
                                                                  Publish Concluído
                                                                         ▼
[Mailpit (SMTP)] <──Send Mail── Notifier (SMTP) <────────────────────────┘
```

1. **Ingestão Assíncrona:** A API recebe o vídeo, salva no SeaweedFS, grava o *job* como `PENDENTE` no PostgreSQL e enfileira uma mensagem no RabbitMQ, liberando o cliente com um status `HTTP 202 Accepted`.
2. **Processamento:** Instâncias do *Worker* consomem a fila, baixam o vídeo do storage S3, extraem a faixa de áudio via FFmpeg, enviam o áudio convertido para o bucket público, removem o vídeo original e enviam confirmação manual (`basic_ack`).
3. **Notificação:** Um serviço dedicado de notificação consome o evento de conclusão e dispara um e-mail formatado via Mailpit.

---

## 🚀 Como Iniciar o Projeto

### Pré-requisitos
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) e **Docker Compose** instalados.

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/conversor_de_arquivos.git
cd conversor_de_arquivos
```

### 2. Subir os contêineres
Execute o comando abaixo na raiz do projeto para compilar as imagens e iniciar todos os serviços em segundo plano:

```bash
docker compose up --build -d
```

### 3. Escalar Workers (Opcional - Teste de Carga)
Para aumentar a capacidade de processamento em paralelo, você pode escalar as instâncias de *workers*:

```bash
docker compose up -d --scale worker=4
```

### 4. Parar a aplicação
Para encerrar e remover todos os contêineres ativos:

```bash
docker compose down
```

---

## 🔗 Endereços e Painéis de Acesso (`localhost`)

Após subir o ambiente com o Docker, acesse os serviços nos seguintes links:

| Serviço | URL Local | Credenciais / Observações |
| :--- | :--- | :--- |
| **Frontend Web** | [http://localhost:3000](http://localhost:3000) | Interface principal do usuário |
| **API Ingestão (Swagger Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentação interativa FastAPI |
| **RabbitMQ Management** | [http://localhost:15672](http://localhost:15672) | **Usuário:** `guest` \| **Senha:** `guest` |
| **Mailpit (Caixa de E-mails)** | [http://localhost:8025](http://localhost:8025) | Interface web do simulador SMTP |
| **SeaweedFS (S3 Gateway)** | [http://localhost:9000](http://localhost:9000) | Endpoint de arquivos do Object Storage |
| **SeaweedFS Master Console** | [http://localhost:9001](http://localhost:9001) | Painel visual de gerenciamento S3 |
| **PostgreSQL Database** | `localhost:5432` | **User:** `postgres` \| **Pass:** `postgrespassword` \| **DB:** `app_db` |

---

## 💡 Como Usar a Aplicação

1. Acesse a interface web em **[http://localhost:3000](http://localhost:3000)**.
2. Selecione um arquivo de vídeo do seu computador (formatos suportados: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`).
3. Selecione o formato de áudio desejado (`mp3`, `wav` ou `ogg`).
4. Informe o e-mail onde deseja receber a notificação.
5. Clique em **"Converter em Áudio"**.
6. Acompanhe a alteração de status na tela (`PENDENTE` $\rightarrow$ `PROCESSANDO` $\rightarrow$ `CONCLUÍDO`).
7. Quando concluído, o botão de **Download do Áudio** ficará disponível na tela.
8. Abra o **Mailpit** em **[http://localhost:8025](http://localhost:8025)** para visualizar o e-mail de notificação recebido com o link direto para descarregar o áudio.

---

## 📄 Licença

Este projeto foi desenvolvido estritamente para fins acadêmicos. Sinta-se livre para utilizar e aprimorar o código!
'use client';

import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Notification {
  type: 'danger' | 'success' | 'info' | 'warning';
  message: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [targetFormat, setTargetFormat] = useState('mp3');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<any>(null);
  const [queryJobId, setQueryJobId] = useState('');
  const [notification, setNotification] = useState<Notification | null>(null);

  const showNotification = (type: Notification['type'], message: string) => {
    setNotification({ type, message });
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotification(null);

    if (!file || !email) {
      showNotification('warning', 'Por favor, selecione um arquivo de vídeo e informe seu e-mail.');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('targetFormat', targetFormat);
    formData.append('notifyEmail', email);

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `Falha no envio do vídeo (Código HTTP: ${res.status})`);
      }

      const data = await res.json();
      setJobId(data.jobId);
      setStatusData({ status: 'PENDENTE', jobId: data.jobId });
      showNotification('success', 'Vídeo enviado com sucesso! O processamento foi iniciado.');
    } catch (err: any) {
      // Captura erros de rede (ex: API offline / porta 8000 inacessível)
      if (err.name === 'TypeError' || err.message.includes('fetch')) {
        showNotification(
          'danger',
          'Erro de Conexão (NetworkError): Não foi possível conectar à API de Ingestão. Verifique se o container da API está ativo em http://localhost:8000.'
        );
      } else {
        showNotification('danger', err.message || 'Ocorreu um erro inesperado ao realizar o upload.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
        if (res.ok) {
          const data = await res.json();
          setStatusData(data);
          if (data.status === 'CONCLUÍDO' || data.status === 'ERRO') {
            clearInterval(interval);
          }
        }
      } catch (e) {
        console.error('Erro na consulta de polling:', e);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  const handleSearchStatus = async () => {
    if (!queryJobId.trim()) {
      showNotification('warning', 'Digite um ID de Job válido para buscar.');
      return;
    }
    setNotification(null);

    try {
      const res = await fetch(`${API_URL}/api/jobs/${queryJobId.trim()}`);
      if (res.ok) {
        const data = await res.json();
        setStatusData(data);
        setJobId(data.jobId);
        showNotification('info', `Status do Job ${data.jobId} atualizado.`);
      } else {
        showNotification('danger', 'Job não encontrado. Verifique o identificador informado.');
      }
    } catch (e) {
      showNotification(
        'danger',
        'Erro de Conexão: Não foi possível obter o status do Job. A API pode estar indisponível.'
      );
    }
  };

  return (
    <main className="container py-5">
      <header className="text-center mb-5">
        <h1 className="display-5 fw-bold text-primary mb-2">Conversor de Vídeo para Áudio</h1>
        <p className="lead text-secondary">
          Envie seu vídeo (MP4, AVI, MOV) e obtenha o áudio extraído assincronamente.
        </p>
      </header>

      {/* Componente de Notificação/Alerta do Bootstrap */}
      {notification && (
        <div className={`alert alert-${notification.type} alert-dismissible fade show mb-4 shadow-sm`} role="alert">
          <div className="d-flex align-items-center">
            <span className="me-2 fs-5">
              {notification.type === 'danger' && '⚠️'}
              {notification.type === 'warning' && '⚡'}
              {notification.type === 'success' && '✅'}
              {notification.type === 'info' && 'ℹ️'}
            </span>
            <div>{notification.message}</div>
          </div>
          <button
            type="button"
            className="btn-close"
            aria-label="Close"
            onClick={() => setNotification(null)}
          ></button>
        </div>
      )}

      <div className="row g-4">
        {/* Formulário de Upload */}
        <div className="col-md-6">
          <div className="card bg-body-tertiary text-light border-secondary shadow-lg h-100">
            <div className="card-body p-4">
              <h2 className="h4 card-title mb-4 text-white">Extrair Áudio</h2>
              <form onSubmit={handleUpload}>
                <div className="mb-3">
                  <label className="form-label text-light">Arquivo de Vídeo</label>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    required
                    className="form-control bg-dark text-light border-secondary"
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label text-light">Formato de Áudio Desejado</label>
                  <select
                    value={targetFormat}
                    onChange={(e) => setTargetFormat(e.target.value)}
                    className="form-select bg-dark text-light border-secondary"
                  >
                    <option value="mp3">MP3 (Padrão)</option>
                    <option value="wav">WAV (Sem Perda)</option>
                    <option value="ogg">OGG</option>
                  </select>
                </div>

                <div className="mb-4">
                  <label className="form-label text-light">Seu E-mail para Notificação</label>
                  <input
                    type="email"
                    placeholder="aluno@exemplo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="form-control bg-dark text-light border-secondary"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary w-100 py-2 fw-semibold"
                >
                  {loading ? 'Enviando Vídeo...' : 'Converter em Áudio'}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Status */}
        <div className="col-md-6">
          <div className="card bg-body-tertiary text-light border-secondary shadow-lg h-100">
            <div className="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <h2 className="h4 card-title mb-4 text-white">Acompanhar Status</h2>

                <div className="input-group mb-4">
                  <input
                    type="text"
                    placeholder="Informe o jobId..."
                    value={queryJobId}
                    onChange={(e) => setQueryJobId(e.target.value)}
                    className="form-control bg-dark text-light border-secondary"
                  />
                  <button onClick={handleSearchStatus} className="btn btn-outline-light">
                    Buscar
                  </button>
                </div>

                {statusData ? (
                  <div className="p-3 bg-dark rounded border border-secondary">
                    <div className="mb-3">
                      <small className="text-secondary d-block">Identificador (jobId)</small>
                      <span className="font-monospace text-warning text-break">{statusData.jobId}</span>
                    </div>

                    <div className="mb-3">
                      <small className="text-secondary d-block mb-1">Status</small>
                      <span
                        className={`badge px-3 py-2 ${
                          statusData.status === 'CONCLUÍDO'
                            ? 'bg-success'
                            : statusData.status === 'PROCESSANDO'
                            ? 'bg-warning text-dark'
                            : statusData.status === 'ERRO'
                            ? 'bg-danger'
                            : 'bg-info text-dark'
                        }`}
                      >
                        {statusData.status}
                      </span>
                    </div>

                    {statusData.resultUrl && (
                      <div className="mt-3">
                        <small className="text-secondary d-block mb-2">Áudio Pronto para Download</small>
                        <a
                          href={statusData.resultUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-success font-semibold px-4"
                        >
                          Baixar Áudio (.{targetFormat})
                        </a>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-secondary fst-italic">Nenhum pedido em acompanhamento.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
import 'bootstrap/dist/css/bootstrap.min.css';
import './globals.css';

export const metadata = {
  title: 'Conversor Escalável de Mídia',
  description: 'Sistema assíncrono de conversão de imagem, áudio e vídeo.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" data-bs-theme="dark">
      <body className="bg-dark text-light min-vh-100">
        {children}
      </body>
    </html>
  );
}
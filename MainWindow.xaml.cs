using System;
using System.Windows;
using System.Runtime.InteropServices;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace StarkGestures
{
    public partial class MainWindow : Window
    {
        [DllImport("user32.dll")]
        static extern bool SetCursorPos(int X, int Y);

        [DllImport("user32.dll")]
        public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);

        private const int MOUSEEVENTF_LEFTDOWN = 0x02;
        private const int MOUSEEVENTF_LEFTUP = 0x04;
        private const int MOUSEEVENTF_WHEEL = 0x0800;

        private bool _isClicked = false;
        private double _ratoXAtual = 0;
        private double _ratoYAtual = 0;
        private int _ultimoYParaScroll = 0;

        public MainWindow()
        {
            InitializeComponent();
            // Iniciamos a escuta assim que o programa abre
            Task.Run(() => EscutarCerebroPython());
        }

        private void EscutarCerebroPython()
        {
            // Criamos o servidor na porta 5052
            UdpClient udpServer = new UdpClient(5052);
            // IP de escuta (qualquer um que venha para esta porta)
            IPEndPoint remoteEP = new IPEndPoint(IPAddress.Any, 5052);

            double larguraEcra = SystemParameters.PrimaryScreenWidth;
            double alturaEcra = SystemParameters.PrimaryScreenHeight;

            while (true)
            {
                try
                {
                    byte[] dados = udpServer.Receive(ref remoteEP);
                    string mensagem = Encoding.UTF8.GetString(dados);
                    string[] partes = mensagem.Split(',');

                    if (partes.Length == 3)
                    {
                        double x = double.Parse(partes[0]);
                        double y = double.Parse(partes[1]);
                        int acao = int.Parse(partes[2]);

                        // Converte as coordenadas do Python (640x480) para o teu monitor
                        double alvoX = (x / 640.0) * larguraEcra;
                        double alvoY = (y / 480.0) * alturaEcra;

                        // Suaviza o movimento (quanto maior o número, mais lento e suave)
                        _ratoXAtual += (alvoX - _ratoXAtual) / 3.0;
                        _ratoYAtual += (alvoY - _ratoYAtual) / 3.0;

                        int finalX = (int)_ratoXAtual;
                        int finalY = (int)_ratoYAtual;

                        Application.Current.Dispatcher.Invoke(() =>
                        {
                            // Sempre movemos o rato para onde a mão aponta
                            SetCursorPos(finalX, finalY);

                            if (acao == 1) // CLIQUE
                            {
                                if (!_isClicked)
                                {
                                    mouse_event(MOUSEEVENTF_LEFTDOWN, finalX, finalY, 0, 0);
                                    _isClicked = true;
                                }
                            }
                            else if (acao == 0) // MOVER (Soltar clique)
                            {
                                if (_isClicked)
                                {
                                    mouse_event(MOUSEEVENTF_LEFTUP, finalX, finalY, 0, 0);
                                    _isClicked = false;
                                }
                                _ultimoYParaScroll = finalY;
                            }
                            else if (acao == 2) // SCROLL
                            {
                                int deltaY = _ultimoYParaScroll - finalY;
                                if (Math.Abs(deltaY) > 10)
                                {
                                    int forca = (deltaY > 0) ? 120 : -120;
                                    mouse_event(MOUSEEVENTF_WHEEL, 0, 0, forca, 0);
                                    _ultimoYParaScroll = finalY;
                                }
                            }
                        });
                    }
                }
                catch { /* Erro de rede ignorado para não travar */ }
            }
        }
    }
}
using System;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace StarkGestures
{
    public partial class MainWindow : Window
    {
        // 1. IMPORTAR A "MAGIA" DO WINDOWS (user32.dll)
        [DllImport("user32.dll")]
        static extern bool SetCursorPos(int X, int Y);

        [DllImport("user32.dll")]
        static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);

        // Códigos hexadecimais para o clique esquerdo do rato
        private const uint MOUSEEVENTF_LEFTDOWN = 0x02;
        private const uint MOUSEEVENTF_LEFTUP = 0x04;

        // NOVOS: Códigos hexadecimais para o clique direito do rato
        private const uint MOUSEEVENTF_RIGHTDOWN = 0x08;
        private const uint MOUSEEVENTF_RIGHTUP = 0x10;



        // Variáveis do sistema UDP
        private UdpClient udpClient;
        private bool isRunning = true;
        private bool isClicked = false;
        private bool isRightClicked = false;

        public MainWindow()
        {
            InitializeComponent();
            IniciarReatorUDP();
        }

        // 2. O RECEPTOR DE MENSAGENS (Roda em segundo plano)
        private async void IniciarReatorUDP()
        {
            udpClient = new UdpClient(5052);

            await Task.Run(async () =>
            {
                while (isRunning)
                {
                    try
                    {
                        // Fica à espera que o Python envie os dados
                        var result = await udpClient.ReceiveAsync();
                        string data = Encoding.UTF8.GetString(result.Buffer);

                        // Envia a string (ex: "0.5,0.3,1") para ser processada
                        ProcessarMovimento(data);
                    }
                    catch (Exception)
                    {
                        // Ignora erros quando o sistema é encerrado
                    }
                }
            });
        }

        // 3. O TRADUTOR DE MOVIMENTOS
        private void ProcessarMovimento(string data)
        {
            string[] partes = data.Split(',');

            // Verifica se a string tem as 3 partes exatas (X, Y, Ação)
            if (partes.Length == 3)
            {
                // Converte as strings para números usando formato universal para evitar erros de vírgulas/pontos
                if (double.TryParse(partes[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double x) &&
                    double.TryParse(partes[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double y) &&
                    int.TryParse(partes[2], out int acao))
                {
                    // Precisamos da Dispatcher para aceder às informações do monitor de forma segura
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        // Descobre o tamanho real do seu ecrã (ex: 1920x1080)
                        int screenWidth = (int)SystemParameters.PrimaryScreenWidth;
                        int screenHeight = (int)SystemParameters.PrimaryScreenHeight;

                        // Mapeia o valor de 0 a 1 para os píxeis reais
                        int mouseX = (int)(x * screenWidth);
                        int mouseY = (int)(y * screenHeight);

                        // AÇÃO A: Mover o rato
                        SetCursorPos(mouseX, mouseY);

                        // AÇÃO B: Controlar os Cliques (Ação 1 = Pinça fechada / Clicar e Segurar)
                        if (acao == 1 && !isClicked)
                        {
                            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); // Aperta o botão
                            isClicked = true;
                        }
                        else if (acao != 1 && isClicked)
                        {
                            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
                            isClicked = false;
                        }

                        // Clique Direito (Ação 2)
                        if (acao == 2 && !isRightClicked)
                        {
                            mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0);
                            isRightClicked = true;
                        }
                        else if (acao != 2 && isRightClicked)
                        {
                            mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0);
                            isRightClicked = false;
                        }
                    });
                }
            }
        }

        // 4. DESLIGAR EM SEGURANÇA
        protected override void OnClosed(EventArgs e)
        {
            isRunning = false;
            udpClient?.Close();
            base.OnClosed(e);
        }
    }
}
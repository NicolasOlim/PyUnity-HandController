# 🦾 StarkGestures (Interface de Visão Computacional)

> **Controle o seu computador com as mãos, inspirado na interface do Tony Stark.**

O **StarkGestures** é um projeto de visão computacional em tempo real que mapeia os movimentos da sua mão através de uma webcam e os traduz em comandos nativos do Windows (mover o cursor, clicar e fazer scroll). 

O sistema utiliza uma arquitetura dividida: um "Cérebro" em Python que processa as imagens e deteta os gestos, e um "Corpo" em C# (WPF) que recebe esses dados instantaneamente e executa as ações no sistema operativo.

---

## ✨ Funcionalidades

* **Rastreamento em Tempo Real:** Segue a ponta do dedo indicador para mover o cursor do rato pelo ecrã com alta precisão.
* **Clique por Pinça:** Juntar o dedo indicador e o polegar simula o "Clique Esquerdo" (permite clicar, arrastar janelas e selecionar texto).
* **Scroll Intuitivo:** Baixar o dedo indicador e o dedo médio simultaneamente faz scroll nas páginas.
* **Comunicação de Ultra-Baixa Latência:** Utiliza Sockets UDP locais (porta `5052`) para garantir que o movimento da mão reflete instantaneamente no ecrã.
* **[ADICIONE OUTRA FUNCIONALIDADE AQUI, SE HOUVER]**

---

## 🧠 Arquitetura do Sistema

A comunicação entre os módulos é feita através de uma ponte UDP:

1. **Visão (Python - `cerebro.py`):** Utiliza a biblioteca `OpenCV` para capturar o feed da webcam e o motor `MediaPipe` da Google para extrair as coordenadas (Landmarks) dos 21 pontos da mão.
2. **Ponte (UDP Socket):** O Python formata os dados numa string simples (`X,Y,Acao`) e envia-os para o endereço `127.0.0.1:5052`.
3. **Ação (C# WPF - `MainWindow.xaml.cs`):** Um servidor local à escuta recebe as coordenadas, mapeia-as para a resolução do monitor e utiliza chamadas nativas do Windows (`user32.dll`) para forçar o movimento e os cliques do rato.

---

## 🛠️ Pré-requisitos e Instalação

Para garantir o funcionamento perfeito e evitar problemas de compatibilidade (especialmente com as bibliotecas C++ internas do MediaPipe), siga estes passos rigorosamente.

### Requisitos do Sistema
* **Sistema Operativo:** Windows 10 ou 11.
* **Python:** Recomendado **Python 3.12** (versões mais recentes ou muito antigas podem causar conflitos com o MediaPipe).
* **Visual Studio:** Para compilar e executar o projeto C# (`StarkGestures.sln`).
* Pacote [Microsoft Visual C++ Redistributable (x64)](https://learn.microsoft.com/pt-pt/cpp/windows/latest-supported-vc-redist) instalado.

### Configuração do Ambiente Python
Abra o terminal na pasta raiz do projeto e instale as dependências. **Nota importante:** É crucial usar esta versão específica do MediaPipe.

```bash
pip install opencv-python mediapipe==0.10.13 --no-cache-dir

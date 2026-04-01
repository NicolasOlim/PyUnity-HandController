# -*- coding: utf-8 -*-
import cv2
import mediapipe as mp
import socket
import math
import numpy as np

# 1. CONFIGURAÇÃO DA COMUNICAÇÃO UDP (A Ponte)
UDP_IP = "127.0.0.1"
UDP_PORT = 5052
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 2. INICIALIZAÇÃO DO MOTOR DE VISÃO (Confiança aumentada para 80%)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# =====================================================================
# 🛠️ CALIBRAÇÃO STARK MARK V (HISTERESE E FLUIDEZ)
# =====================================================================
margem_camera = 130  # Zona de conforto um pouco maior
suavizacao = 5       # Amortecedor ideal para não arrastar muito

plocX, plocY = 0.0, 0.0
clocX, clocY = 0.0, 0.0

# NOVO: Travas Magnéticas de Clique (Histerese)
clique_esq_ativo = False
clique_dir_ativo = False
limiar_apertar = 0.04  # Distância curta para ATIVAR o clique
limiar_soltar = 0.06   # Distância maior para DESATIVAR (evita soltar sem querer)
# =====================================================================

cap = cv2.VideoCapture(0)
print("SISTEMA STARK: Motor Mark V online. Fluidez máxima e bloqueio magnético de cliques.")

while cap.isOpened():
    sucesso, frame = cap.read()
    if not sucesso:
        continue

    h, w, c = frame.shape
    frame = cv2.flip(frame, 1)
    
    # Desenha o HUD
    cv2.rectangle(frame, (margem_camera, margem_camera), (w - margem_camera, h - margem_camera), (255, 0, 255), 2)

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = hands.process(img_rgb)

    if resultados.multi_hand_landmarks:
        for hand_landmarks in resultados.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            indicador = hand_landmarks.landmark[8]
            medio = hand_landmarks.landmark[12]
            polegar = hand_landmarks.landmark[4]

            # --- RASTREAMENTO MAIS FLUIDO ---
            x_pixel = indicador.x * w
            y_pixel = indicador.y * h

            x_mapeado = np.interp(x_pixel, (margem_camera, w - margem_camera), (0, 1))
            y_mapeado = np.interp(y_pixel, (margem_camera, h - margem_camera), (0, 1))

            # Trava de Segurança: Garante que os valores nunca passam de 0 ou 1
            x_mapeado = np.clip(x_mapeado, 0.0, 1.0)
            y_mapeado = np.clip(y_mapeado, 0.0, 1.0)

            # Amortecedor Inercial (Suavização Clássica)
            clocX = plocX + (x_mapeado - plocX) / suavizacao
            clocY = plocY + (y_mapeado - plocY) / suavizacao
            
            plocX, plocY = clocX, clocY

            # --- NOVO SISTEMA DE CLIQUES (HISTERESE) ---
            dist_esq = math.hypot(indicador.x - polegar.x, indicador.y - polegar.y)
            dist_dir = math.hypot(medio.x - polegar.x, medio.y - polegar.y)
            
            # Avalia a trava magnética do Clique Esquerdo
            if dist_esq < limiar_apertar:
                clique_esq_ativo = True
            elif dist_esq > limiar_soltar:
                clique_esq_ativo = False

            # Avalia a trava magnética do Clique Direito
            if dist_dir < limiar_apertar:
                clique_dir_ativo = True
            elif dist_dir > limiar_soltar:
                clique_dir_ativo = False

            # Define a ação final a ser enviada
            acao = 0 
            if clique_esq_ativo:
                acao = 1
                cv2.circle(frame, (int(indicador.x * w), int(indicador.y * h)), 15, (0, 255, 0), cv2.FILLED)
            elif clique_dir_ativo:
                acao = 2
                cv2.circle(frame, (int(medio.x * w), int(medio.y * h)), 15, (255, 0, 0), cv2.FILLED)

            # 4. DISPARAR DADOS
            mensagem = f"{clocX},{clocY},{acao}"
            sock.sendto(mensagem.encode('utf-8'), (UDP_IP, UDP_PORT))

    cv2.imshow("Jarvis Vision - Mark V", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        print("SISTEMA STARK: Encerrando...")
        break

cap.release()
cv2.destroyAllWindows()
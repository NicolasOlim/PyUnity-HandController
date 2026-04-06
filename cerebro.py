# -*- coding: utf-8 -*-
import cv2
import mediapipe as mp
import socket
import math
import numpy as np

# 1. COMUNICAÇÃO UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 5052
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 2. MOTOR DE VISÃO
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# =====================================================================
# 🛠️ CALIBRAÇÃO STARK MARK IX (FILTRO ADAPTATIVO CONTÍNUO)
# =====================================================================
margem_X = 200  
margem_Y = 130  

plocX, plocY = 0.0, 0.0
clocX, clocY = 0.0, 0.0

clique_esq_ativo = False
clique_dir_ativo = False
limiar_apertar = 0.04  
limiar_soltar = 0.06   
# =====================================================================

cap = cv2.VideoCapture(0)
print("SISTEMA STARK: Motor Mark IX online. Filtro Adaptativo Contínuo ativado.")

while cap.isOpened():
    sucesso, frame = cap.read()
    if not sucesso:
        continue

    h, w, c = frame.shape
    frame = cv2.flip(frame, 1)
    
    cv2.rectangle(frame, (margem_X, margem_Y), (w - margem_X, h - margem_Y), (255, 0, 255), 2)

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = hands.process(img_rgb)

    if resultados.multi_hand_landmarks:
        for hand_landmarks in resultados.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            indicador = hand_landmarks.landmark[8]
            medio = hand_landmarks.landmark[12]
            polegar = hand_landmarks.landmark[4]

            # --- MAPEAMENTO DE ALTO ALCANCE ---
            x_pixel = indicador.x * w
            y_pixel = indicador.y * h

            x_mapeado = np.interp(x_pixel, (margem_X, w - margem_X), (0, 1))
            y_mapeado = np.interp(y_pixel, (margem_Y, h - margem_Y), (0, 1))

            x_mapeado = np.clip(x_mapeado, 0.0, 1.0)
            y_mapeado = np.clip(y_mapeado, 0.0, 1.0)

            # --- FILTRO ADAPTATIVO CONTÍNUO ---
            # Calcula a velocidade exata da mão neste frame
            velocidade = math.hypot(x_mapeado - plocX, y_mapeado - plocY)
            
            if velocidade < 0.002:
                # ZONA MORTA: Se o movimento for menor que 0.2%, ignora (corta o tremor)
                suavizacao = 1.0 
                x_mapeado, y_mapeado = plocX, plocY 
            else:
                # TRANSIÇÃO SUAVE: Interpola o amortecedor baseado na velocidade real
                # Se for lento (0.002), suavização = 12 (Muito estável)
                # Se for rápido (0.05+), suavização = 2 (Muito rápido e sem lag)
                suavizacao = np.interp(velocidade, [0.002, 0.05], [12, 2])

            clocX = plocX + (x_mapeado - plocX) / suavizacao
            clocY = plocY + (y_mapeado - plocY) / suavizacao
            
            plocX, plocY = clocX, clocY

            # --- SISTEMA DE CLIQUES (HISTERESE) ---
            dist_esq = math.hypot(indicador.x - polegar.x, indicador.y - polegar.y)
            dist_dir = math.hypot(medio.x - polegar.x, medio.y - polegar.y)
            
            if dist_esq < limiar_apertar:
                clique_esq_ativo = True
            elif dist_esq > limiar_soltar:
                clique_esq_ativo = False

            if dist_dir < limiar_apertar:
                clique_dir_ativo = True
            elif dist_dir > limiar_soltar:
                clique_dir_ativo = False

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

    cv2.imshow("Jarvis Vision - Mark IX", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        print("SISTEMA STARK: Encerrando...")
        break

cap.release()
cv2.destroyAllWindows()
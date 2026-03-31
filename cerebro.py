# -*- coding: utf-8 -*-
import cv2
import socket
import math
import mediapipe as mp

# Inicializacao do Mediapipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Configuracao do Socket UDP para o Unity/C#
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("127.0.0.1", 5052)

# Configuracao da deteccao
detector = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
cap = cv2.VideoCapture(0)

print("SISTEMA STARK: Camera iniciada com sucesso!")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Inverter a imagem para parecer um espelho e converter cores
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Processar a imagem
    res = detector.process(rgb)
    
    if res.multi_hand_landmarks:
        for lm in res.multi_hand_landmarks:
            # Desenhar as linhas na mao
            mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
            
            # Pegar os pontos de interesse
            dedo = lm.landmark[8]
            polegar = lm.landmark[4]
            medio = lm.landmark[12]
            
            # Converter para coordenadas da tela
            ix, iy = int(dedo.x * w), int(dedo.y * h)
            px, py = int(polegar.x * w), int(polegar.y * h)
            
            # Verificar se os dedos estao levantados
            i_u = dedo.y < lm.landmark[6].y
            m_u = medio.y < lm.landmark[10].y
            
            acao = 0 
            # Logica de acoes
            if i_u and m_u: 
                acao = 2 
            elif i_u:
                distancia = math.hypot(ix - px, iy - py)
                if distancia < 35: 
                    acao = 1 
            
            # Enviar dados (X, Y, Acao)
            msg = f"{int(dedo.x*640)},{int(dedo.y*480)},{acao}"
            sock.sendto(msg.encode(), dest)

    cv2.imshow("Jarvis Vision", frame)
    # Pressionar 'ESC' para fechar
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
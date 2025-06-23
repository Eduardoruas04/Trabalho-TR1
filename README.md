 # Simulador de Comunicação — Camada Física e Camada de Enlace

 Este projeto simula o funcionamento completo das camadas Física e de Enlace de um sistema de comunicação digital, como parte do Trabalho Final da disciplina Teleinformática e Redes 1.

## Objetivo

> Desenvolver um simulador educativo e interativo que implemente:

> Protocolos de enquadramento e detecção/correção de erros da camada de enlace;

> Modulações digitais e por portadora da camada física;

> Interface gráfica (GUI) para simulação visual do sinal modulado.

## Funcionalidades Implementadas

    1. Camada Física:

    1.1 Modulações Digitais (Banda Base):

        > NRZ-Polar

        > Manchester

        > Bipolar

    1.2 Modulações por Portadora:

        > ASK (Amplitude Shift Keying)

        > FSK (Frequency Shift Keying)

        > 8-QAM (Quadrature Amplitude Modulation)
    
    2. Camada de Enlace

    2.1 Enquadramento de Dados:

        > Contagem de caracteres

        > Byte Stuffing com FLAG e ESC

        > Bit Stuffing com FLAG (01111110)
    
    2.2 Detecção e Correção de Erros:

        > Bit de paridade par

        > RC-32 (IEEE 802)

        > Código de Hamming (simulado)



## Interface Gráfica (GTK 3)

A interface construída com GTK 3 permite:

    1.Entrada da mensagem a ser transmitida;

    2.Escolha do tipo de enquadramento, detecção/correção de erros e modulação;

    3.Visualização do sinal resultante no gráfico.


## Estrutura dos Arquivos

Camada_fisica.py: Funções de modulação da camada física
Camada_enlace.py: Funções de enquadramento e controle de erro
interface_gui.py: Interface gráfica GTK para simulação


## Execução

Para executar a interface gráfica: python3 interface_gui.py

## Tecnologias Utilizadas

- Python 3

- GTK 3 (PyGObject)

 - Matplotlib

- NumPy
       





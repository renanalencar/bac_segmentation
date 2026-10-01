# Plano de Atividades e Tarefas do Projeto BAC Segmentation (TODOs)

Este documento organiza as atividades pendentes para a replicação e extensão do estudo *Dapamede et al. (2026, European Heart Journal)* com Explainable AI (XAI), estruturadas a partir das deliberações e planejamento registrados em [`.context/perplexity-history.md`](../.context/perplexity-history.md).

As tarefas estão categorizadas em ordem de prioridade decrescente (**P0 - Crítica/Imediata** a **P4 - Futura/Dependente**), com estimativas de impacto, dependências e critérios de aceitação.

---

## 📊 Matriz de Resumo e Status

| Nível | Foco Principal | Prazo Estimado | Bloqueadores Principais |
| :--- | :--- | :--- | :--- |
| **P0 (Crítica)** | Desbloqueio da Anotação INbreast e Correções de Caminhos | 1 a 2 semanas | Decisão final do lote e setup do CVAT |
| **P1 (Alta)** | Conclusão de Anotações, Conversão de Máscaras e Submissão EMBED | 2 a 4 semanas | Tempo de trabalho do radiologista |
| **P2 (Média-Alta)** | Treinamento Real do MiT + MLP e Avaliação de Métricas | 4 a 6 semanas | Conclusão das máscaras do P1 |
| **P3 (Média-Alta)** | Implementação do Pipeline de Explainable AI (XAI: Grad-CAM / SHAP) | 6 a 8 semanas | Modelo treinado do P2 |
| **P4 (Média)** | Ingestão do EMBED e Validação Externa / Transfer Learning | A definir | Aprovação de acesso pelo HitiLab |
| **P5 (Longa/Futura)** | Análise Estatística de Sobrevivência (Cox, Kaplan-Meier, Fine-Gray) | A definir | Disponibilidade de desfechos clínicos (MACE) |

---

## 🔴 Prioridade 0 (P0) — Desbloqueio da Anotação e Ajustes Estruturais (Imediata)

O objetivo desta fase é deixar o conjunto de dados piloto (INbreast) pronto para o radiologista iniciar as anotações sem atritos, além de corrigir pendências do código.

### 1.1 Filtragem Final para Incidência MLO (`filter_by_view_final.py`)
- [ ] **Descrição**: Filtrar as 280 imagens já selecionadas por laudo em `data/external/inbreast/for_annotation/` para manter exclusivamente as incidências MLO (Mediolateral Oblique), resultando em ~140 imagens.
- [ ] **Justificativa**: O estudo foca em incidências MLO (mais ortogonais ao trajeto das artérias mamárias); reduz o custo e o tempo de anotação clínica em 50%.
- [ ] **Ação**: Criar e executar `src/data/filter_by_view_final.py`, populando `data/external/inbreast/for_annotation_mlo/`.
- [ ] **Critério de Aceitação**: Diretório `for_annotation_mlo/` gerado com ~140 imagens PNG e arquivo `metadata_mlo.json` correspondente.

### 1.2 Empacotamento do Lote para Anotação
- [ ] **Descrição**: Gerar o arquivo compactado `data/external/inbreast/inbreast_mlo_images.zip`.
- [ ] **Ação**: Executar comando de compactação no diretório de imagens filtradas.
- [ ] **Critério de Aceitação**: Arquivo `.zip` com integridade validada e tamanho aproximado entre 250 MB e 400 MB.

### 1.3 Correção de Caminhos Inconsistentes no Código
- [ ] **Descrição**: Ajustar scripts em `src/data/` que possuem referências hardcoded para `data/inbreast/` em vez de `data/external/inbreast/` ou que não suportam passagem de argumentos via CLI.
- [ ] **Arquivos a revisar**:
  - `src/data/filter_by_medical_reports.py`
  - `src/data/prepare_inbreast_for_annotation.py`
  - `src/data/cvat_export_to_masks.py`
- [ ] **Critério de Aceitação**: Todos os scripts executando sem erros apontando para a estrutura física real de dados.

### 1.4 Implantação do Servidor CVAT (Docker)
- [ ] **Descrição**: Subir o container Docker do CVAT (Computer Vision Annotation Tool) no homelab ou máquina local.
- [ ] **Ação**:
  - Executar `docker compose up -d` do CVAT.
  - Criar usuário administrador e credenciais de acesso restrito para o radiologista.
  - Configurar tunelamento seguro para acesso externo (Cloudflare Tunnel, ngrok ou Tailscale).
- [ ] **Critério de Aceitação**: Painel web do CVAT acessível remotamente pelo navegador via HTTPS com login funcionando.

### 1.5 Criação da Tarefa de Anotação no CVAT
- [ ] **Descrição**: Criar a Task no CVAT para o lote MLO com os parâmetros alinhados no histórico:
  - **Name**: `INbreast BAC Annotation - Batch 1`
  - **Project**: `BAC Segmentation - INbreast`
  - **Subset**: vazio ou `Train`
  - **Sorting method**: `Natural`
  - **Image Quality**: `95%`
  - **Validation mode**: `None`
  - **Labels**: `BAC` (cor destacada) e `uncertain` (opcional)
- [ ] **Upload**: Subir `inbreast_mlo_images.zip`.
- [ ] **Critério de Aceitação**: Tarefa criada com todas as ~140 imagens carregadas e visualizáveis no canvas do CVAT.

### 1.6 Recrutamento e Treinamento do Radiologista
- [ ] **Descrição**: Formalizar o convite com a candidata / candidato a radiologista.
- [ ] **Ação**:
  - Enviar carta-convite e minuta de termo de colaboração (`docs/cvat/RADIOLOGIST_COLLABORATION_AGREEMENT.md`).
  - Compartilhar o guia de anotação (`docs/cvat/CVAT_USER_GUIDE.md` e `ANNOTATION_GUIDE.md`).
  - Realizar reunião de alinhamento técnico (30 min) e revisar o lote piloto de teste (primeiras 5 imagens).
- [ ] **Critério de Aceitação**: Radiologista cadastrado no CVAT e primeiras 5 imagens de teste validadas com sucesso.

---

## 🟠 Prioridade 1 (P1) — Execução da Anotação, Ingestão de Máscaras e Solicitação EMBED

### 2.1 Conclusão do Lote de Anotações Clínicas
- [ ] **Descrição**: Acompanhamento do progresso do radiologista na anotação de calcificações vasculares/arteriais no CVAT.
- [ ] **Critério de Aceitação**: 100% das imagens da tarefa com status de anotação concluído.

### 2.2 Exportação COCO 1.0 e Conversão para Máscaras Binárias PNG
- [ ] **Descrição**: Exportar as anotações do CVAT no formato `COCO 1.0` (`annotations.json`).
- [ ] **Ação**: Executar `src/data/cvat_export_to_masks.py` para gerar máscaras binárias (0 = fundo, 255 = BAC) no tamanho original da imagem.
- [ ] **Critério de Aceitação**: Diretório de máscaras populado com máscaras PNG binárias alinhadas 1:1 com as imagens originais.

### 2.3 Geração de Splits Estratificados
- [ ] **Descrição**: Pré-processar imagens e máscaras para 1024x1024 com padding e normalização, gerando a estrutura estratificada definitiva.
- [ ] **Ação**: Executar `src/features/build_features.py` para produzir:
  - `data/processed/train/{images,masks}` (~70%)
  - `data/processed/val/{images,masks}` (~15%)
  - `data/processed/test/{images,masks}` (~15%)
- [ ] **Critério de Aceitação**: Estrutura `data/processed/` pronta com JSONs de metadados e distribuição de severidade calculada.

### 2.4 Submissão da Solicitação de Acesso ao EMBED (HitiLab)
- [ ] **Descrição**: Submeter o formulário oficial de solicitação de acesso aos dados do EMBED junto ao laboratório do Dr. Hari Trivedi (Emory HITI).
- [ ] **Ação**: Utilizar as respostas em inglês revisadas na mensagem 72 do histórico (descrição da pesquisa, hipótese clínica, armazenamento em workstation local com BitLocker, sem envio para nuvem, conformidade HIPAA).
- [ ] **Critério de Aceitação**: Formulário submetido e protocolo de confirmação registrado.

### 2.5 Criação de Testes Automatizados Unitários (`make test`)
- [ ] **Descrição**: Adicionar testes unitários com `pytest` cobrindo os módulos fundamentais do projeto.
- [ ] **Ação**:
  - Criar `tests/test_architecture.py` (verificação de shapes e forward pass do MixVisionTransformer, MLPDecoder e BACSegmentationModel).
  - Criar `tests/test_dataset.py` (carregamento de imagens, máscaras e transformações do Albumentations).
  - Criar `tests/test_metrics.py` (cálculo de Dice, IoU, conversão de área por pixel spacing e classificação de severidade).
- [ ] **Critério de Aceitação**: Execução com sucesso de `make test` via `uv run pytest tests/ -v --cov=src`.

---

## 🟡 Prioridade 2 (P2) — Treinamento do Modelo e Validação Científica

O objetivo desta fase é validar a replicação das métricas descritas em *Dapamede et al. (2026)* sobre os dados reais anotados.

### 3.1 Treinamento do Mix Vision Transformer (MiT) + MLP Decoder
- [ ] **Descrição**: Treinar o modelo de segmentação com os dados reais processados.
- [ ] **Parâmetros recomendados**:
  - Resolução: 1024x1024 grayscale (1 canal)
  - Épocas: 100 a 150 épocas
  - Otimizador: AdamW ($\text{lr} = 5\times 10^{-5}$ a $1\times 10^{-4}$, weight decay 0.01) com Cosine Annealing
  - Hardware: GPU NVIDIA (CUDA) com checkpointing a cada 5 épocas
- [ ] **Ação**: Executar `src/models/train_model.py`.
- [ ] **Critério de Aceitação**: Checkpoint `models/best_model.pth` gerado com menor perda de validação e histórico em `models/training_history.json`.

### 3.2 Otimização da Função de Perda para Desbalanceamento
- [ ] **Descrição**: Avaliar e calibrar a perda combinada ($\text{Loss} = \alpha \cdot \text{DiceLoss} + \beta \cdot \text{FocalLoss}$ ou $\text{BCE}$) para maximizar o recall de calcificações vasculares finas sem inflar falsos positivos no parênquima fibrogladular denso.
- [ ] **Critério de Aceitação**: Curvas de convergência estáveis sem platô prematuro no Dice Score de validação.

### 3.3 Avaliação Quantitativa no Conjunto de Teste
- [ ] **Descrição**: Executar predições no test set e computar as métricas para comparação formal com a literatura:
  - **Métricas de Segmentação**: Coeficiente de Dice ($\text{meta} > 0.70$), IoU ($\text{meta} > 0.55$), Acurácia de Pixel.
  - **Métricas de Quantificação de Área (em mm²)**:
    - MAE (Mean Absolute Error): meta de referência do artigo $= 3.94\text{ mm}^2$.
    - Coeficiente de Determinação: $R^2 \ge 0.85$ (artigo $= 0.91$).
    - Correlação de Pearson: $r \ge 0.90$ (artigo $= 0.95$).
  - **Matriz de Confusão por Faixas de Severidade**:
    - Zero ($0\text{ mm}^2$)
    - Leve ($0\text{--}10\text{ mm}^2$)
    - Moderada ($10\text{--}25\text{ mm}^2$)
    - Severa ($\ge 25\text{ mm}^2$)
- [ ] **Critério de Aceitação**: Relatório em `reports/` com tabela comparativa entre os resultados obtidos e as métricas do artigo base.

### 3.4 Geração de Painéis Visuais de Predição
- [ ] **Descrição**: Executar `src/visualization/visualize.py` para produzir figuras de comparação lado a lado (Imagem original, Máscara ground truth, Predição do modelo, Sobreposição com erro).
- [ ] **Critério de Aceitação**: Figuras salvas em alta resolução em `reports/figures/`.

---

## 🟢 Prioridade 3 (P3) — Implementação de Explainable AI (XAI)

Principal contribuição inédita do projeto: explicar mecanisticamente as decisões do modelo de segmentação para aumentar a confiabilidade clínica em radiologia.

### 4.1 Módulo de Grad-CAM para Vision Transformers
- [ ] **Descrição**: Implementar técnica de ativação de classes ponderada por gradientes adaptada para o encoder Mix Transformer hierárquico.
- [ ] **Ação**:
  - Criar `src/visualization/gradcam.py`.
  - Capturar gradientes e ativações do último bloco do MiT (Estágio 4) e de estágios intermediários (Estágio 2/3).
  - Gerar heatmaps sobrepostos à imagem mamográfica original.
- [ ] **Objetivo Clínico**: Provar visualmente que o modelo ativa ao longo de estruturas lineares vasculares contínuas e em "trilho de trem" (*tram-track*), sem ser influenciado por calcificações ductais redondas/agrupadas ou clipes metálicos.
- [ ] **Critério de Aceitação**: Mapas Grad-CAM gerados e salvos para amostras das 4 classes de severidade.

### 4.2 Atribuição de Importância com SHAP
- [ ] **Descrição**: Integrar a biblioteca SHAP (KernelExplainer ou DeepExplainer) para calcular atribuição de features baseada em teoria dos jogos sobre a área predita e severidade.
- [ ] **Critério de Aceitação**: Gráficos de importância de features locais (por paciente) e globais (padrão de contraste, densidade mamária) exportados em `reports/figures/shap_analysis.png`.

### 4.3 Visualização de Mapas de Atenção Multi-Cabeça (Attention Rollout)
- [ ] **Descrição**: Extrair e visualizar a matriz de autoatenção das cabeças nos 4 estágios do MiT para inspecionar o alcance do campo receptivo em estruturas finas.
- [ ] **Critério de Aceitação**: Visualização dos mapas de atenção comparando mamografias com BAC extenso versus mamografias negativas.

### 4.4 Métrica Quantitativa de Fidelidade de Explicabilidade
- [ ] **Descrição**: Medir a fidelidade dos heatmaps do Grad-CAM calculando a porcentagem de energia de ativação concentrada dentro da máscara real do vaso anotada pelo radiologista (Energy-based Pointing Game / Intersection over Heatmap).
- [ ] **Critério de Aceitação**: Métrica quantitativa de fidelidade documentada nos relatórios.

---

## 🔵 Prioridade 4 (P4) — Integração do EMBED e Validação Externa (Quando Liberado)

### 5.1 Implementação do Ingestor do EMBED (`download_embed_with_rois.py`)
- [ ] **Descrição**: Script para download automatizado de mamografias MLO do bucket AWS S3 do EMBED e extração de metadados clínicos.
- [ ] **Ação**: Implementar `src/data/download_embed_with_rois.py` com suporte a autenticação AWS, filtragem de exames 2D e extração de espaçamento de pixel.
- [ ] **Critério de Aceitação**: Ingestão de lote de validação do EMBED em `data/raw/` e pré-processamento em `data/interim/`.

### 5.2 Validação Cruzada Inter-institucional (Generalização)
- [ ] **Descrição**: Testar o modelo treinado com o INbreast em mamografias do EMBED (provenientes de diferentes fabricantes de mamógrafos: Hologic, GE, Lorad).
- [ ] **Critério de Aceitação**: Avaliação de robustez inter-fabricante e análise de queda ou manutenção de desempenho.

### 5.3 Transfer Learning e Refinamento
- [ ] **Descrição**: Fine-tuning do modelo com dados do EMBED caso novas anotações sejam viabilizadas.
- [ ] **Critério de Aceitação**: Modelo aprimorado com métricas comparativas documentadas.

---

## ⚪ Prioridade 5 (P5) — Análise Clínica de Risco Cardiovascular (Longo Prazo)

Depende da disponibilização das tabelas de eventos clínicos de acompanhamento (prontuários / MACE).

### 6.1 Análise de Curvas de Sobrevivência (Kaplan-Meier)
- [ ] **Descrição**: Plotar curvas de sobrevivência livre de eventos cardiovasculares maiores (infarto agudo do miocárdio, AVC e óbito cardiovascular) estratificadas pelos 4 estratos de BAC (Zero, Leve, Moderado, Severo).
- [ ] **Critério de Aceitação**: Gráficos de Kaplan-Meier com cálculo de Log-rank test ($p < 0.05$).

### 6.2 Modelos de Riscos Proporcionais de Cox
- [ ] **Descrição**: Ajustar modelos multivariáveis de Cox controlando para idade, hipertensão, diabetes, dislipidemia e tabagismo para calcular os Hazard Ratios (HR) da presença e área de BAC.
- [ ] **Critério de Aceitação**: Tabela de Hazard Ratios com intervalos de confiança de 95%.

### 6.3 Modelagem de Riscos Competitivos (Fine-Gray)
- [ ] **Descrição**: Ajustar modelo de riscos competitivos considerando mortalidade não-cardiovascular como evento concorrente.
- [ ] **Critério de Aceitação**: Subdistribution Hazard Ratios (sHR) calculados e comparados com o artigo base.

---

## 📋 Checklist Rápido de Execução

```markdown
[ ] 1. Criar script src/data/filter_by_view_final.py (MLO only -> ~140 imagens)
[ ] 2. Gerar zip: inbreast_mlo_images.zip
[ ] 3. Ajustar caminhos hardcoded nos scripts de src/data/
[ ] 4. Iniciar Docker CVAT e configurar tunelamento
[ ] 5. Criar tarefa no CVAT e subir o zip de imagens MLO
[ ] 6. Enviar termos e guia ao radiologista; validar primeiras 5 anotações
[ ] 7. Submeter formulário do HitiLab para acesso ao EMBED
[ ] 8. Adicionar testes unitários com pytest em tests/
[ ] 9. Exportar anotações do CVAT e converter em máscaras PNG
[ ] 10. Executar build_features.py para criar data/processed final
[ ] 11. Treinar MiT + MLP por 150 épocas na GPU
[ ] 12. Avaliar métricas científicas (Dice, IoU, MAE, R², Pearson)
[ ] 13. Desenvolver e aplicar Grad-CAM em src/visualization/gradcam.py
[ ] 14. Aplicar SHAP e extrair mapas de atenção
[ ] 15. Consolidar figuras e relatório comparativo final em reports/
```

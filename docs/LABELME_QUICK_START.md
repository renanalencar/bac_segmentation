# LabelMe - Guia Rápido para Radiologistas

## 1. Instalação (será feita pelo pesquisador)
```powershell
pip install labelme
```

## 2. Iniciar LabelMe
```powershell
labelme data/inbreast/for_annotation --output data/inbreast/annotations --labels BAC,uncertain
```

## 3. Interface

### Atalhos Úteis:
- **Create Polygon**: Clicar pontos ao redor da calcificação, Enter para fechar
- **Edit Polygon**: Editar pontos existentes
- **Delete**: Apagar anotação
- **Save**: Ctrl+S (salva JSON automaticamente)
- **Next Image**: D
- **Previous Image**: A
- **Zoom In**: Scroll up
- **Zoom Out**: Scroll down

## 4. Workflow Sugerido

### Para cada imagem:

1️⃣ **Avaliar se há BAC visível** (10-30 segundos)
   - Se NÃO: Apenas avançar (Next Image)
   - Se SIM: Prosseguir para anotação

2️⃣ **Anotar calcificações arteriais** (2-5 min por caso)
   - Selecionar "Create Polygons"
   - Contornar calcificação clicando pontos
   - Enter para finalizar polígono
   - Escolher label "BAC"

3️⃣ **Casos duvidosos**
   - Se incerto, marcar como "uncertain"
   - Adicionar nota no campo "description"

4️⃣ **Salvar e avançar**
   - Ctrl+S (automático ao trocar de imagem)
   - D para próxima imagem

## 5. Exemplos Visuais de BAC

### ✅ ANOTAR ISTO:
- Calcificação em padrão linear: ||||||||
- Calcificação em "trilhos": ══════
- Trajeto vascular visível
- Bilateral (mesmo padrão em ambas as mamas)

### ❌ NÃO ANOTAR:
- Microcalcs agrupadas: • • • • •
- Calcs pleomórficas
- Calcs dentro de massa
- Calcs cutâneas

## 6. Controle de Qualidade

### Auto-revisão a cada 10 imagens:
- Verificar se anotações estão completas
- Conferir se labels estão corretos
- Garantir que polígonos fecharam corretamente

## 7. Salvamento

Os arquivos JSON são salvos automaticamente em:
`data/inbreast/annotations/[nome_da_imagem].json`

**IMPORTANTE:** Fazer backup regularmente!

## 8. Dúvidas Frequentes

**P: E se a imagem não tiver BAC?**
R: Apenas avançar (não criar anotação vazia)

**P: Devo anotar TODAS as calcificações?**
R: Apenas calcificações ARTERIAIS (vasculares)

**P: Quanto tempo leva?**
R: ~2-5 min por caso COM BAC, 30seg por caso SEM BAC

## Contato
Dúvidas técnicas ou clínicas: [rca2@ecomp.poli.br](mailto:rca2@ecomp.poli.br)

# Guia de Anotação - CVAT (Para Radiologistas)

## 1. Acesso ao Sistema

**URL:** https://cvat.cheekymonkeydixie.us/
**Usuário:** radiologista  
**Senha:** [senha fornecida]

---

## 2. Como Começar

### Passo 1: Login
1. Abrir navegador (Chrome ou Firefox recomendados)
2. Acessar URL fornecida
3. Fazer login com credenciais

### Passo 2: Abrir Tarefa
1. Clicar em **Tasks** no menu superior
2. Selecionar **INbreast Batch 1**
3. Clicar em **Open**

---

## 3. Interface de Anotação

### Ferramentas Principais:
🔧 TOOLBAR (Lado Esquerdo):

| Menu | Descrição |
|--------|-----------|
| 🮰 Cursor | Navegar/Mover |
| ⬟ Polygon | USAR ESTA para BAC |
| ✏️ Edit | Editar pontos |
| 🗑️ Delete | Apagar anotação |
| 💾 Save | Salvar (Ctrl+S) |


⌨️ ATALHOS ÚTEIS:

| Atalho | Descrição |
|--------|-----------|
| N | Próxima imagem |
| P | Imagem anterior |
| Ctrl + S| Salvar |
| F | Fit screen (ajustar zoom) |
| +/- | Zoom in/out |
| Espaço | Mover imagem |
| Ctrl + Z | Desfazer |

---

## 4. Como Anotar BAC

### Workflow por Imagem:

#### 4.1 Avaliar Imagem (10-30 segundos)
- ❓ Há calcificação arterial visível?
- **SIM** → Prosseguir para anotação
- **NÃO** → Apertar `N` (próxima imagem)

#### 4.2 Anotar Calcificação (2-5 minutos)

**Passo a Passo:**

1️⃣   **Selecionar ferramenta Polygon** (ícone 🔲)

2️⃣   **Escolher label:** "BAC" no dropdown

3️⃣   **Clicar pontos ao redor da calcificação:**
   - Clicar ao longo do contorno
   - Aproximadamente 10-20 pontos por calcificação
   - Seguir trajeto vascular

4️⃣   **Fechar polígono:**
   - Último clique = Primeiro ponto
   - Ou apertar `N` para completar

5️⃣   **Ajustar se necessário:**
   - Selecionar ferramenta ✏️ Edit
   - Arrastar pontos para ajustar

6️⃣   **Salvar:** `Ctrl + S`

---

## 5. Critérios de Anotação

### ✅ ANOTAR (BAC):

| Padrão | Descrição | Visual |
|--------|-----------|--------|
| Linear | Calcificação em linha reta | `\|\|\|\|\|\|` |
| Trilhos | Duas linhas paralelas | `═══════` |
| Tubular | Segue vaso sanguíneo | `~~~~~~~` |
| Serpentino | Padrão sinuoso | `∿∿∿∿∿∿` |

**Características:**
- Grosseiras (não puntiformes)
- Bilaterais (ambas as mamas)
- Acompanham trajeto vascular
- Tipicamente periféricas

---

### ❌ NÃO ANOTAR:

| Tipo | Descrição |
|------|-----------|
| Microcalcificações | Pequenos pontos agrupados `• • • •` |
| Pleomórficas | Formas irregulares variadas |
| Em massa | Dentro de nódulos/massas |
| Cutâneas | Na pele (skin) |

---

## 6. Casos Especiais

### Se INCERTO:
1. Usar label **"uncertain"**
2. Anotar mesmo assim
3. Adicionar comentário (clique direito → Add comment)

### Se NÃO TEM BAC:
- **Não criar anotação**
- Apenas apertar `N` para próxima

### Se MÚLTIPLAS calcificações:
- Anotar **CADA calcificação separadamente**
- Não unir todas em um único polígono

---

## 7. Controle de Qualidade

### Auto-revisão a cada 10 imagens:
- ✅ Polígonos fechados corretamente?
- ✅ Label "BAC" selecionado?
- ✅ Não confundi com microcalcs?
- ✅ Salvei? (Ctrl+S)

---

## 8. Progresso e Estatísticas

### Ver progresso:
- Menu superior → **Dashboard**
- Gráfico mostra: imagens anotadas / total

### Estatísticas úteis:
- Tempo médio por imagem
- Total de anotações criadas

---

## 9. Salvar e Finalizar

### Durante trabalho:
- `Ctrl + S` frequentemente
- CVAT salva **automaticamente** ao trocar de imagem

### Ao finalizar sessão:
1. `Ctrl + S` uma última vez
2. Clicar **Menu** → **Finish job**
3. Fazer logout

---

## 10. Problemas Comuns

| Problema | Solução |
|----------|---------|
| "Polígono não fecha" | Clicar no primeiro ponto novamente |
| "Não consigo editar" | Selecionar ferramenta ✏️ Edit |
| "Zoom muito grande" | Apertar `F` (fit screen) |
| "Perdi anotação" | `Ctrl + Z` (desfazer) |
| "Tela travou" | F5 (recarregar página) |

---

## 11. Contato e Suporte

**Dúvidas Técnicas:** [seu WhatsApp/Telegram]  
**Dúvidas Clínicas:** [seu email]  

**Horário de suporte:** Segunda a Sexta, 9h-18h

---

## 12. Estimativa de Tempo

| Cenário | Tempo |
|---------|-------|
| Imagem SEM BAC | ~20-40 segundos |
| Imagem COM BAC (1-2 calcs) | ~3-5 minutos |
| Imagem COM BAC (3+ calcs) | ~8-15 minutos |

**Meta diária sugerida:** 10-15 imagens  
**Total estimado:** 100-150 imagens em 2-3 semanas

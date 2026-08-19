import streamlit as st
import os
from google import genai
from google.genai import types
from pypdf import PdfReader

# 1. Configuração da página do Streamlit (Layout Limpo Original)
st.set_page_config(page_title="Agente Inteligente - Imposto de Renda 2026", page_icon="🤖", layout="centered")
st.title("🤖 Agente Inteligente - Imposto de Renda 2026")

# Texto de Apresentação Oficial
st.write("""
Olá! Seja bem-vindo ao Guia Prático do Imposto de Renda 2026. Estou aqui para simplificar a sua declaração e tirar todas as suas dúvidas sobre as situações mais comuns do dia a dia do contribuinte. Você pode falar comigo para entender o que é, o que considerar e como preencher o programa da Receita Federal.

**Veja os principais temas em que posso te ajudar:**
* 📊 **Faixas de Renda e Alíquotas:** Descubra em qual faixa da tabela progressiva anual você se encaixa, o percentual de imposto do seu perfil e o que muda com a nova regra de isenção.
* 🏢 **Financiamentos:** Saiba como declarar seu imóvel ou veículo financiado sem errar nas fichas de Bens e Direitos.
* 🪙 **Criptomoedas e Trade:** Entenda as regras de isenção mensal, apuração de lucro (GCAP), prejuízos e operações de Day Trade ou Swing Trade.
* 👶 **Dependentes:** Descubra quem você pode incluir, a obrigatoriedade do CPF e os limites de abatimento.
* 🩺 **Deduções (Saúde e Educação):** Saiba quais despesas médicas e escolares reduzem o seu imposto e quais documentos você deve guardar.
* 📈 **Rendimentos e Investimentos:** Como declarar Poupança, Renda Fixa (CDB, Tesouro Direto) e a diferença entre rendimentos isentos e tributáveis.
* ⚖️ **Modelo Ideal:** Entenda se a sua declaração deve ser pelo modelo Completo ou Simplificado para garantir a maior restituição possível.

Se você não sabe por onde começar, pode me fazer perguntas diretas como: *'Quem ganha R$ 40 mil por ano paga quanto de imposto?'* ou *'Como declaro meu apartamento financiado?'*.

Como posso te ajudar a organizar sua declaração hoje?
""")

st.markdown("---")

# 2. Configuração da API Key
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("Erro: A variável de ambiente GEMINI_API_KEY não foi encontrada. Configure-a no seu terminal.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# 3. Base de Conhecimento Oculta (Apenas para processamento interno)
ARQUIVO_PDF = "Guia_Rapido_IRPF_2026.pdf"
CSV_COMPARA = "Tabela_compara_compl_simpl_IRPF2026.csv"
CSV_INVEST = "Tabela_Investimentos_2026.csv"
CSV_GERAL = "Tabela_IRPF_2026.csv"

@st.cache_resource
def extrair_contexto_local(pdf, csv_comp, csv_inv, csv_ger):
    """Lê todas as fontes locais de forma oculta na memória do sistema"""
    texto_contexto = ""
    
    if os.path.exists(pdf):
        try:
            leitor = PdfReader(pdf)
            for pagina in leitor.pages:
                texto_contexto += pagina.extract_text() or ""
        except Exception as e:
            pass

    if os.path.exists(csv_comp):
        try:
            with open(csv_comp, "r", encoding="utf-8") as f:
                texto_contexto += "\n\n=== COMPARAÇÃO MODELO COMPLETO VS SIMPLIFICADO ===\n"
                texto_contexto += f.read()
        except Exception as e:
            pass

    if os.path.exists(csv_inv):
        try:
            with open(csv_inv, "r", encoding="utf-8") as f:
                texto_contexto += "\n\n=== TRIBUTAÇÃO DE INVESTIMENTOS ===\n"
                texto_contexto += f.read()
        except Exception as e:
            pass

    if os.path.exists(csv_ger):
        try:
            with open(csv_ger, "r", encoding="utf-8") as f:
                texto_contexto += "\n\n=== TABELA PROGRESSIVA ANUAL GERAL ===\n"
                texto_contexto += f.read()
        except Exception as e:
            pass
        
    return texto_contexto

contexto_consolidado = extrair_contexto_local(ARQUIVO_PDF, CSV_COMPARA, CSV_INVEST, CSV_GERAL)

# 4. Histórico do Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Interface e Diretrizes de Resposta Limpa (Anti-Falhas de Formatação)
if prompt := st.chat_input("Digite sua dúvida sobre o IRPF 2026 aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Diretriz ultra-rígida proibindo LaTeX, repetições de texto e barras invertidas
        instrucao_sistema = (
            "Você é o Agente Inteligente - Imposto de Renda 2026 do Challenge Alura. "
            "Sua tarefa é responder de forma clara, amigável e puramente textual. "
            "Baseie suas respostas estritamente no contexto de dados fornecido abaixo.\n\n"
            "REGRAS CRUTIAIS DE FORMATAÇÃO DE TEXTO:\n"
            "1. PROIBIDO o uso de qualquer caractere de formato LaTeX ou fórmula matemática (NÃO USE barras invertidas, termos como \\times, \\text, \\mathbf, ou cifrões duplos).\n"
            "2. Apresente contas matemáticas em texto simples de forma corrida. Exemplo correto: '12 x R$ 6.000,00 = R$ 72.000,00'.\n"
            "3. Garanta que NÃO ocorram repetições coladas de texto ou frases duplicadas nas equações.\n"
            "4. Se o assunto não estiver nas tabelas ou no guia, diga apenas que não localizou nos manuais oficiais.\n\n"
            f"=== BASE DE CONHECIMENTO VIGENTE ===\n{contexto_consolidado}"
        )
        
        try:
            resposta = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=instrucao_sistema,
                    temperature=0.1
                )
            )
            
            texto_resposta = resposta.text
            message_placeholder.markdown(texto_resposta)
            st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
            
        except Exception as e:
            st.error(f"Erro ao processar requisição: {e}")

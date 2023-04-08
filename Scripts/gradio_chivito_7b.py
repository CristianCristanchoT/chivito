print('Cargando librerias....')

import torch
from peft import PeftModel
from transformers import LLaMATokenizer, LLaMAForCausalLM, GenerationConfig
import gradio as gr


tokenizer = LLaMATokenizer.from_pretrained(
    "decapoda-research/llama-7b-hf"
)

BASE_MODEL = "decapoda-research/llama-7b-hf"
LORA_WEIGHTS = "CristianC/chivito_lora_alpaca_es_7b"

if torch.cuda.is_available():
    device = "cuda"
    print('GPU detectada!')

else:
    device = "cpu"
    print('GPU no detectada, procediendo a ejecucion en CPU!')



if device == "cuda":
    model = LLaMAForCausalLM.from_pretrained(
        BASE_MODEL,
        load_in_8bit=False,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(
        model, LORA_WEIGHTS, torch_dtype=torch.float16, force_download=True
    )


else:
    model = LLaMAForCausalLM.from_pretrained(
        BASE_MODEL, device_map={"": device}, low_cpu_mem_usage=True
    )
    model = PeftModel.from_pretrained(
        model,
        LORA_WEIGHTS,
        device_map={"": device},
    )


def generate_prompt(data_point):
    # desculpe o desastre de formatação, preciso ser rápido
    if data_point["input"] != '':
        return f"""A continuación hay una instrucción que describe una tarea, junto con una entrada que proporciona más contexto. Escriba una respuesta que complete adecuadamente la solicitud.

### Instrucción:
{data_point["instruction"]}

### Entrada:
{data_point["input"]}

### Respuesta:"""
    else:
        return f"""A continuación hay una instrucción que describe una tarea. Escriba una respuesta que complete adecuadamente la solicitud.

### Instrucción:
{data_point["instruction"]}

### Respuesta:"""

def tokenize(prompt):
    result = tokenizer(
        prompt,
        return_tensors="pt",
    )
    return result

def generate_and_tokenize_prompt(data_point):
    full_prompt = generate_prompt(data_point)
    tokenized_full_prompt = tokenize(full_prompt)
    return tokenized_full_prompt



model.eval()
if torch.__version__ >= "2":
    model = torch.compile(model)


def evaluate(
    instruction,
    input,
    temperature=0.1,
    top_p=0.75,
    top_k=40,
    num_beams=4,
    max_new_tokens=128,
    **kwargs,
):

    dict_input = {
    'instruction': instruction,
    'input': input
    }

    inputs = generate_and_tokenize_prompt(dict_input)
    input_ids = inputs["input_ids"].to(device)
    generation_config = GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        num_beams=num_beams,
        **kwargs,
    )
    with torch.no_grad():
        generation_output = model.generate(
            input_ids=input_ids,
            generation_config=generation_config,
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_new_tokens,
        )
    s = generation_output.sequences[0]
    output = tokenizer.decode(s)
    return output.split("### Respuesta:")[1].strip()



g = gr.Interface(
    fn=evaluate,
    inputs=[
        gr.components.Textbox(
            lines=3, label="Instrucción", placeholder="""Escribe la tarea que quieres que el modelo haga. 
Ejemplo: 
Genera un query SQL que liste los nombres de los departamentos los cuales emplearon mas de 20 empleados."""
        ),
        gr.components.Textbox(lines=4, label="Contexto", placeholder="""Incluye el contexto requerido para completar la tarea (Este campo es opcional).
Ejemplo: 
Existen las siguientes tablas de Postgres SQL, con las siguientes caracteristicas:
Employee(id,name,department_id)
Department(id,name,address)
Salary_Payments(id,employee_id,amount,date)
"""),

        gr.components.Slider(minimum=0, maximum=1, value=0.1, label="Temperature"),
        gr.components.Slider(minimum=0, maximum=1, value=0.75, label="Top p"),
        gr.components.Slider(minimum=0, maximum=100, step=1, value=40, label="Top k"),
        gr.components.Slider(minimum=1, maximum=4, step=1, value=4, label="Beams"),
        gr.components.Slider(
            minimum=1, maximum=512, step=1, value=128, label="Max tokens"
        ),
    ],
    outputs=[
        gr.inputs.Textbox(
            lines=5,
            label="Respuesta",
        )
    ],
    title="🐐 Chivito-LoRA 7B 🐐",
    description="Chivito-LoRA es un modelo LLaMA de 7B parámetros ajustado para seguir instrucciones en español. Está entrenado en el conjunto de datos [Stanford Alpaca](https://github.com/tatsu-lab/stanford_alpaca) pero traducido al español [Alpaca-Spanish](https://huggingface.co/datasets/bertin-project/alpaca-spanish) por bertin-project y utiliza la implementación Huggingface LLaMA.Para obtener más información, visite [el sitio web del proyecto](https://github.com/CristianCristanchoT/chivito).",
)
g.queue(concurrency_count=1)
g.launch()

from llama_cpp import Llama

print("LLMChatSession loaded !")

class LLMChatSession:
    def __init__(self, model_path, n_ctx=2048, n_threads=16, n_batch=1024, temperature=0.1, n_gpu_layers=-1):
        self.model_path = str(model_path)
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_batch = n_batch
        self.temperature = temperature
        self.n_gpu_layers = n_gpu_layers

        # Charger le modèle directement à l'initialisation
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_batch=self.n_batch,
            use_mlock=True,
            temperature=self.temperature,
            verbose=False,
            n_gpu_layers=self.n_gpu_layers
        )

    def generate(self, prompt, stop_tag=None, max_tokens=512):
        stop = [stop_tag] if stop_tag else []
        response = self.llm(prompt, stop=stop, max_tokens=max_tokens)
        return response["choices"][0]["text"].strip()

    def __del__(self):
        # Optionnel: libère la mémoire à la destruction
        del self.llm

class ErroRegra(Exception):
    def __init__(self, status_code: int, mensagem: str):
        self.status_code = status_code
        self.mensagem = mensagem
        super().__init__(mensagem)

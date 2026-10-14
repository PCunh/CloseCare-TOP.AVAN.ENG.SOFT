
const API = 'http://localhost:8000';
const $ = id => document.getElementById(id);

let usuario = null;
let agendaAtual = [];
let horariosAtuais = [];

const textoData = valor => new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Sao_Paulo'
}).format(new Date(valor));

const seguro = valor => String(valor ?? '').replace(
    /[&<>"']/g,
    c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[c])
);

function aviso(msg, tipo = '') {
    $('mensagem').textContent = msg;
    $('mensagem').className = 'aviso-esbc ' + tipo;
}

async function req(url, method = 'GET', data = undefined) {
    const resposta = await fetch(API + url, {
        method,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: data === undefined ? undefined : JSON.stringify(data)
    });

    if (resposta.status === 204) return null;

    const json = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
        throw new Error(
            'HTTP ' + resposta.status +
            ' em ' + method + ' ' + url + ': ' +
            (
                typeof json.detail === 'string'
                    ? json.detail
                    : JSON.stringify(json.detail ?? 'Erro na requisição')
            )
        );
    }

    return json;
}

async function executar(fn) {
    try {
        await fn();
    } catch (e) {
        aviso(e.message, 'error');
    }
}

function formatLocal(data) {
    const d = new Date(data);

    return new Date(
        d.getTime() - d.getTimezoneOffset() * 60000
    ).toISOString().slice(0, 16);
}

function iso(valor) {
    return new Date(valor).toISOString();
}

function diaSeguinte(valor) {
    const [data, hora] = valor.split('T');
    const [ano, mes, dia] = data.split('-').map(Number);

    const d = new Date(Date.UTC(ano, mes - 1, dia + 1));

    return d.toISOString().slice(0, 10) + 'T' + hora;
}

function adicionarMinutosLocal(valor, minutos) {
    const data = new Date(valor);
    data.setMinutes(data.getMinutes() + minutos);
    return formatLocal(data);
}

function sincronizarFimComInicio() {
    const inicio = $('inicio').value;
    const fim = $('fim').value;

    if (!inicio) return;

    const dataInicio = inicio.slice(0, 10);
    const horaFim = fim ? fim.slice(11, 16) : '';

    let novoFim = horaFim
        ? dataInicio + 'T' + horaFim
        : adicionarMinutosLocal(inicio, 60);

    if (new Date(novoFim) <= new Date(inicio)) {
        novoFim = adicionarMinutosLocal(inicio, 60);
    }

    $('fim').value = novoFim;
}

function linha(titulo, subtitulo, botoes = []) {
    const item = document.createElement('div');
    item.className = 'item';

    const texto = document.createElement('div');

    texto.innerHTML =
        '<strong>' + seguro(titulo) + '</strong>' +
        '<small>' + seguro(subtitulo) + '</small>';

    item.append(texto);

    const actions = document.createElement('div');
    actions.className = 'actions';

    for (const [rotulo, funcao, tipo] of botoes) {
        const b = document.createElement('button');

        b.textContent = rotulo;
        b.className = 'small ' + (tipo || '');
        b.onclick = () => executar(funcao);

        actions.append(b);
    }

    item.append(actions);

    return item;
}

function vazio(id, mensagem) {
    $(id).replaceChildren();

    const v = document.createElement('div');
    v.className = 'vazio';
    v.textContent = mensagem;

    $(id).append(v);
}

async function sessao() {
    try {
        usuario = await req('/auth/me');
    } catch {
        usuario = null;
    }

    $('session').textContent = usuario
        ? usuario.nome + ' · ' + usuario.tipo_usuario
        : 'Não conectado';

    $('profissional').classList.toggle(
        'hidden',
        usuario?.tipo_usuario !== 'profissional'
    );

    $('paciente').classList.toggle(
        'hidden',
        usuario?.tipo_usuario !== 'paciente'
    );

    if (usuario?.tipo_usuario === 'profissional') {
        await listarMeusHorarios();
    }

    if (usuario?.tipo_usuario === 'paciente') {
        await listarProfissionais();
        await listarAgendamentos();
    }
}

async function listarProfissionais() {
    const pro = await req('/esbc/disponibilidade/profissionais');

    const selecao = $('profissionais');
    const atual = selecao.value;

    selecao.replaceChildren();

    for (const p of pro) {
        const option = document.createElement('option');

        option.value = p.id;
        option.textContent = p.nome + ' — ' + p.especialidade;

        selecao.append(option);
    }

    if (pro.some(p => String(p.id) === atual)) {
        selecao.value = atual;
    }

    await listarLivres();
}

async function listarMeusHorarios() {
    const horarios = await req('/esbc/disponibilidade/meus');

    horariosAtuais = horarios;

    const container = $('meusHorarios');
    container.replaceChildren();

    if (!horarios.length) {
        return vazio('meusHorarios', 'Nenhum horário cadastrado.');
    }

    for (const h of horarios) {
        const ocupado = h.status !== 'livre';

        const actions = ocupado ? [] : [
            [
                'Editar',
                async () => {
                    const novoInicio = prompt(
                        'Novo início (AAAA-MM-DDTHH:MM)',
                        formatLocal(h.inicio)
                    );

                    if (!novoInicio) return;

                    const novoFim = prompt(
                        'Novo fim (AAAA-MM-DDTHH:MM)',
                        formatLocal(h.fim)
                    );

                    if (!novoFim) return;

                    if (new Date(novoFim) <= new Date(novoInicio)) {
                        throw new Error(
                            'O término deve ser posterior ao início.'
                        );
                    }

                    await req(
                        '/esbc/disponibilidade/' + h.id,
                        'PUT',
                        {
                            inicio: iso(novoInicio),
                            fim: iso(novoFim)
                        }
                    );

                    aviso('Horário atualizado.', 'ok');
                    await listarMeusHorarios();
                }
            ],
            [
                'Excluir',
                async () => {
                    if (!confirm('Excluir este horário?')) return;

                    await req(
                        '/esbc/disponibilidade/' + h.id,
                        'DELETE'
                    );

                    aviso('Horário removido.', 'ok');
                    await listarMeusHorarios();
                },
                'danger'
            ]
        ];

        container.append(
            linha(
                textoData(h.inicio) + ' — ' + textoData(h.fim),
                'Horário #' + h.id + ' · ' + h.status,
                actions
            )
        );
    }
}

async function listarLivres() {
    const id = $('profissionais').value;

    console.log('Profissional selecionado:', id);

    if (!id) {
        return vazio(
            'horariosLivres',
            'Selecione um profissional.'
        );
    }

    const horarios = await req('/esbc/disponibilidade/' + id);

    console.log('Horários retornados:', horarios);

    const container = $('horariosLivres');
    container.replaceChildren();

    if (!horarios.length) {
        return vazio(
            'horariosLivres',
            'Nenhum horário livre para este profissional.'
        );
    }

    for (const h of horarios) {
        container.append(
            linha(
                textoData(h.inicio) + ' — ' + textoData(h.fim),
                'Horário #' + h.id,
                [
                    [
                        'Agendar',
                        async () => {
                            await req('/esbc/agendamentos', 'POST', {
                                horario_id: h.id
                            });

                            aviso('Agendamento confirmado.', 'ok');

                            await listarLivres();
                            await listarAgendamentos();
                        }
                    ]
                ]
            )
        );
    }
}

async function listarAgendamentos() {
    agendaAtual = await req('/esbc/agendamentos/meus');

    const container = $('meusAgendamentos');
    container.replaceChildren();

    if (!agendaAtual.length) {
        return vazio(
            'meusAgendamentos',
            'Você ainda não possui agendamentos.'
        );
    }

    for (const a of agendaAtual) {
        const acoes = a.status === 'agendado'
            ? [
                [
                    'Cancelar',
                    async () => {
                        if (!confirm(
                            'Cancelar agendamento #' + a.id + '?'
                        )) {
                            return;
                        }

                        const resultado = await req(
                            '/esbc/agendamentos/' + a.id + '/cancelar',
                            'PATCH'
                        );

                        if (resultado?.status !== 'cancelado') {
                            throw new Error(
                                'O backend não confirmou o cancelamento.'
                            );
                        }

                        await listarAgendamentos();

                        try {
                            await listarLivres();
                        } catch (erro) {
                            console.warn(
                                'Falha ao atualizar horários livres',
                                erro
                            );
                        }

                        aviso(
                            'Agendamento #' + a.id +
                            ' cancelado com sucesso.',
                            'ok'
                        );
                    },
                    'danger'
                ],
                [
                    'Remarcar',
                    async () => {
                        const profissional = $('profissionais').value;

                        const livres = await req(
                            '/esbc/disponibilidade/' + profissional
                        );

                        if (!livres.length) {
                            throw new Error(
                                'Sem horários livres para remarcação.'
                            );
                        }

                        const resposta = prompt(
                            'Digite o ID do novo horário:\n' +
                            livres.map(
                                h => '#' + h.id +
                                ' — ' + textoData(h.inicio)
                            ).join('\n')
                        );

                        if (!resposta) return;

                        await req(
                            '/esbc/agendamentos/' + a.id + '/remarcar',
                            'PATCH',
                            {
                                novo_horario_id: Number(resposta)
                            }
                        );

                        await listarAgendamentos();
                        await listarLivres();

                        aviso('Consulta remarcada.', 'ok');
                    }
                ]
            ]
            : [];

        container.append(
            linha(
                'Agendamento #' + a.id + ' · ' + a.status,
                'Horário #' + a.horario_id,
                acoes
            )
        );
    }
}

$('cadTipo').onchange = () => {
    $('especialidadeBox').classList.toggle(
        'hidden',
        $('cadTipo').value !== 'profissional'
    );
};

$('cadastroForm').onsubmit = e => {
    e.preventDefault();

    executar(async () => {
        const dados = {
            nome: $('cadNome').value,
            email: $('cadEmail').value,
            senha: $('cadSenha').value,
            tipo_usuario: $('cadTipo').value
        };

        if (dados.tipo_usuario === 'profissional') {
            dados.especialidade = $('cadEspecialidade').value;
        }

        await req('/usuarios', 'POST', dados);

        $('loginEmail').value = dados.email;
        $('loginSenha').value = dados.senha;

        aviso('Cadastro realizado. Clique em Entrar.', 'ok');
    });
};

$('loginForm').onsubmit = e => {
    e.preventDefault();

    executar(async () => {
        await req('/auth/login', 'POST', {
            email: $('loginEmail').value,
            senha: $('loginSenha').value
        });

        await sessao();

        aviso('Login realizado com sucesso.', 'ok');
    });
};

$('logout').onclick = () => executar(async () => {
    await req('/auth/logout', 'POST');
    await sessao();
    aviso('Sessão encerrada.');
});

$('horarioForm').onsubmit = e => {
    e.preventDefault();

    executar(async () => {
        const data = $('dataAtendimento').value;
        const horaInicio = $('horaInicio').value;
        const horaFim = $('horaFim').value;

        if (!data || !horaInicio || !horaFim) {
            throw new Error('Preencha a data e os horários.');
        }

        if (horaFim <= horaInicio) {
            throw new Error('O término deve ser posterior ao início.');
        }

        const inicio = `${data}T${horaInicio}`;
        const fim = `${data}T${horaFim}`;

        await req('/esbc/disponibilidade', 'POST', {
            inicio: iso(inicio),
            fim: iso(fim)
        });

        await listarMeusHorarios();

        $('dataAtendimento').value = diaSeguinte(inicio).slice(0, 10);

        aviso('Horário cadastrado com sucesso.', 'ok');
    });
};
$('refreshProf')?.addEventListener('click', () => executar(listarMeusHorarios));
$('refreshLivres')?.addEventListener('click', () => executar(listarLivres));
$('refreshAg')?.addEventListener('click', () => executar(listarAgendamentos));
$('profissionais')?.addEventListener('change', () => executar(listarLivres));

const amanha = new Date();
amanha.setDate(amanha.getDate() + 1);

$('dataAtendimento').value = formatLocal(amanha).slice(0, 10);
$('horaInicio').value = '09:00';
$('horaFim').value = '10:00';

executar(sessao);

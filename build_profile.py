from base64 import b32hexencode
from pathlib import Path
from shutil import which
from subprocess import run
from uuid import UUID, uuid4
from zipfile import ZipFile, ZIP_DEFLATED
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'Herdr-XL-Agentes.streamDeckProfile'
ASSETS = ROOT / '.build'
MAGICK = 'magick'
FONT = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
NS = 'com.elgato.streamdeck.'
COLORS = {
    'agent': ('#10263B', '#61CFFF'), 'attention': ('#392316', '#FFC06C'),
    'done': ('#142D26', '#80E8AE'), 'layout': ('#252040', '#BDA6FF'),
    'git': ('#123335', '#78E8D9'), 'prompt': ('#35233C', '#F0B5F0'),
    'system': ('#252B36', '#C2CEDF'),
}
KEYCODES = dict(zip('asdfhgzxcvbqwerty12346nkjl', (0,1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,20,21,22,45,40,38,37)))
KEYCODES.update({',':43,'.':47,'f8':100,'f2':120,'i':34,'t':17,'y':16,'o':31,'p':35,'-':27,'left':123,'right':124,'up':126,'down':125,'esc':53,'tab':48,'return':36})
QT = {'f8':16777271,'f2':16777265,'left':16777234,'right':16777236,'up':16777235,'down':16777237,'esc':16777216,'tab':16777217,'return':16777220}
INDEX = {
    'iTerm': ('system', '>', 'iTerm', 'open'),
    'Agentes': ('agent', 'A', 'Agentes', ('prefix','g')),
    'Bloqueados': ('attention', '!', 'Bloqueados', ('prefix','g','b')),
    'Terminados': ('done', '✓', 'Terminados', ('prefix','g','d')),
    'Trabajando': ('agent', '···', 'Trabajando', ('prefix','g','w')),
    'En espera': ('agent', '○', 'En espera', ('prefix','g','i')),
    'Aviso': ('attention', '↗', 'Último aviso', ('prefix','o')),
    'Proyectos': ('git', '▤', 'Proyectos', ('prefix','w')),
    'Codex': ('agent', 'C', 'Codex', ('prefix','c',('@text','codex'))),
    'Claude': ('agent', 'Cl', 'Claude', ('prefix','c',('@text','claude'))),
    'Nueva pestaña': ('layout', '+', 'Nueva\npestaña', ('prefix','c')),
    'Nuevo proyecto': ('git', '+', 'Nuevo\nproyecto', ('prefix','shift+n')),
    'Worktree': ('git', 'Y', 'Worktree', (
        'prefix', 'c', ('@text','Worktree',250), ('@key','return',160),
        ('@text','herdr worktree create --branch ',650),
    )),
    'Dividir abajo': ('layout', '⊞', 'Dividir\nabajo', ('prefix','-')),
    'Panel amplio': ('layout', '□', 'Ampliar\npanel', ('prefix','z')),
    'Barra lateral': ('layout', '▣', 'Barra\nlateral', ('prefix','b')),
    'Renombrar pestaña': ('layout', 'Aa', 'Renombrar\npestaña', ('prefix','shift+t')),
    'Panel izq': ('layout', '←', 'Panel izq.', ('alt+h',)),
    'Panel arriba': ('layout', '↑', 'Panel arriba', ('alt+k',)),
    'Panel abajo': ('layout', '↓', 'Panel abajo', ('alt+j',)),
    'Panel dcha': ('layout', '→', 'Panel dcha.', ('alt+l',)),
    'Pestaña anterior': ('layout', '‹', 'Pestaña ant.', ('alt+left',)),
    'Pestaña siguiente': ('layout', '›', 'Pestaña sig.', ('alt+right',)),
    'Paelladoc Deliver': ('done', 'PD', 'Paelladoc\nDeliver', ('f8',)),
    'Plan': ('prompt', '1', 'Plan', 'Antes de editar, inspecciona el código y las convenciones del repo. Propón un plan breve con los archivos afectados, los supuestos y cómo comprobarás el resultado. Espera mi visto bueno.'),
    'Revisar diff': ('prompt', '2', 'Revisar diff', 'Revisa el diff, incluidos cambios preparados y sin preparar. Prioriza bugs, regresiones y casos sin cubrir. Cita archivo y línea. Deja el código intacto.'),
    'Tests': ('prompt', '3', 'Tests', 'Identifica y ejecuta las pruebas más relevantes para el cambio actual. Distingue los fallos reproducidos de los que parecen ajenos al cambio. Resume los comandos y resultados.'),
    'Diagnóstico': ('prompt', '4', 'Diagnóstico', 'Reproduce el fallo descrito, identifica su causa con evidencia y plantea la corrección más pequeña. Espera mi visto bueno antes de editar.'),
    'Retomar': ('prompt', '5', 'Retomar', 'Antes de continuar, resume el objetivo, qué has cambiado, qué has verificado y qué queda pendiente. Señala la siguiente decisión que requiera mi intervención.'),
    'Borrador PR': ('prompt', '6', 'Borrador PR', 'Redacta un título y cuerpo para una PR a partir del diff actual. Incluye cambios, motivación, pruebas ejecutadas y riesgos concretos. Déjalo como borrador en este chat.'),
    'Menú Codex': ('agent', 'C', 'Menú Codex', ('folder','codex')),
    'Menú Claude': ('prompt', 'Cl', 'Menú Claude', ('folder','claude')),
}

LOWER = ('agent', '−', 'Esfuerzo −', ('alt+,',))
RAISE = ('agent', '+', 'Esfuerzo +', ('alt+.',))
BACK = ('system', '‹', 'Volver', ('back',))
ESC = ('system', '×', 'Esc', ('esc',))
HERDR_DOCS = ('system', '?', 'Docs Herdr', ('website','https://herdr.dev/tui/docs/'))

def slash(category, symbol, label, command):
    return (category, symbol, label, command)

CODEX = [
    BACK, LOWER, RAISE,
    slash('agent','M','Modelo','/model'),
    slash('agent','»','Fast','/fast'),
    slash('agent','i','Estado','/status'),
    slash('agent','Pr','Presets','/presets'),
    slash('agent','/','Comandos','/'),
    slash('git','Δ','Diff','/diff'),
    slash('git','✓','Revisión','/review'),
    slash('prompt','P','Plan','/plan'),
    slash('prompt','◎','Objetivo','/goal'),
    slash('agent','S','Subagentes','/subagents'),
    slash('agent','A','Agentes','/agents'),
    slash('system','PS','Procesos','/ps'),
    slash('agent','↗','Consulta lateral','/side'),
    slash('layout','N','Chat nuevo','/new'),
    slash('layout','↩','Retomar','/resume'),
    slash('layout','Y','Bifurcar','/fork'),
    slash('layout','Aa','Renombrar','/rename'),
    slash('layout','↓','Compactar','/compact'),
    slash('system','C','Copiar salida','/copy'),
    slash('system','M','MCP','/mcp'),
    slash('system','K','Atajos Codex','/keymap'),
    slash('system','S','Skills','/skills'),
    slash('system','P','Plugins','/plugins'),
    slash('system','A','Apps','/apps'),
    slash('system','@','Citar archivo','/mention'),
    slash('system','≡','Permisos','/permissions'),
    slash('system','⚙','Config Codex','/config'),
    ESC, ('system','?','Docs Codex',('website','https://developers.openai.com/codex/cli/slash-commands')),
]

CLAUDE = [
    BACK,
    slash('prompt','−','Esfuerzo bajo','/effort low'),
    slash('prompt','+','Esfuerzo alto','/effort high'),
    slash('prompt','M','Modelo','/model'),
    slash('prompt','»','Fast','/fast'),
    slash('prompt','i','Estado','/status'),
    slash('prompt','E','Elegir esfuerzo','/effort'),
    slash('prompt','/','Comandos','/'),
    slash('git','Δ','Diff','/diff'),
    slash('git','✓','Revisión','/code-review'),
    slash('prompt','P','Plan','/plan'),
    slash('prompt','O','Opus','/model opus'),
    slash('prompt','S','Sonnet','/model sonnet'),
    slash('prompt','H','Haiku','/model haiku'),
    slash('prompt','%','Uso y cuota','/usage'),
    slash('prompt','↗','Consulta lateral','/btw '),
    slash('layout','N','Chat nuevo','/clear'),
    slash('layout','↩','Retomar','/resume'),
    slash('layout','↶','Rebobinar','/rewind'),
    slash('layout','Aa','Renombrar','/rename '),
    slash('layout','↓','Compactar','/compact'),
    slash('layout','C','Contexto','/context'),
    slash('system','M','MCP','/mcp'),
    slash('system','T','Tareas','/tasks'),
    slash('system','A','Agentes','/agents'),
    slash('system','P','Plugins','/plugin'),
    slash('system','≡','Permisos','/permissions'),
    slash('prompt','=','Esfuerzo medio','/effort medium'),
    slash('system','⚙','Config Claude','/config'),
    slash('system','?','Ayuda Claude','/help'),
    ESC, ('system','?','Docs Claude',('website','https://code.claude.com/docs/en/commands')),
]

def menu(label, folder, symbol, category='agent'):
    return (category,symbol,label,('folder',folder))

def launch(executable, label, category='agent'):
    return (category, '>', label, ('prefix','c',('@text',executable)))

def docs(label, url):
    return ('system','?',label,('website',url))

def command_menu(executable, url, commands, shortcuts=(), label=None):
    result = [BACK, launch(executable,label or f'Abrir {executable}')]
    result.extend(('agent',symbol,title,(chord,)) for symbol,title,chord in shortcuts)
    result.extend(slash('system',symbol,title,command) for symbol,title,command in commands)
    result.append(docs('Docs',url))
    return result

PI = [
    BACK, ('agent','↻','Ciclo esfuerzo',('shift+tab',)),
    slash('agent','−','Esfuerzo bajo','/thinking low'),
    slash('agent','+','Esfuerzo alto','/thinking high'),
    slash('agent','M','Modelo','/model'),
    slash('agent','E','Elegir esfuerzo','/thinking'),
    slash('agent','i','Estado','/session'),
    launch('pi','Abrir Pi'),
    slash('agent','0','Sin esfuerzo','/thinking off'),
    slash('agent','=','Esfuerzo medio','/thinking medium'),
    slash('agent','++','Esfuerzo extra','/thinking xhigh'),
    slash('system','K','Atajos Pi','/hotkeys'),
    slash('agent','S','Mis modelos','/scoped-models'),
    ('system','T','Ver thinking',('ctrl+t',)),
    ('system','O','Ver herramientas',('ctrl+o',)),
    slash('system','/','Comandos','/'),
    slash('layout','N','Chat nuevo','/new'),
    slash('layout','R','Retomar','/resume'),
    slash('layout','Y','Árbol sesión','/tree'),
    slash('layout','Y','Bifurcar','/fork'),
    slash('layout','D','Duplicar','/clone'),
    slash('layout','Aa','Nombrar','/name '),
    slash('layout','↓','Compactar','/compact'),
    slash('system','C','Copiar salida','/copy'),
    slash('system','M','MCP','/mcp'),
    slash('system','R','Recargar','/reload'),
    slash('system','S','Ajustes Pi','/settings'),
    slash('system','+','Novedades','/changelog'),
    ESC, docs('Docs Pi','https://docs.pi.dev/latest/slash-commands'),
]
HERMES = [
    BACK,
    slash('agent','−','Esfuerzo bajo','/reasoning low'),
    slash('agent','+','Esfuerzo alto','/reasoning high'),
    slash('agent','M','Modelo','/model'),
    slash('agent','E','Nivel actual','/reasoning'),
    slash('agent','i','Estado','/status'),
    slash('agent','%','Uso y cuota','/usage'),
    launch('hermes','Abrir Hermes'),
    slash('agent','0','Sin esfuerzo','/reasoning none'),
    slash('agent','=','Esfuerzo medio','/reasoning medium'),
    slash('agent','++','Esfuerzo extra','/reasoning xhigh'),
    slash('agent','»','Fast','/fast'),
    slash('system','T','Ver thinking','/reasoning show'),
    slash('system','T','Ocultar thinking','/reasoning hide'),
    slash('layout','C','Contexto','/context'),
    slash('layout','↓','Comprimir','/compress'),
    slash('layout','N','Chat nuevo','/new'),
    slash('layout','S','Sesiones','/sessions'),
    slash('layout','R','Retomar','/resume'),
    slash('layout','Aa','Nombrar','/title '),
    slash('git','Δ','Diff','/diff'),
    slash('prompt','P','Plan','/plan '),
    slash('prompt','↗','Consulta lateral','/btw '),
    slash('system','C','Copiar salida','/copy'),
    slash('system','T','Herramientas','/tools'),
    slash('system','S','Skills','/skills'),
    slash('system','M','MCP','/mcp'),
    slash('system','i','Config Hermes','/config'),
    slash('system','/','Comandos','/'),
    slash('system','?','Ayuda Hermes','/help'),
    ESC,
    docs('Docs Hermes','https://hermes-agent.nousresearch.com/docs/reference/slash-commands'),
]
MORE = [
    BACK, HERDR_DOCS, None, None, None, None, None, None,
    menu('OpenCode','opencode','Oc'), menu('Gemini','gemini','Gm'),
    menu('Cursor','cursor','Cu'), menu('Copilot','copilot','Cp'),
    menu('Grok','grok','Gk'), menu('Kimi','kimi','Ki'),
    menu('Qwen','qwen','Qw'), menu('Crush','crush','Cr'),
]
EXTRA = {
    'opencode': ('OpenCode', command_menu('opencode','https://opencode.ai/docs/cli/tui/', [
        ('M','Modelos','/models'), ('A','Agentes','/agents'), ('S','Sesiones','/sessions'),
        ('N','Chat nuevo','/new'), ('C','Compactar','/compact'), ('M','MCP','/mcp'),
        ('E','Editor','/editor'), ('↶','Deshacer','/undo'), ('↷','Rehacer','/redo'),
    ], [('V','Variante','ctrl+t'),('M','Modelo previo','f2'),('P','Paleta','ctrl+p')])),
    'gemini': ('Gemini', command_menu('gemini','https://google-gemini.github.io/gemini-cli/docs/cli/commands.html', [
        ('%','Estadísticas','/stats'), ('T','Herramientas','/tools'),
        ('C','Comprimir','/compress'), ('M','Ver memoria','/memory show'),
        ('S','Chats guardados','/chat list'), ('M','MCP','/mcp'),
        ('⚙','Ajustes','/settings'), ('?','Ayuda','/help'),
    ]) + [launch('gemini --model ', 'Elegir modelo')]),
    'cursor': ('Cursor', command_menu('cursor-agent','https://cursor.com/docs/cli/reference/slash-commands', [
        ('M','Modelo','/model'), ('P','Plan','/plan'), ('A','Pregunta','/ask'),
        ('i','Acerca de','/about'), ('N','Chat nuevo','/new-chat'), ('?','Ayuda','/help'),
    ], label='Abrir Cursor')),
    'copilot': ('Copilot', command_menu('copilot','https://docs.github.com/en/copilot/reference/cli-command-reference', [
        ('M','Modelo','/model'), ('%','Uso y cuota','/usage'), ('C','Contexto','/context'),
        ('↓','Compactar','/compact'), ('P','Plan','/plan'), ('✓','Revisión','/review'),
        ('≡','Permisos','/permissions'), ('?','Ayuda','/help'),
    ])),
    'grok': ('Grok', command_menu('grok','https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/04-slash-commands.md', [
        ('i','Estado','/status'), ('A','Sesiones','/sessions'),
        ('↓','Compactar','/compact'), ('?','Ayuda','/help'),
    ]) + [launch('grok --model ', 'Elegir modelo')]),
    'kimi': ('Kimi', command_menu('kimi','https://moonshotai.github.io/kimi-code/en/guides/interaction.html', [
        ('M','Modelo','/model'), ('↓','Compactar','/compact'), ('?','Ayuda','/help'),
    ])),
    'qwen': ('Qwen', command_menu('qwen','https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/', [
        ('M','Modelo','/model'), ('i','Estadísticas','/stats'), ('↓','Comprimir','/compress'),
        ('M','MCP','/mcp'), ('?','Ayuda','/help'),
    ])),
    'crush': ('Crush', command_menu('crush','https://github.com/charmbracelet/crush', [],
        [('P','Paleta','ctrl+p')])),
    'prompts': ('Prompts', [BACK, *list(INDEX.values())[24:30], ESC, HERDR_DOCS]),
}

def keys(*names):
    return [INDEX[name] for name in names]

def controls_first(board, labels, executable=None):
    by_label = {key[2]: key for key in board}
    top = [by_label[label] for label in labels]
    room = [] if executable is None else [launch(executable, f'Abrir {executable.title()}')]
    omit = set(labels)
    if executable is not None:
        omit.add('Comandos')
    return top + room + [key for key in board if key[2] not in omit]

CODEX = controls_first(CODEX, [
    'Volver', 'Esfuerzo −', 'Esfuerzo +', 'Modelo', 'Fast', 'Estado', 'Presets',
], 'codex')
CLAUDE = controls_first(CLAUDE, [
    'Volver', 'Esfuerzo bajo', 'Esfuerzo alto', 'Modelo', 'Elegir esfuerzo', 'Estado', 'Uso y cuota',
], 'claude')
PI = controls_first(PI, [
    'Volver', 'Esfuerzo bajo', 'Esfuerzo alto', 'Modelo', 'Ciclo esfuerzo', 'Estado', 'Elegir esfuerzo', 'Abrir Pi',
])
HERMES = controls_first(HERMES, [
    'Volver', 'Esfuerzo bajo', 'Esfuerzo alto', 'Modelo', 'Nivel actual', 'Estado', 'Uso y cuota', 'Abrir Hermes',
])

MAIN = [
    *keys('iTerm','Agentes','Bloqueados','Terminados','Trabajando','En espera','Aviso','Paelladoc Deliver'),
    *keys('Proyectos','Nuevo proyecto','Worktree','Nueva pestaña','Dividir abajo','Panel amplio','Barra lateral','Renombrar pestaña'),
    *keys('Panel izq','Panel arriba','Panel abajo','Panel dcha','Pestaña anterior','Pestaña siguiente'),
    LOWER[:2] + ('Codex −', LOWER[3]),
    RAISE[:2] + ('Codex +', RAISE[3]),
    menu('Codex','codex','Co','git'),
    menu('Claude Code','claude','Cl','git'),
    menu('Pi','pi','Pi','git'),
    menu('Hermes','hermes','He','git'),
    menu('Más agentes','more','+','git'),
    menu('Prompts','prompts','P','git'),
    *keys('Revisar diff','Tests'),
]

def uid():
    return str(uuid4()).upper()

def action(name, kind, settings, state=None, plugin_name=None):
    uuid = NS + kind
    data = {'ActionID': uid().lower(), 'LinkedTitle': True, 'Name': name}
    if plugin_name:
        data['Plugin'] = {'Name': plugin_name, 'UUID': uuid, 'Version': '1.0'}
    data.update(Resources=None, Settings=settings, State=0, States=[state or {}], UUID=uuid)
    return data

def hotkey(chord):
    *mods, key = chord.split('+')
    data = {'KeyCmd': 'cmd' in mods, 'KeyCtrl': 'ctrl' in mods,
            'KeyModifiers': sum(v for k,v in [('shift',1),('ctrl',2),('alt',4),('cmd',8)] if k in mods),
            'KeyOption': 'alt' in mods, 'KeyShift': 'shift' in mods,
            'NativeCode': KEYCODES[key], 'QTKeyCode': QT[key] if key in QT else ord(key.upper()), 'VKeyCode': KEYCODES[key]}
    blank = {k: (False if isinstance(v, bool) else 0 if k == 'KeyModifiers' else 33554431 if k == 'QTKeyCode' else -1) for k,v in data.items()}
    return action('Hotkey', 'system.hotkey', {'Coalesce': True, 'Hotkeys': [data, blank, blank, blank]},
                  plugin_name='Activate a Key Command')

def text_key(contents):
    return action('Text', 'system.text', {'isSendingEnter': False, 'pastedText': contents})

def delay(ms):
    return action('Delay', 'multiactions.delay', {'delay': ms})

def sequence(steps):
    routine = []
    for step in steps:
        is_custom = isinstance(step, tuple)
        kind, value = step[:2] if is_custom else ('@key', step)
        pause = step[2] if is_custom and len(step) == 3 else (450 if kind == '@text' else 80)
        if routine:
            routine.append(delay(pause))
        if kind == '@text':
            routine.append(text_key(value))
        else:
            routine.append(hotkey('ctrl+a' if value == 'prefix' else value))
    multi = action('Multi Action', 'multiactions.routine', {})
    multi['Actions'] = [{'Actions': routine}, {'Actions': []}]
    multi['Plugin'] = {'Name':'Multi Action','UUID':NS+'multiactions','Version':'1.0'}
    return multi

def icon(i, kind, symbol, label):
    bg, accent = COLORS[kind]
    path = ASSETS / f'key-{i:02}.png'
    lines = label.splitlines()
    argv = [MAGICK, '-size','144x144',f'xc:{bg}', '-fill',accent, '-draw','roundrectangle 13,12 37,16 2,2',
            '-font',FONT, '-gravity','north', '-pointsize','48','-annotate','+0+23',symbol,
            '-fill','#F9FBFF','-pointsize', '19' if len(label) > 12 else '21']
    for offset, line in enumerate(lines):
        argv += ['-annotate',f'+0+{87+23*offset if len(lines)==2 else 99}',line]
    run([*argv, f'PNG24:{path}'], check=True)
    return path

def legacy_folder(identifier):
    value = b32hexencode(UUID(identifier).bytes).decode().rstrip('=')
    return value.translate(str.maketrans('UV','VW')) + 'Z'

def build():
    if not which(MAGICK):
        raise SystemExit('ImageMagick is required. On macOS: brew install imagemagick')
    if not Path(FONT).is_file():
        raise SystemExit(f'Font not found: {FONT}')
    ASSETS.mkdir(exist_ok=True)
    OUT.parent.mkdir(exist_ok=True)
    outer, base, page = (uid() for _ in range(3))
    root = f'{outer}.sdProfile/'
    folders = {
        'codex':('Menú Codex',CODEX), 'claude':('Menú Claude',CLAUDE),
        'pi':('Menú Pi',PI), 'hermes':('Menú Hermes',HERMES),
        'more':('Más agentes',MORE), **EXTRA,
    }
    folder_ids = {name:uid() for name in folders}
    top = {
        'Device':{'Model':'20GAT9902','UUID':''}, 'Name':'Herdr XL · Agentes v5',
        'Pages':{'Current':page.lower(),'Default':base.lower(),'Pages':[page.lower()]},
        'Version':'2.0',
    }
    def button(job):
        if job == 'open':
            return action('Open','system.open',{'path':'"/Applications/iTerm.app"'})
        if isinstance(job,str):
            return text_key(job)
        if job[0] == 'website':
            return action('Website','system.website',{'path':job[1],'openInBrowser':True})
        if job[0] == 'folder':
            return action('Create Folder','profile.openchild',{'ProfileUUID':folder_ids[job[1]].lower()})
        if job[0] == 'back':
            return action('Parent Folder','profile.backtoparent',{})
        if len(job) == 1:
            return hotkey(job[0])
        return sequence(job)
    with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
        def dump(path,obj):
            z.writestr(path,json.dumps(obj,ensure_ascii=False))
        for directory in (root,root+'Images/',root+'Profiles/'):
            z.mkdir(directory)
        dump(root+'manifest.json',top)
        pages = [(base,'',None), (page,'',MAIN)]
        pages.extend((folder_ids[key],name,buttons) for key,(name,buttons) in folders.items())
        for page_index,(identifier,name,buttons) in enumerate(pages):
            folder = f'{root}Profiles/{legacy_folder(identifier)}/'
            z.mkdir(folder)
            z.mkdir(folder+'Images/')
            actions = None
            if buttons:
                assert len(buttons) <= 32
                actions = {}
                for i,entry in enumerate(buttons):
                    if entry is None:
                        continue
                    kind,symbol,label,job = entry
                    key = button(job)
                    file = icon(page_index*32+i,kind,symbol,label)
                    image = f'Images/{file.name}'
                    z.write(file,folder+image)
                    key['States'] = [{'Image':image,'ShowTitle':False,'Title':label}]
                    actions[f'{i%8},{i//8}'] = key
            dump(folder+'manifest.json', {'Controllers':[{'Actions':actions,'Type':'Keypad'}],'Icon':'','Name':name})
    with ZipFile(OUT) as z:
        assert z.testzip() is None
    print(OUT.resolve())

if __name__ == '__main__':
    build()

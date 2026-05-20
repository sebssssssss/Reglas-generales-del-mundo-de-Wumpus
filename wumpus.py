"""
╔══════════════════════════════════════════════════════════════╗
║  Práctica 5 — Inteligencia Artificial                        ║
║  Alumno: Pérez Moncayo Gonzalo Sebastian                     ║
║  Mundo de Wumpus                                             ║
║  ESCOM-IPN                                                   ║
╠══════════════════════════════════════════════════════════════╣
║  INSTRUCCIONES DE EJECUCIÓN                                  ║
║                                                              ║
║  1) Modo demo automático (percepciones predefinidas):        ║
║       python wumpus_kb.py                                    ║
║                                                              ║
║  2) Modo interactivo — grid 4x4 (por defecto):               ║
║       python wumpus_kb.py interactivo                        ║
║                                                              ║
║  3) Modo interactivo — grid personalizado (ej. 5x5):         ║
║       python wumpus_kb.py interactivo 5                      ║
║                                                              ║
║  Formato de percepcion (modo interactivo):                   ║
║    Texto libre : (i,j) - brisa hedor destello choque grito   ║
║    Lista       : (i,j) - [brisa, hedor]                      ║
║    Sin percep. : (i,j) -                                     ║
║                                                              ║
║  Comandos disponibles en modo interactivo:                   ║
║    resumen              -> muestra hechos registrados        ║
║    clausulas            -> lista clausulas unitarias KB      ║
║    grid                 -> visualiza estado del grid         ║
║    consulta <simbolo>   -> consulta un simbolo proposicional ║
║    salir                -> termina el programa               ║
╚══════════════════════════════════════════════════════════════╝
"""

def P(i, j):       return f"P_{i}_{j}"  
def W(i, j):       return f"W_{i}_{j}"   
def B(i, j):       return f"B_{i}_{j}"    
def S(i, j):       return f"S_{i}_{j}"    
def OK(i, j):      return f"OK_{i}_{j}"   
def V(i, j):       return f"V_{i}_{j}"    
def G(i, j):       return f"G_{i}_{j}"    
def Glitter(i, j): return f"GL_{i}_{j}"   
def Bump():        return "BUMP"           
def Scream():      return "SCREAM"         

class Literal:
    """Literal proposicional: simbolo positivo o negado."""

    def __init__(self, symbol: str, negated: bool = False):
        self.symbol  = symbol
        self.negated = negated

    def negate(self):
        return Literal(self.symbol, not self.negated)

    def __repr__(self):
        return ("!" + self.symbol) if self.negated else self.symbol

    def __eq__(self, other):
        return (isinstance(other, Literal)
                and self.symbol  == other.symbol
                and self.negated == other.negated)

    def __hash__(self):
        return hash((self.symbol, self.negated))


class Clause:
    """Clausula FNC: disyuncion de literales."""

    def __init__(self, literals: list):
        self.literals = list(set(literals))

    def is_tautology(self):
        seen = {}
        for l in self.literals:
            if l.symbol in seen and seen[l.symbol] != l.negated:
                return True
            seen[l.symbol] = l.negated
        return False

    def __repr__(self):
        if not self.literals:
            return "[]"
        return "(" + " v ".join(str(l) for l in self.literals) + ")"

    def __eq__(self, other):
        return isinstance(other, Clause) and set(self.literals) == set(other.literals)

    def __hash__(self):
        return hash(frozenset(self.literals))


def lit(symbol: str, neg: bool = False) -> Literal:
    return Literal(symbol, neg)

def clause(*literals) -> Clause:
    return Clause(list(literals))


def biconditional_to_cnf(left: Literal, right_lits: list) -> list:
    """
    left <-> (R1 v R2 v ... v Rn)
    ->  (!left v R1 v ... v Rn)
        (!R1 v left), (!R2 v left), ..., (!Rn v left)
    """
    clauses = [Clause([left.negate()] + right_lits)]
    for r in right_lits:
        clauses.append(Clause([r.negate(), left]))
    return clauses


def get_neighbors(i, j, n):
    """Vecinos ortogonales validos en grid nxn (1-indexado)."""
    return [(i+di, j+dj)
            for di, dj in [(-1,0),(1,0),(0,-1),(0,1)]
            if 1 <= i+di <= n and 1 <= j+dj <= n]


def encode_domain_rules(n: int) -> list:
    """
    Codifica en FNC las reglas generales del Mundo de Wumpus:
      R1: B(i,j) <-> v P(vecinos)        [brisa <-> pozo adyacente]
      R2: S(i,j) <-> v W(vecinos)        [hedor <-> wumpus adyacente]
      R3: OK(i,j) <-> !P(i,j) ^ !W(i,j) [seguro <-> sin pozo y sin wumpus]
      R4: GL(i,j) -> G(i,j)              [destello -> hay oro]
      R5: exactamente un Wumpus          [at-least-one + at-most-one]
    """
    clauses = []
    all_cells = [(i, j) for i in range(1, n+1) for j in range(1, n+1)]

    for i, j in all_cells:
        nbrs = get_neighbors(i, j, n)

        nbr_p = [lit(P(ni, nj)) for ni, nj in nbrs]
        if nbr_p:
            clauses.extend(biconditional_to_cnf(lit(B(i,j)), nbr_p))

        nbr_w = [lit(W(ni, nj)) for ni, nj in nbrs]
        if nbr_w:
            clauses.extend(biconditional_to_cnf(lit(S(i,j)), nbr_w))

        clauses.append(clause(lit(OK(i,j), neg=True), lit(P(i,j), neg=True)))
        clauses.append(clause(lit(OK(i,j), neg=True), lit(W(i,j), neg=True)))
        clauses.append(clause(lit(P(i,j)), lit(W(i,j)), lit(OK(i,j))))

        clauses.append(clause(lit(Glitter(i,j), neg=True), lit(G(i,j))))

    clauses.append(Clause([lit(W(i,j)) for i,j in all_cells]))

    for a in range(len(all_cells)):
        for b in range(a+1, len(all_cells)):
            ci,cj = all_cells[a]
            ck,cl = all_cells[b]
            clauses.append(clause(lit(W(ci,cj), neg=True), lit(W(ck,cl), neg=True)))

    return [c for c in clauses if not c.is_tautology()]


class KnowledgeBase:
    """
    Base de Conocimiento Proposicional en FNC para el Mundo de Wumpus.
    Se inicializa con las reglas del dominio y se actualiza con tell().
    """

    def __init__(self, n: int = 4):
        self.n = n
        self.clauses: set = set()
        self.facts: list = []
        self._add_domain_rules()

    def _add_domain_rules(self):
        for c in encode_domain_rules(self.n):
            self.clauses.add(c)

    def add_clause(self, c: Clause, label: str = ""):
        if not c.is_tautology():
            self.clauses.add(c)
            if label:
                self.facts.append(f"[{label}] {c}")

    def add_fact(self, symbol: str, value: bool = True, label: str = ""):
        """Agrega literal unitario a la KB."""
        c = Clause([Literal(symbol, not value)])
        self.add_clause(c, label or (("" if value else "!") + symbol))


    def tell(self, percepts: dict, position: tuple):
        """
        Traduce las percepciones de una casilla a clausulas FNC
        y las incorpora a la KB.

        percepts: dict con claves: 'brisa', 'hedor', 'destello', 'choque', 'grito'
        position: (i, j)
        """
        i, j = position
        lp = f"({i},{j})"

        self.add_fact(V(i,j), True, f"{lp} visitada")

        self.add_fact(B(i,j),
                      percepts.get('brisa', False),
                      f"{lp} {'brisa' if percepts.get('brisa') else 'sin brisa'}")
        self.add_fact(S(i,j),
                      percepts.get('hedor', False),
                      f"{lp} {'hedor' if percepts.get('hedor') else 'sin hedor'}")
        self.add_fact(Glitter(i,j),
                      percepts.get('destello', False),
                      f"{lp} {'destello' if percepts.get('destello') else 'sin destello'}")

        if percepts.get('choque',  False):
            self.add_fact(Bump(),   True, f"{lp} choque")
        if percepts.get('grito',   False):
            self.add_fact(Scream(), True, f"{lp} grito-wumpus-muerto")

        if not percepts.get('brisa', False):
            for ni, nj in get_neighbors(i, j, self.n):
                self.add_fact(P(ni,nj),  False, f"{lp} inferido !pozo({ni},{nj})")
                self.add_fact(OK(ni,nj), True,  f"{lp} inferido OK({ni},{nj})")

        if not percepts.get('hedor', False):
            for ni, nj in get_neighbors(i, j, self.n):
                self.add_fact(W(ni,nj), False, f"{lp} inferido !wumpus({ni},{nj})")


    def query(self, symbol: str) -> str:
        """Consulta el valor de un simbolo: True / False / Desconocido / Contradiccion."""
        pos_c = Clause([Literal(symbol, False)])
        neg_c = Clause([Literal(symbol, True)])
        has_pos = pos_c in self.clauses
        has_neg = neg_c in self.clauses
        if has_pos and has_neg: return "Contradiccion"
        if has_pos:             return "True"
        if has_neg:             return "False"
        return "Desconocido"


    def print_grid(self):
        """
        Muestra el estado actual del grid casilla por casilla.
        Leyenda:
          V  = visitada       OK = segura confirmada
          P! = pozo aqui      !P = sin pozo confirmado
          W! = wumpus aqui    !W = sin wumpus confirmado
          G! = oro aqui       B  = brisa    S  = hedor
          ?  = desconocido
        """
        n = self.n
        sep = "+" + ("-"*16 + "+") * n
        print(f"\n  Estado del grid {n}x{n}  (j=N arriba, j=1 abajo)")
        print(sep)

        for j in range(n, 0, -1):
            line1 = "|"
            line2 = "|"
            for i in range(1, n+1):
                info_top = []
                info_bot = []

                qok = self.query(OK(i,j))
                qp  = self.query(P(i,j))
                qw  = self.query(W(i,j))
                qv  = self.query(V(i,j))

                if qv  == "True":  info_top.append("V")
                if qok == "True":  info_top.append("OK")
                if qp  == "True":  info_top.append("P!")
                if qp  == "False": info_top.append("!P")
                if qw  == "True":  info_top.append("W!")
                if qw  == "False": info_top.append("!W")

                qg  = self.query(G(i,j))
                qb  = self.query(B(i,j))
                qs  = self.query(S(i,j))
                if qg == "True":   info_bot.append("G!")
                if qb == "True":   info_bot.append("B")
                if qs == "True":   info_bot.append("S")

                top = ",".join(info_top) if info_top else "?"
                bot = ",".join(info_bot) if info_bot else ""

                line1 += f" {top:^14}|"
                line2 += f" {('('+bot+')') if bot else '':^14}|"

            print(f" j={j} {line1}")
            print(f"      {line2}")
            print(sep)

        col_header = "      " + "".join(f"  {'i='+str(i):^14}" for i in range(1, n+1))
        print(col_header)
        print()
        print("  Leyenda: V=visitada  OK=segura  P!/W!/G!=peligro/oro aqui")
        print("           !P/!W=confirmado ausente  B=brisa  S=hedor  ?=desconocido")


    def summary(self) -> str:
        lines = [
            "\n" + "="*62,
            f"  KB -- Mundo Wumpus {self.n}x{self.n}",
            f"  Total clausulas FNC: {len(self.clauses)}",
            "="*62,
            "  Hechos percibidos / inferidos:"
        ]
        for f in self.facts:
            lines.append(f"    {f}")
        return "\n".join(lines)

    def print_clauses(self, max_show: int = 25):
        unit = sorted(str(c) for c in self.clauses if len(c.literals) == 1)
        print(f"\n--- Clausulas unitarias ({len(unit)} total) ---")
        for c in unit[:max_show]:
            print(f"  {c}")
        if len(unit) > max_show:
            print(f"  ... ({len(unit) - max_show} mas)")


KEYWORDS = {
    'brisa':    'brisa',    'breeze':   'brisa',
    'hedor':    'hedor',    'stench':   'hedor',
    'destello': 'destello', 'glitter':  'destello',
    'choque':   'choque',   'bump':     'choque',
    'grito':    'grito',    'scream':   'grito',
}

def parse_perception(raw: str) -> tuple:
    """
    Parsea una percepcion con formato:
        (i,j) - <percepciones>

    La parte de percepciones acepta:
        Texto libre : brisa hedor destello
        Lista Python: [brisa, hedor, destello]
        Vacio       : (ninguna percepcion)

    Retorna ((i, j), dict_percepciones).
    """
    raw = raw.strip()
    parts = raw.split("-", 1)
    if len(parts) < 2:
        raise ValueError(
            f"Formato invalido: '{raw}'\n"
            "  Usa: (i,j) - [brisa] [hedor] [destello] [choque] [grito]"
        )

    pos_str = parts[0].strip().strip("() ")
    coords  = pos_str.split(",")
    if len(coords) != 2:
        raise ValueError(f"Coordenada invalida: '{parts[0].strip()}'")
    i, j = int(coords[0].strip()), int(coords[1].strip())

    percept_str = parts[1].strip().lower().strip("[]").replace(",", " ")

    percepts = {v: False for v in ('brisa','hedor','destello','choque','grito')}
    for token in percept_str.split():
        key = KEYWORDS.get(token)
        if key:
            percepts[key] = True

    return (i, j), percepts


def run_interactive(n: int = 4):
    kb = KnowledgeBase(n)
    print("\n" + "="*62)
    print(f"  Mundo de Wumpus {n}x{n}  --  KB inicializada")
    print(f"  Clausulas de dominio cargadas: {len(kb.clauses)}")
    print("="*62)
    print("  Formato  : (i,j) - [brisa] [hedor] [destello] [choque] [grito]")
    print("  O lista  : (i,j) - [brisa, hedor]")
    print("  Comandos : resumen | clausulas | grid | consulta <sim> | salir\n")

    while True:
        try:
            entrada = input("Percepcion > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo...")
            break

        if not entrada:
            continue

        cmd = entrada.lower()

        if cmd == 'salir':
            break
        elif cmd == 'resumen':
            print(kb.summary())
        elif cmd == 'clausulas':
            kb.print_clauses()
        elif cmd == 'grid':
            kb.print_grid()
        elif cmd.startswith('consulta '):
            sym = entrada.split(' ', 1)[1].strip()
            print(f"  {sym}  -->  {kb.query(sym)}")
        else:
            try:
                pos, percepts = parse_perception(entrada)
                kb.tell(percepts, pos)
                activas = [k for k, v in percepts.items() if v] or ['ninguna']
                print(f"  OK {pos}  percepciones={activas}  clausulas KB={len(kb.clauses)}")
                kb.print_grid()
            except ValueError as e:
                print(f"  ERROR: {e}")

    print(kb.summary())


def run_demo():
    print("\n" + "="*62)
    print("  PRACTICA 5 -- MUNDO DE WUMPUS -- BASE DE CONOCIMIENTO FNC")
    print("="*62)

    n = 4
    kb = KnowledgeBase(n)
    print(f"\n[INIT] Grid {n}x{n} -- Clausulas de dominio cargadas: {len(kb.clauses)}\n")

    percepciones = [
        ("(1,1) - ",               "Inicio: sin percepcion"),
        ("(1,2) - brisa",          "Norte: brisa detectada"),
        ("(2,1) - hedor",          "Este: hedor detectado"),
        ("(2,2) - [brisa, hedor]", "Diagonal: brisa y hedor (formato lista)"),
        ("(1,3) - brisa, destello","Destello: oro cerca!"),
    ]

    for raw, desc in percepciones:
        pos, percepts = parse_perception(raw)
        kb.tell(percepts, pos)
        print(f"[TELL] {pos}  --  {desc}")
        print(f"       Total clausulas KB: {len(kb.clauses)}")

    print(kb.summary())
    kb.print_clauses()
    kb.print_grid()

    print("\n--- Consultas de ejemplo ---")
    consultas = [
        (P(1,1),  "Pozo en (1,1)?"),
        (P(1,3),  "Pozo en (1,3)?"),
        (W(1,1),  "Wumpus en (1,1)?"),
        (W(3,1),  "Wumpus en (3,1)?"),
        (OK(1,1), "Segura (1,1)?"),
        (OK(2,2), "Segura (2,2)?"),
        (G(1,3),  "Oro en (1,3)?"),
        (B(1,2),  "Brisa en (1,2)?"),
        (S(2,1),  "Hedor en (2,1)?"),
    ]
    for sym, pregunta in consultas:
        print(f"  {pregunta:<25}  {sym:<15} --> {kb.query(sym)}")

    print("\n[FIN] Demo completada.\n")
    return kb


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactivo":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        run_interactive(n)
    else:
        run_demo()

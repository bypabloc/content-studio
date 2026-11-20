/**
 * Textos sueltos del client (spec 007, AC-5 y D-8). Lo llama la etapa `i18n` de devtools con bun.
 *
 * Uso: `bun run --cwd client loose-texts <archivo.ts|tsx>...`. stdout = un JSON con los hallazgos; stderr = el error si
 * algo falla (exit 2). La regla de «qué cuenta como texto» es la de devtools/test_runner/i18n_loose.py: la prueban con la
 * misma tabla (devtools/tests/fixtures/i18n/prose-cases.json).
 */
import { readFileSync } from 'node:fs';
import ts from 'typescript';

interface Finding {
  path: string;
  line: number;
  text: string;
  reasonMissing: boolean;
}

// Atributos JSX que no muestran texto (la clase, la clave, el id, el tipo, el enlace...).
const NON_VISIBLE_ATTRIBUTES = new Set([
  'className',
  'class',
  'style',
  'key',
  'id',
  'role',
  'type',
  'href',
  'src',
  'name',
  'htmlFor',
  'aria-controls',
  'aria-describedby',
  'aria-labelledby',
]);
// Llamadas cuyos argumentos son clases de estilo, no texto.
const STYLE_CALLS = new Set(['cn', 'clsx', 'cva']);
const MARKER = /\/\/\s*i18n-ignore:(.*)$/;

/** La regla de «qué cuenta como texto» (la misma que i18n_loose.is_prose). */
export function isProse(text: string): boolean {
  const stripped = text.trim();
  if (![...stripped].some((char) => /\p{L}/u.test(char))) return false;
  if ([...stripped].some((char) => char === '¿' || char === '¡' || (char.charCodeAt(0) > 127 && /\p{L}/u.test(char)))) {
    return true;
  }
  const words = stripped.split(/\s+/);
  if (words.filter((word) => /\p{L}/u.test(word)).length >= 2) return true;
  return words.length === 1 && /^\p{Lu}/u.test(stripped) && stripped.slice(1) === stripped.slice(1).toLowerCase();
}

// Cabeceras HTTP: su nombre y su valor no se muestran al usuario.
const HEADER_NAMES = new Set(['Authorization', 'Accept-Language', 'Content-Type']);

/** URL, selector CSS o consulta de media: no son texto visible. */
function isUrlOrSelector(text: string): boolean {
  return text.includes('://') || /^[/#.[]/.test(text) || /^\([\w-]+:\s*[\w-]+\)$/.test(text);
}

// Trozos de una lista de clases de Tailwind: minúsculas y sin espacios, con puntos, corchetes o paréntesis.
const CLASS_TOKEN = /^[a-z0-9\-:[\]\/!.%()_,#*&@'"=+>~^$|\\]+$/;
// Las marcas que solo tienen las clases: un guion, dos puntos, un corchete, una barra, `!`, `*`, `&` o `@`.
const CLASS_MARK = /[-:[\]\/!*&@]/;

/**
 * Lista de clases de Tailwind (`bg-primary hover:bg-primary/80`), no texto. Un literal cuyos trozos son todos
 * clases y al menos uno tiene una marca de utilidad: `cva` y los objetos de variantes de shadcn lo usan.
 * Un texto con mayúscula o con tilde no cuenta como clase, y una frase en minúsculas sin marca tampoco.
 */
function isClassList(text: string): boolean {
  const tokens = text.trim().split(/\s+/);
  return tokens.every((token) => CLASS_TOKEN.test(token)) && tokens.some((token) => CLASS_MARK.test(token));
}

/** El primer atributo JSX del que cuelga el literal (`className={cond ? 'a' : 'b'}` cuenta como className). */
function enclosingAttribute(node: ts.Node): ts.JsxAttribute | undefined {
  let current: ts.Node | undefined = node.parent;
  while (current && !ts.isJsxAttribute(current) && !ts.isJsxElement(current) && !ts.isSourceFile(current)) {
    current = current.parent;
  }
  return current && ts.isJsxAttribute(current) ? current : undefined;
}

function calleeName(node: ts.CallExpression): string {
  const callee = node.expression;
  if (ts.isIdentifier(callee)) return callee.text;
  if (ts.isPropertyAccessExpression(callee)) return callee.expression.getText();
  return '';
}

/** ¿Este literal no es texto visible por su posición en el código? */
function isExempt(node: ts.Node): boolean {
  const parent = node.parent;
  if (
    ts.isImportDeclaration(parent) ||
    ts.isExportDeclaration(parent) ||
    ts.isLiteralTypeNode(parent) ||
    ts.isImportTypeNode(parent) ||
    ts.isExternalModuleReference(parent)
  ) {
    return true;
  }
  if (ts.isPropertyAssignment(parent) && parent.name === node) return true;
  if (ts.isPropertyAssignment(parent) && parent.initializer === node && HEADER_NAMES.has(parent.name.getText())) {
    return true;
  }
  if (ts.isElementAccessExpression(parent) && parent.argumentExpression === node) return true;
  // Comparar con una tecla (`event.key === 'Escape'`) o un código no muestra nada.
  if (ts.isBinaryExpression(parent) && isEqualityOperator(parent.operatorToken.kind)) {
    const other = parent.left === node ? parent.right : parent.left;
    if (ts.isPropertyAccessExpression(other) && ['key', 'code'].includes(other.name.text)) return true;
  }
  // El mensaje de un error de programación (`throw new Error(...)`) va en inglés y no se muestra.
  if (ts.isNewExpression(parent) && parent.expression.getText() === 'Error' && ts.isThrowStatement(parent.parent)) {
    return true;
  }
  if (ts.isCallExpression(parent)) {
    const callee = calleeName(parent);
    if (callee === 'console' || callee.startsWith('console.')) return true;
    if (STYLE_CALLS.has(callee)) return true;
    if (callee === 't' && parent.arguments[0] === node) return true;
  }
  const attribute = enclosingAttribute(node);
  return attribute !== undefined && attributeIsExempt(attribute.name.getText());
}

function isEqualityOperator(kind: ts.SyntaxKind): boolean {
  return [
    ts.SyntaxKind.EqualsEqualsEqualsToken,
    ts.SyntaxKind.ExclamationEqualsEqualsToken,
    ts.SyntaxKind.EqualsEqualsToken,
    ts.SyntaxKind.ExclamationEqualsToken,
  ].includes(kind);
}

function attributeIsExempt(name: string): boolean {
  return NON_VISIBLE_ATTRIBUTES.has(name) || name.startsWith('data-');
}

/** El texto del nodo, o undefined si no es un literal que mostrar. */
function literalText(node: ts.Node): string | undefined {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (ts.isTemplateExpression(node)) return node.head.text;
  if (ts.isJsxText(node)) return node.text.trim();
  return undefined;
}

export function findLoose(path: string): Finding[] {
  const text = readFileSync(path, 'utf8');
  const source = ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true);
  const lines = text.split(/\r?\n/); // Windows guarda los archivos con CRLF: el \r no es parte de la línea.
  const findings: Finding[] = [];
  const markerLines = new Set<number>();

  lines.forEach((line, index) => {
    const match = MARKER.exec(line);
    if (!match) return;
    markerLines.add(index + 1);
    if (match[1].trim() === '') findings.push({ path, line: index + 1, text: '', reasonMissing: true });
  });

  const visit = (node: ts.Node): void => {
    const value = literalText(node);
    if (value !== undefined && isProse(value) && !isUrlOrSelector(value) && !isClassList(value) && !isExempt(node)) {
      const line = source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1;
      // Una plantilla se muestra completa (`Hola ${name}`), no solo su primer trozo.
      const shown = ts.isTemplateExpression(node) ? node.getText(source).slice(1, -1) : value;
      if (!markerLines.has(line)) findings.push({ path, line, text: shown, reasonMissing: false });
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return findings;
}

function main(argv: string[]): number {
  if (argv.length === 0) {
    process.stderr.write('usage: bun run --cwd client loose-texts <file.ts|file.tsx>...\n');
    return 2;
  }
  try {
    const findings = argv.flatMap((path) => findLoose(path));
    process.stdout.write(JSON.stringify(findings));
    return 0;
  } catch (error) {
    process.stderr.write(`loose-texts: ${error instanceof Error ? error.message : String(error)}\n`);
    return 2;
  }
}

if (import.meta.main) {
  process.exitCode = main(process.argv.slice(2));
}

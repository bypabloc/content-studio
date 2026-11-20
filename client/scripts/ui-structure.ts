/**
 * Etiquetas nativas fuera de los átomos (spec 008, AC-2 y D-5). Lo llama la etapa `ui-structure` de devtools con bun.
 *
 * Uso: `bun run --cwd client ui-structure <archivo.tsx>...`. stdout = un JSON con los hallazgos; stderr = el error si
 * algo falla (exit 2). Marca tres formas: un elemento JSX en minúscula (`<div>`), un `createElement('span')` con cadena
 * literal y un `<Tag>` cuya constante vale una cadena (`const Tag = 'h1'`). Las carpetas `atoms/` y `shadcn/` no pasan
 * por aquí: las excluye el llamador (devtools/test_runner/ui_structure.py).
 */
import { readFileSync } from 'node:fs';
import ts from 'typescript';

export interface Finding {
  path: string;
  line: number;
  tag: string;
}

// Una etiqueta nativa es una palabra en minúscula (`div`, `h1`, `svg`); un componente empieza en mayúscula.
const NATIVE_TAG = /^[a-z][a-z0-9-]*$/;

function isStringLiteral(node: ts.Expression): node is ts.StringLiteral | ts.NoSubstitutionTemplateLiteral {
  return ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node);
}

function isCreateElement(callee: ts.Expression): boolean {
  return (
    (ts.isIdentifier(callee) && callee.text === 'createElement') ||
    (ts.isPropertyAccessExpression(callee) && callee.name.text === 'createElement')
  );
}

/** Las etiquetas nativas de un archivo, con su línea (desde 1). */
export function findNativeTags(path: string, text: string): Finding[] {
  const source = ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

  // Primera pasada: las constantes que valen una cadena (`const Tag = 'h1'`), para resolver `<Tag>`.
  const constants = new Map<string, string>();
  const collect = (node: ts.Node): void => {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.initializer &&
      isStringLiteral(node.initializer)
    ) {
      constants.set(node.name.text, node.initializer.text);
    }
    ts.forEachChild(node, collect);
  };
  collect(source);

  const findings: Finding[] = [];
  const report = (node: ts.Node, tag: string): void => {
    const { line } = source.getLineAndCharacterOfPosition(node.getStart(source));
    findings.push({ path, line: line + 1, tag });
  };
  const visit = (node: ts.Node): void => {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      if (ts.isIdentifier(node.tagName)) {
        // En JSX, un nombre en minúscula es siempre una etiqueta nativa; uno en mayúscula es un componente o una constante.
        const name = node.tagName.text;
        const value = NATIVE_TAG.test(name) ? name : constants.get(name);
        if (value !== undefined && NATIVE_TAG.test(value)) report(node, value);
      }
    }
    if (ts.isCallExpression(node) && isCreateElement(node.expression) && node.arguments.length > 0) {
      const first = node.arguments[0];
      if (isStringLiteral(first) && NATIVE_TAG.test(first.text)) report(node, first.text);
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return findings;
}

function main(argv: string[]): number {
  if (argv.length === 0) {
    process.stderr.write('usage: bun run --cwd client ui-structure <file.tsx>...\n');
    return 2;
  }
  try {
    const findings = argv.flatMap((path) => findNativeTags(path, readFileSync(path, 'utf-8')));
    process.stdout.write(JSON.stringify(findings));
    return 0;
  } catch (error) {
    process.stderr.write(`ui-structure: ${error instanceof Error ? error.message : String(error)}\n`);
    return 2;
  }
}

if (import.meta.main) {
  process.exitCode = main(process.argv.slice(2));
}

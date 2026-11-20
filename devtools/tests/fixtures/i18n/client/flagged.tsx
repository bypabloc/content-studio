export function Foo({ name }: { name: string }) {
  const label = 'Abrir carpeta';
  toast('Listo');
  return (
    <div>
      <button aria-label="Cerrar">x</button>
      <p>{`Hola ${name}`}</p>
    </div>
  );
}

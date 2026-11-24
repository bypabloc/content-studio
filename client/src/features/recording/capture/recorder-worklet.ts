// AudioWorklet: corre en el hilo de audio y manda cada bloque de 128 muestras al hilo principal (spec 010, D-2).
// Vite lo empaqueta con `?worker&url` (useRecorder.ts): por eso no lleva imports.

declare class AudioWorkletProcessor {
  readonly port: MessagePort;
}
declare function registerProcessor(name: string, processor: new () => AudioWorkletProcessor): void;

class RecorderProcessor extends AudioWorkletProcessor {
  process(inputs: Float32Array[][]): boolean {
    const channel = inputs[0]?.[0];
    if (channel) this.port.postMessage(channel.slice(0)); // copia: el hilo de audio reutiliza el bloque
    return true;
  }
}

registerProcessor('recorder', RecorderProcessor);

// Sin imports ni exports el archivo sería un script: `export {}` lo deja como módulo, que es lo que carga addModule.
export {};

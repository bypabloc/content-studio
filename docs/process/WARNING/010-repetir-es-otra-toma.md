# 010: «Repetir» graba otra toma del mismo estilo, con el mismo inicio y parada que «Grabar»

- **Contexto**: la sección Grabar de la spec pide «Siguiente» y «Repetir». Las tomas no se sobrescriben: se comparan y se elige una.
- **Elegida**: «Repetir» hace lo mismo que «Grabar»; la toma nueva se suma a la lista del estilo y las anteriores se quedan.
- **Descartadas**: borrar la toma anterior al repetir (pierde una toma que quizá era la mejor); quitar «Repetir» (la spec lo nombra).
- **Cómo revertir**: quitar el botón «Repetir» de `RecordWizard.tsx`.
- **Cómo comprobarla**: en la app, con dos tomas del mismo estilo (corrida real, T9).
- **Pendiente**: [010-grabar-con-microfono-real](../PENDING/010-grabar-con-microfono-real.md).

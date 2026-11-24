; Content Studio (spec 022, D-5). Al desinstalar, la casilla de Tauri «Borrar los datos de la aplicación» también borra,
; tras una confirmación más, los motores, voces, base y salidas por defecto de %LOCALAPPDATA%\Content Studio y de
; Documentos\Content Studio. Sin la casilla, o en una actualización, los datos quedan para una reinstalación.
!macro NSIS_HOOK_POSTUNINSTALL
  ${If} $DeleteAppDataCheckboxState = 1
  ${AndIf} $UpdateMode <> 1
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "¿Borrar también los motores, las voces y las salidas de Content Studio? No se puede deshacer." IDNO content_studio_keep_data
    RMDir /r "$LOCALAPPDATA\Content Studio"
    RMDir /r "$DOCUMENTS\Content Studio"
    content_studio_keep_data:
  ${EndIf}
!macroend

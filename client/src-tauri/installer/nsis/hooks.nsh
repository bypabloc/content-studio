; Content Studio (spec 022, D-5). Al desinstalar, la casilla de Tauri «Borrar los datos de la aplicación» también borra,
; tras una confirmación más, los motores, voces, base y salidas por defecto de %LOCALAPPDATA%\Content Studio y de
; Documentos\Content Studio. Con CONTENT_STUDIO_HOME (una instalación aislada, como la de las pruebas) borra solo esa
; carpeta, igual que la app guarda ahí todo. Sin la casilla, o en una actualización, los datos quedan.
; El server corre desde $INSTDIR\app (instalación editable): Python deja ahí sus __pycache__, que el desinstalador no
; conoce. Esa carpeta es solo de la app, así que se borra entera.
; «Enviar a» (spec 031, AC-6, D-3): cinco accesos directos en la carpeta SendTo del usuario, sin admin. Al elegirlos,
; el Explorador pasa los archivos como argumentos tras --send <acción> (client/src/app/external/parseExternal.ts).
!macro NSIS_HOOK_POSTINSTALL
  CreateShortCut "$SENDTO\Content Studio - Convertir a MP3.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "--send convert-mp3"
  CreateShortCut "$SENDTO\Content Studio - Normalizar.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "--send normalize"
  CreateShortCut "$SENDTO\Content Studio - Limpiar silencios.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "--send clean"
  CreateShortCut "$SENDTO\Content Studio - Transcribir.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "--send transcribe"
  CreateShortCut "$SENDTO\Content Studio - Abrir en el Editor.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "--send editor"
!macroend
!macro NSIS_HOOK_POSTUNINSTALL
  RMDir /r "$INSTDIR\app"
  ; Los accesos de «Enviar a» (AC-6) se quitan con la app.
  Delete "$SENDTO\Content Studio - Convertir a MP3.lnk"
  Delete "$SENDTO\Content Studio - Normalizar.lnk"
  Delete "$SENDTO\Content Studio - Limpiar silencios.lnk"
  Delete "$SENDTO\Content Studio - Transcribir.lnk"
  Delete "$SENDTO\Content Studio - Abrir en el Editor.lnk"
  ${If} $DeleteAppDataCheckboxState = 1
  ${AndIf} $UpdateMode <> 1
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "¿Borrar también los motores, las voces y las salidas de Content Studio? No se puede deshacer." /SD IDYES IDNO content_studio_keep_data
    ReadEnvStr $R0 CONTENT_STUDIO_HOME
    ${If} $R0 != ""
      RMDir /r "$R0"
    ${Else}
      RMDir /r "$LOCALAPPDATA\Content Studio"
      RMDir /r "$DOCUMENTS\Content Studio"
    ${EndIf}
    content_studio_keep_data:
  ${EndIf}
!macroend

; NSIS installer header, included from bundle.nsi.
; This file is dedicated into the public domain, CC0 v1.0.
; https://creativecommons.org/publicdomain/zero/1.0/

!include "Library.nsh"



; Associates a file with an executable.
; Any existing sssociation is backed up first, so that the
; uninstaller can remove it.
;
; Example:  !insertmacro FileAssoc "xxx" "y.xFile" "$INSTDIR\y.exe,0" \
;                        "Open with Y" "$INSTDIR\y.exe $\"%1$\""

!macro FileAssoc EXT FILETYPE FILEDESC ICO EXPLANATION CMDLINE
    ReadRegStr $R0 HKCR ".${EXT}" ""
    WriteRegStr HKCR ".${EXT}" "${FILETYPE}_backup" "$R0"

    WriteRegStr HKCR ".${EXT}" "" "${FILETYPE}"
    WriteRegStr HKCR "${FILETYPE}" "" "${FILEDESC}"
    WriteRegStr HKCR "${FILETYPE}\DefaultIcon" "" "${ICO}"
    WriteRegStr HKCR "${FILETYPE}\shell" "" "open"
    WriteRegStr HKCR "${FILETYPE}\shell\open" "" "${EXPLANATION}"
    WriteRegStr HKCR "${FILETYPE}\shell\open\command" "" "${CMDLINE}"
!macroend


; Un-associates a previous file association.
; Example: !insertmacro FileUnAssoc "xxx" "y.xFile"

!macro FileUnAssoc EXT FILETYPE
    ReadRegStr $R0 HKCR ".${EXT}" "${FILETYPE}_backup"
    WriteRegStr HKCR ".${EXT}" "" "$R0"

    DeleteRegKey HKCR "${FILETYPE}"
!macroend


; Updates the system's view of the registry's file associations.
; Example: !insertmacro UpdateFileAssocs

!macro UpdateFileAssocs
    System::Call "shell32::SHChangeNotify(i,i,i,i) (${SHCNE_ASSOCCHANGED}, 0, 0, 0)"
!macroend


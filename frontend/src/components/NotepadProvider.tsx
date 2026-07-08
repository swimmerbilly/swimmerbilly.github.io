import { createContext, useContext, useState, type ReactNode } from "react";
import CallNotepad from "./CallNotepad";

interface NotepadContextValue {
  openNotepad: (projectId?: number) => void;
}

const NotepadContext = createContext<NotepadContextValue>({
  openNotepad: () => undefined,
});

export function useCallNotepad() {
  return useContext(NotepadContext);
}

export function NotepadProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [projectId, setProjectId] = useState<number | null>(null);

  const openNotepad = (id?: number) => {
    setProjectId(id ?? null);
    setOpen(true);
  };

  return (
    <NotepadContext.Provider value={{ openNotepad }}>
      {children}
      <button className="notepad-fab" onClick={() => openNotepad()} title="Open call notepad">
        <span>📞</span>
        Call Notes
      </button>
      <CallNotepad
        open={open}
        onClose={() => setOpen(false)}
        initialProjectId={projectId}
      />
    </NotepadContext.Provider>
  );
}

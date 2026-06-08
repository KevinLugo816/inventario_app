"use client";

import { createContext, useContext, useState, useEffect } from "react";

const ChatContext = createContext<any>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [chat, setChat] = useState<{ emisor: string; texto: string }[]>([]);
  const [typing, setTyping] = useState(false);

  // Cargar historial o mensaje inicial
  useEffect(() => {
    const saved = localStorage.getItem("chatBell");

    if (saved) {
      setChat(JSON.parse(saved));
    } else {
      setChat([
        { emisor: "ia", texto: "Hola, ¿en qué te ayudo hoy?" }
      ]);
    }
  }, []);

  // Guardar historial
  useEffect(() => {
    localStorage.setItem("chatBell", JSON.stringify(chat));
  }, [chat]);

  return (
    <ChatContext.Provider value={{ chat, setChat, typing, setTyping }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  return useContext(ChatContext);
}

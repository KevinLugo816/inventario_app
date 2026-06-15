"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@/context/ChatContext";

type Mensaje = { emisor: "tú" | "ia"; texto: string };

export default function Chat() {
  const [mensaje, setMensaje] = useState("");
  const { chat, setChat, typing, setTyping } = useChat();
  const chatRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const enviar = async () => {
    if (!mensaje.trim()) return;

    inputRef.current?.classList.add("animate-[shake_.2s]");
    setTimeout(() => inputRef.current?.classList.remove("animate-[shake_.2s]"), 200);

    setChat((prev: Mensaje[]) => [...prev, { emisor: "tú", texto: mensaje }]);
    setMensaje("");

    setTyping(true);

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/asistente_ia`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje }),
    });

    const data = await res.json();
    setTyping(false);

    setChat((prev: Mensaje[]) => [...prev, { emisor: "ia", texto: data.respuesta }]);
  };

  const borrarChat = () => {
    localStorage.removeItem("chatBell");
    setChat([{ emisor: "ia", texto: "Hola, ¿en qué te ayudo hoy?" }]);
  };

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTo({
        top: chatRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [chat, typing]);

  return (
    <div className="flex flex-col h-full space-y-6">

      {/* Título + borrar */}
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-bold tracking-tight text-orange-400">
          Asistente Bell
        </h1>

        <button
          onClick={borrarChat}
          className="text-sm px-4 py-2 rounded-lg bg-[#2a2a2a] text-gray-300 border border-[#3a3a3a] hover:bg-red-600 hover:text-white transition"
        >
          Borrar chat
        </button>
      </div>

      {/* Contenedor del chat */}
      <div
        ref={chatRef}
        className="flex-1 bg-[#1b1b1b] p-6 rounded-xl border border-[#2a2a2a] overflow-y-auto shadow-lg space-y-4"
      >
        {/* Pantalla de chat vacío */}
        {chat.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <p className="text-lg">Tu asistente Bell está listo</p>
            <p className="text-sm opacity-70">Escribe un mensaje para comenzar</p>
          </div>
        )}

        {/* Mensajes */}
        {chat.map((msg: Mensaje, i: number) => (
          <div
            key={i}
            className={`max-w-xl px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-lg transition-all duration-200 animate-[fadeIn_.25s_ease-out] whitespace-pre-wrap ${
              msg.emisor === "tú"
                ? "bg-gradient-to-br from-orange-600 to-orange-500 text-white self-end ml-auto"
                : "bg-[#2a2a2a] text-gray-200 self-start mr-auto"
            }`}
          >
            {msg.texto}
          </div>
        ))}

        {/* Animación typing */}
        {typing && (
          <div className="flex gap-1 items-center bg-[#2a2a2a] px-4 py-3 rounded-xl w-14 animate-[fadeIn_.25s_ease-out]">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-300"></span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          ref={inputRef}
          className="flex-1 p-4 rounded-xl bg-[#111] border border-[#2a2a2a] text-white focus:outline-none focus:ring-2 focus:ring-orange-500 transition"
          placeholder="Escribe un mensaje..."
          value={mensaje}
          onChange={(e) => setMensaje(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && enviar()}
        />

        <button
          onClick={enviar}
          className="bg-orange-600 px-8 rounded-xl font-semibold hover:bg-orange-500 transition shadow-md"
        >
          Enviar
        </button>
      </div>

    </div>
  );
}

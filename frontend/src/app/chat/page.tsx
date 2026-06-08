"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@/context/ChatContext";

export default function Chat() {
  const [mensaje, setMensaje] = useState("");
  const { chat, setChat, typing, setTyping } = useChat();
  const chatRef = useRef<HTMLDivElement>(null);

  const enviar = async () => {
    if (!mensaje.trim()) return;

    setChat((prev: { emisor: string; texto: string }[]) => [
      ...prev,
      { emisor: "tú", texto: mensaje },
    ]);
    setMensaje("");

    setTyping(true);

    const res = await fetch("http://192.168.1.7:8000/asistente_ia", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje }),
    });

    const data = await res.json();

    setTyping(false);

    setChat((prev: { emisor: string; texto: string }[]) => [
      ...prev,
      { emisor: "ia", texto: data.respuesta },
    ]);
  };

  const borrarChat = () => {
    localStorage.removeItem("chatBell");
    setChat([
      { emisor: "ia", texto: "Hola Kevin, ¿en qué te ayudo hoy?" }
    ]);
  };

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [chat, typing]);

  return (
    <div className="flex flex-col h-full space-y-6">

      {/* Título + botón borrar */}
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
        {chat.map((msg: { emisor: string; texto: string }, i: number) => (
          <div
            key={i}
            className={`max-w-xl px-4 py-3 rounded-xl text-sm leading-relaxed shadow-md transition ${
              msg.emisor === "tú"
                ? "bg-orange-600 text-white self-end ml-auto"
                : "bg-[#2a2a2a] text-gray-200 self-start mr-auto"
            }`}
          >
            {msg.texto}
          </div>
        ))}

        {/* Animación de escribiendo */}
        {typing && (
          <div className="max-w-xl px-4 py-3 rounded-xl text-sm leading-relaxed shadow-md bg-[#2a2a2a] text-gray-300 self-start mr-auto animate-pulse">
            ...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          className="flex-1 p-4 rounded-xl bg-[#111] border border-[#2a2a2a] text-white focus:outline-none focus:ring-2 focus:ring-orange-500 transition"
          placeholder="Escribe un mensaje..."
          value={mensaje}
          onChange={e => setMensaje(e.target.value)}
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

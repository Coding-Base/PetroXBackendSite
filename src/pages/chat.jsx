import React, { useState, useEffect, useRef, useCallback } from 'react';
import {  Button } from '../components/ui/button'

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);
  const username = localStorage.getItem('username') || 'Anonymous';

  const connectWS = useCallback(() => {
    if (ws.current) ws.current.close();

    // Use fallback URL if env variable is missing
    const wsUrl =
      import.meta.env.VITE_APP_WS_URL || `ws://${window.location.host}`;
    ws.current = new WebSocket(`${wsUrl}/ws/chat/`);

    ws.current.onopen = () => setIsConnected(true);
    ws.current.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setMessages((m) => [...m, data]);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      // Retry connection after delay
      setTimeout(connectWS, 3000);
    };
    ws.current.onclose = () => setIsConnected(false);
  }, []);

  useEffect(() => {
    connectWS();
    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [connectWS]);

  const sendMsg = (e) => {
    e.preventDefault();
    if (
      !message.trim() ||
      !ws.current ||
      ws.current.readyState !== WebSocket.OPEN
    )
      return;

    const payload = JSON.stringify({ username, text: message });
    ws.current.send(payload);
    setMessage('');
  };

  return (
    <div className="mx-auto max-w-2xl rounded-xl bg-gray-50 bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-bold text-blue-600">Group Chat</h2>
      <div className="mb-2 text-sm">
        {isConnected ? (
          <span className="text-green-500">🟢 Connected</span>
        ) : (
          <span className="text-red-500">🔴 Connecting...</span>
        )}
      </div>
      <div className="mb-4 h-64 space-y-2 overflow-y-auto rounded border border-gray-200 p-4">
        {messages.length === 0 ? (
          <div className="py-8 text-center text-gray-500">No messages yet</div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className="">
              <span className="font-semibold">{msg.username}:</span> {msg.text}
            </div>
          ))
        )}
      </div>
      <form onSubmit={sendMsg} className="flex space-x-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <Button
          type="submit"
          className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          disabled={!isConnected || !message.trim()}
        >
          Send
        </Button>
      </form>
    </div>
  );
}

import React from 'react';
import { format } from 'date-fns';
export default function SlackMessageCard({ message, isThreadReply }) {
  const initials = message.sender.split(' ').map(n => n[0]).join('').toUpperCase();
  return (<div className={`flex gap-3 ${isThreadReply ? 'ml-12 mt-2 py-1' : 'mt-4 py-2'}`}>
    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">{initials}</div>
    <div className="flex-1 min-w-0">
      <div className="flex items-baseline gap-2"><span className="font-bold text-sm text-gray-900">{message.sender}</span><span className="text-xs text-gray-500">{format(new Date(message.timestamp), 'HH:mm')}</span></div>
      <p className="text-sm text-gray-800 mt-1 break-words whitespace-pre-wrap">{message.body}</p>
      {message.reactions && message.reactions.length > 0 && <div className="flex gap-2 mt-2">{message.reactions.map((r, i) => <span key={i} className="text-lg">{r}</span>)}</div>}
    </div>
  </div>);
}

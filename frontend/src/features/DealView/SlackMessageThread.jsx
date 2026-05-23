import React, { useMemo } from 'react';
import SlackMessageCard from './SlackMessageCard';
export default function SlackMessageThread({ channel }) {
  const groupedMessages = useMemo(() => {
    const messages = channel?.messages || [];
    const groups = [];
    let current = [];
    messages.forEach(msg => {
      if (msg.is_thread_reply) current.push(msg);
      else { if (current.length > 0) groups.push({ main: null, replies: current }); current = []; groups.push({ main: msg, replies: [] }); }
    });
    if (current.length > 0) groups.push({ main: null, replies: current });
    return groups;
  }, [channel]);
  if (!channel) return <div className="flex-1 flex items-center justify-center text-gray-500">Select a channel</div>;
  return (<div className="flex-1 flex flex-col bg-white">
    <div className="border-b border-gray-200 px-6 py-4"><h2 className="text-lg font-bold">#{channel.name}</h2><p className="text-sm text-gray-600 mt-1">{channel.topic}</p></div>
    <div className="flex-1 overflow-y-auto px-6 py-4">{groupedMessages.length === 0 ? <div className="text-center text-gray-500 py-8">No messages</div> : groupedMessages.map((g, i) => <div key={i}>{g.main && <SlackMessageCard message={g.main} isThreadReply={false} />}{g.replies.map(r => <SlackMessageCard key={r.message_id} message={r} isThreadReply={true} />)}</div>)}</div>
  </div>);
}
